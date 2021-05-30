import re
import datetime
import os.path

import asttokens
import nbconvert
import nbformat
import pyperclip
import pyimgur
import pkg_resources


# Helper functions for reprex() ---------------------------


def _get_source_code(code, code_file):
    if code is not None:
        code_str = code
    elif code_file is not None:
        with open(code_file) as fi:
            code_str = fi.read()
    else:
        try:
            code_str = pyperclip.paste()
        except pyperclip.PyperclipException:
            raise Exception(
                'Could not retrieve code from the clipboard. '
                'Try putting your code in a file and using '
                'the `code_file` parameter instead of using the clipboard.'
            )
    return code_str


# an "input chunk" includes all lines (including comments/empty lines) that
# come after the preceding python statement and before the statement in
# this chunk. each chunk will be placed in a notebook cell.
def _get_input_chunks(code_str, si):
    tok = asttokens.ASTTokens(code_str, parse=True)

    ends = {statement.last_token.end[0] for statement in tok.tree.body}
    ends = list(sorted(ends))

    starts = [i + 1 for i in ends]
    starts.insert(0, 1)
    starts = starts[:-1]

    code_lines = code_str.splitlines()
    schunks = [code_lines[start - 1:end] for start, end in zip(starts, ends)]
    if si:
        schunks = schunks + [
            ['import reprexpy', 'print(reprexpy.SessionInfo())']
        ]
    return schunks


def _get_setup_code():
    magic_one = '%matplotlib inline'
    # set envvar so SessionInfo can filter out setup code as needed
    env = 'import os; os.environ["REPREX_RUNNING"] = "true"'
    # set up settings for displaying plot outputs
    p1 = 'import IPython.display; IPython.display.set_matplotlib_close(False)'
    p2 = 'import matplotlib.pyplot; matplotlib.pyplot.ioff();'
    python_statements = '; '.join([env, p1, p2])
    return [[magic_one]] + [[python_statements]]


def _run_nb(statement_chunks, kernel_name):
    scode = _get_setup_code()
    statement_chunks = scode + statement_chunks

    nb = nbformat.v4.new_notebook()
    nb['cells'] = [
        nbformat.v4.new_code_cell('\n'.join(i))
        for i in statement_chunks
    ]
    if kernel_name is None:
        ep = nbconvert.preprocessors.ExecutePreprocessor(
            timeout=600, allow_errors=True
        )
    else:
        ep = nbconvert.preprocessors.ExecutePreprocessor(
            timeout=600, allow_errors=True, kernel_name=kernel_name
        )
    node_out, _ = ep.preprocess(nb, {})
    return node_out


def _extract_outputs(cells):
    all_outputs = [[] if not i['outputs'] else i['outputs'] for i in cells]
    return all_outputs[len(_get_setup_code()):]


def _is_plot_output(el):
    # check if the node is for an image output
    if el.output_type == 'display_data':
        if hasattr(el, 'data'):
            if hasattr(el.data, 'image/png'):
                return True
    return False


def _any_plot_outputs(lst):
    return any([_is_plot_output(i) for i in lst])


# get the line numbers where 'code blocks' start and stop. a code block is a
# set of source code line(s)/text output(s) that should all be placed inside
# the same fenced-in code block.
def _get_code_block_start_stops(outputs, si):
    len_outputs = len(outputs)
    last_ind = len_outputs - 1

    # a statement is the last statement in a block if that statement either
    # returned a plot output or is the statement right before the call to
    # SessionInfo()
    cb_stops = [
        i[0]
        for i in enumerate(outputs)
        if _any_plot_outputs(i[1]) or (i[0] == last_ind - 1 and si)
    ]
    cb_stops = list(sorted(set(cb_stops + [last_ind])))

    # first start index will always be first statement (i.e., index 0). then,
    # to get the remaining start indexes, we add 1 to the index of the stop
    # indexes (assuming the stop index doesn't also coincide with last index in
    # statement list - i.e., last statement in code). note, we assume here that
    # the first statement doesn't result in plot output, which seems safe.
    cb_starts = [0] + [i + 1 for i in cb_stops if i + 1 <= last_ind]

    assert len(cb_starts) == len(cb_stops), (
        '\n\nlist of start indexes for code blocks is not' 
        ' the same length of as list of stop indexes. starts is {} while ' 
        'stops is {}'.format(cb_starts, cb_stops)
    )

    return list(zip(cb_starts, cb_stops))


# extract the text output for all output types except display_data. also
# process some of the text outputs where needed (e.g., strip ansi color codes
# from error traceback text) and add output comment char to the beginning of
# each text output line.
def _get_one_txt_output(output_el, comment, venue):
    if not output_el:
        return None
    elif output_el.output_type == 'execute_result':
        # results of type execute_result should always be strings, so have to
        # convert to list (of strings)
        txt = [output_el['data']['text/plain']]
    elif output_el.output_type == 'stream':
        print_txt = output_el['text']
        # stream results will also be presented as strings, but we need to add
        # the comment char after each newline of printed text. note, this will
        # strip the trailing newlines that usually come with calling `print`,
        # which is desired behavior.
        txt = print_txt.splitlines()
    elif output_el.output_type == 'error':
        # error traceback is given in a list, usually with one line of
        # traceback per element. remove ansi color codes from traceback text
        # and split any elements in list that are actually two lines.
        txt = [
            re.sub('\x1b\\[(.*?)([@-~])', '', i)
            for i in output_el['traceback']
        ]
        txt = [i.splitlines() for i in txt]
        txt = [x for i in txt for x in i]
        txt = [
            'Traceback (most recent call last):'
            if re.search('traceback .+most recent call last', i, re.IGNORECASE)
            else i
            for i in txt if re.search('[^-]', i)
        ]
    elif output_el.output_type == 'display_data':
        return None
    else:
        raise RuntimeError('Ran into an unknown output_type')

    if venue == 'sx':
        return txt
    else:
        return [comment + ' ' + i for i in txt]


# for each element of the output list (i.e., for each output for a given cell),
# get all the text outputs of that cell and merge them into a single list. all
# outputs are considered "text outputs" except those that correspond to plot
# output.
def _get_txt_outputs(outputs, comment, venue):
    tmp_out = [
        [_get_one_txt_output(j, comment, venue) for j in i]
        for i in outputs
    ]
    tmp_out = [[j for j in i if j] for i in tmp_out]
    return [[x for i in one for x in i] for one in tmp_out]


def _get_image_urls(node):
    data = node['data']['image/png'].encode()
    authentication = {'Authorization': 'Client-ID ' + '14fb4fdc5c02a96'}
    return pyimgur.request.send_request(
        'https://api.imgur.com/3/image',
        params={'image': data},
        method='POST',
        authentication=authentication
    )[0]['link']


def _get_markedup_urls(one_out, venue):
    if _any_plot_outputs(one_out):
        img_urls = [
            _get_image_urls(i)
            for i in one_out if _is_plot_output(i)
        ]
        ptxt_out = [
            '    .. image:: ' + i if venue == 'sx' else '![](' + i + ')'
            for i in img_urls
        ]
        ptxt_out = '\n\n'.join(ptxt_out)
        return '\n\n' + ptxt_out
    else:
        return ''


def _get_advertisement():
    now = datetime.datetime.now()
    date = now.strftime('%Y-%m-%d')
    return '<sup>Created on ' + date + \
           ' by the [reprexpy package](https://github.com/crew102/reprexpy)</sup>'


def reprex_ex(file):
    r"""Get the path to an example reprex file

    Parameters
    ----------
    file : {'basic-example.py', 'error.py', 'plotting.py'}
        Name of the file whose path you want.

    Returns
    -------
    str
        A path to an example reprex file.
    """
    return pkg_resources.resource_filename(
        'reprexpy', os.path.join('examples', file)
    )


# reprex() ---------------------------


def reprex(code=None, code_file=None, venue='gh', kernel_name=None,
           comment='#>', si=False, advertise=False):
    r"""Render a reproducible example of Python code (a reprex).

    Runs Python code inside a fresh IPython session, captures the results, and
    marks everything up using the appropriate markdown syntax (determined
    by ``venue``). The code for your reprex can come from one of three places:

    1. **The clipboard** (the default). Code for the reprex will be taken from
       the clipboard if you leave ``code=None`` and ``code_file=None``.
    2. **A string.** Use the ``code`` parameter to pass in a string of code.
    3. **A file.** Use the ``code_file`` parameter to specify a path to a file
       containing reprex code.

    Parameters
    ----------
    code : str, optional
        The code that makes up your reprex (e.g.,
        ``'x = "hi there"\nprint(x)'``).
    code_file : str, optional
        Path to a file that contains your reprex.
    venue : {'gh', 'so', 'sx'}, optional
        The venue that your reprex is bound for. Choose 'gh' if your reprex
        will be posted to GitHub, 'so' if it's bound for Stack Overflow, or
        'sx' if you will be inserting it into a docstring.
    kernel_name : str, optional
        The name of the IPython kernel that you want to use to execute your
        reprex. Choosing ``kernel_name=None`` (the default) means you want to
        use the default kernel. See the IPython docs `kernels for
        different environments
        <https://ipython.readthedocs.io/en/stable/install/kernel_install.html#kernels-for-different-environments>`_
        for details on how to create/use a custom kernel.
    comment : str, optional
        String that should be used to comment out your code's outputs. This
        parameter is ignored if ``venue='sx'``.
    si : bool, optional
        Do you want to display your IPython kernel's session info at the end of
        the reprex? See :py:class:`reprexpy.session_info.SessionInfo` for
        details on session info. This parameter is ignored if ``venue='sx'``.
    advertise : bool, optional
        Do you want to include a note at the bottom of your reprex that says
        that it was produced by the reprexpy package? This parameter is ignored
        if ``venue='sx'``.

    Returns
    -------
    str
        A string containing your rendered reprex. ``reprex()`` also tries to
        copy the rendered reprex to the clipboard.

    Examples
    --------

    Render a simple reprex for GitHub:

    >>> import reprexpy
    >>> code = 'x = "hi there"\ny = " old friend"\nprint(x + y)'
    >>> print(reprexpy.reprex(code))
    ```python
    x = "hi there"
    y = " old friend"
    print(x + y)
    #> hi there old friend
    ```

    Render same reprex, except pull the code from a file and use
    Stack Overflow markdown instead of GitHub markdown (hence the leading
    spaces in the rendered result):

    >>> import reprexpy
    >>> file_path = reprexpy.reprex_ex('basic-example.py')
    >>> print(reprexpy.reprex(code_file=file_path, venue='so'))
    # <!-- language-all: lang-py -->
        x = "hi there"
        y = " old friend"
        print(x + y)
        #> hi there old friend

    """

    code_str = _get_source_code(code, code_file)

    if venue == 'sx':
        si = False
        advertise = False

    print('Rendering reprex...')
    input_chunks = _get_input_chunks(code_str, si=si)
    node_out = _run_nb(input_chunks, kernel_name)
    outputs = _extract_outputs(node_out.cells)
    start_stops = _get_code_block_start_stops(outputs, si=si)
    txt_outputs = _get_txt_outputs(outputs, comment=comment, venue=venue)

    # add txt_outputs to source code (input_chunks) to create txt_chunks
    if venue == 'sx':
        input_chunks = [[j for j in i if j != ''] for i in input_chunks]
        input_chunks = [['>>> ' + j for j in i] for i in input_chunks]
    txt_chunks = [
        i + j if j else i
        for i, j in zip(input_chunks, txt_outputs)
    ]
    if venue in ['so', 'sx']:
        txt_chunks = [['    ' + j for j in i] for i in txt_chunks]
    txt_chunks = ['\n'.join(i) for i in txt_chunks]

    # group txt_chunks into code_blocks
    code_blocks = [txt_chunks[i[0]:(i[1] + 1)] for i in start_stops]
    code_blocks = ['\n'.join(i) for i in code_blocks]
    if venue == 'gh':
        code_blocks = ['```python\n' + i + '\n```' for i in code_blocks]

    # extract urls to plots and add mark them up
    markedup_urls = [
        _get_markedup_urls(outputs[i[1]], venue=venue)
        for i in start_stops
    ]
    final_blocks = [i + j for i, j in zip(code_blocks, markedup_urls)]

    # add misc markup items to the first/last block
    if venue == 'gh' and si:
        final_blocks[-1] = '<details><summary>Session info</summary>\n\n' + \
                           final_blocks[-1] + '\n\n</details>'
    if advertise:
        if si:
            final_blocks[-1] = _get_advertisement() + '\n\n' + final_blocks[-1]
        else:
            final_blocks[-1] = final_blocks[-1] + '\n\n' + _get_advertisement()
    if venue == 'so':
        final_blocks[0] = '# <!-- language-all: lang-py -->\n\n' + \
                          final_blocks[0]

    # convert list of code blocks to a string
    out = '\n\n'.join(final_blocks)
    if not isinstance(out, str):
        out = out.encode('utf8')

    try:
        pyperclip.copy(out)
    except RuntimeError:
        print('Could not copy rendered reprex to the clipboard.\n')
    else:
        print('Rendered reprex is on the clipboard.\n')

    return out
