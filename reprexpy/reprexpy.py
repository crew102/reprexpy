import re
import warnings
import datetime

import asttokens
import nbconvert
import nbformat
import pyperclip
import pyimgur


# Helper functions for reprexpy() ---------------------------


# a "statement chunk" includes all lines (including comments/empty lines) that
# come after the preceding python statement and before the statement in this
# chunk. each chunk will be placed in a notebook cell.
def _get_statement_chunks(code_str, si):
    tok = asttokens.ASTTokens(code_str, parse=True)

    ends = {statement.last_token.end[0] for statement in tok.tree.body}
    ends = list(sorted(ends))

    starts = [i + 1 for i in ends]
    # insert 1 as first value and remove last value
    starts.insert(0, 1)
    starts = starts[:-1]

    code_lines = code_str.splitlines()
    schunks = [code_lines[start - 1:end] for start, end in zip(starts, ends)]
    if si:
        schunks = schunks + [
            ["import reprexpy", "print(reprexpy.SessionInfo())"]
        ]
    return schunks


def _run_nb(statement_chunks, kernel_name):
    statement_chunks = [
      # save env var so SessionInfo can filter out import statements as needed
      ["import os; os.environ['REPREX_RUNNING'] = 'true'"],
      ["import IPython.display; IPython.display.set_matplotlib_close(False)"],
      # interactive backend
      ["import matplotlib; import matplotlib.pyplot; matplotlib.pyplot.ioff()"]
    ] + statement_chunks
    nb = nbformat.v4.new_notebook()
    nb["cells"] = [
        nbformat.v4.new_code_cell("\n".join(i))
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


def _warn_if_prep_err(lst):
    if lst:
        if lst[0].output_type == "error":
            warnings.warn(
                "reprexpy encountered a problem when trying to import"
                " matplotlib"
            )


def _extract_outputs(cells):
    all_outputs = [[] if not i["outputs"] else i["outputs"] for i in cells]
    [_warn_if_prep_err(i) for i in all_outputs[0:3]]
    return all_outputs[3:]


# helper used in _get_code_block_start_stops
def _is_plot_output(el):
    # check if the node is for an image output
    if el.output_type == "display_data":
        if hasattr(el, "data"):
            if hasattr(el.data, "image/png"):
                return True
    return False


def _any_plot_outputs(lst):
    return any([_is_plot_output(i) for i in lst])


# get the line numbers where "code blocks" start and stop. a code block is a
# set of source code line(s)/text output(s) that need to be marked up using
# github/so's syntax highlighters
def _get_code_block_start_stops(outputs, si):
    len_outputs = len(outputs)
    last_ind = len_outputs - 1

    # get list of indexes that define code block ends... a statement is
    # considered the last statement in a block if that statement either
    # returned a plot output or is the statement right before the call the
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

    assert len(cb_starts) == len(cb_stops), \
        '\n\nlist of start indexes for code blocks is not' \
        ' the same length of as list of stop indexes. starts is {} while ' \
        'stops is {}'.format(cb_starts, cb_stops)

    return list(zip(cb_starts, cb_stops))


# we need to extract the text output for all output types except display_data.
# during this process we also process some of the text outputs where needed
# (e.g., strip ansi color codes from error traceback text) and add our output
# comment char to the beginning of each text output line.
def _get_one_txt_output(output_el, comment):
    if not output_el:
        pass
        return None
    elif output_el.output_type == 'execute_result':
        # results of type execute_result should always be strings, so have to
        # convert to list (of strings)
        txt = [output_el["data"]["text/plain"]]
    elif output_el.output_type == 'stream':
        print_txt = output_el['text']
        # stream results will also be presented as strings, but we need to add
        # the comment char after each newline of printed text. note, this will
        # strip the trailing newlines that usually come with calling `print`,
        # which is desired behavior in our case.
        txt = print_txt.splitlines()
    elif output_el.output_type == "error":
        # error traceback is given in a list, usually with one line of
        # traceback per element. we need to remove ansi color codes from
        # traceback text and split any elements in list that are actually two
        # lines, then finally concat lists.
        txt = [re.sub('\x1b\\[(.*?)([@-~])', '', i) for i in output_el["traceback"]]
        txt = [i.splitlines() for i in txt]
        txt = [x for i in txt for x in i]
    elif output_el.output_type == "display_data":
        return None
    else:
        assert False, "Ran into an unknown output_type"

    return [comment + ' ' + i for i in txt]


# for each element of the output list (i.e., for each output for a given cell),
# get all the text outputs of that cell and merge them into a single list
def _get_cell_txt_outputs(outputs, comment):
    tmp_out = [[_get_one_txt_output(j, comment) for j in i] for i in outputs]
    # remove None values in lists
    tmp_out = [[j for j in i if j] for i in tmp_out]
    # merge multi-element lists into single element lists
    return [[x for i in one for x in i] for one in tmp_out]


def _proc_one_display_data_node(node, client):
    data = node["data"]["image/png"].encode()
    req = client._send_request(
        'https://api.imgur.com/3/image', method='POST', params={'image': data}
    )
    return "![](" + req["link"] + ")"


def _get_plot_output_txt(one_out, client):
    if _any_plot_outputs(one_out):
        ptxt_out = [
            _proc_one_display_data_node(i, client)
            for i in one_out if _is_plot_output(i)
        ]
        ptxt_out = '\n\n'.join(ptxt_out)
        return '\n\n' + ptxt_out
    else:
        return ""


def _get_advertisement():
    now = datetime.datetime.now()
    date = now.strftime("%Y-%m-%d")
    return 'Created on ' + date + \
           ' by the [reprexpy package](https://github.com/crew102/reprexpy)'


# reprexpy() ---------------------------


def reprexpy(x=None, infile=None, venue='gh', kernel_name=None,
             comment='#>', si=True, advertise=True):

    # get source code string
    if x is not None:
        code_str = x
    elif infile is not None:
        with open(infile) as fi:
            code_str = fi.read()
    else:
        try:
            code_str = pyperclip.paste()
        # todo: modify pyperclip exeption here and re-raise it
        except:
            print(
                "Could not retrieve code from the clipboard. "
                "Try putting your code in a file and using "
                "the `infile` parameter instead of the clipboard."
            )

    statement_chunks = _get_statement_chunks(code_str, si=si)
    node_out = _run_nb(statement_chunks, kernel_name)
    outputs = _extract_outputs(node_out.cells)
    start_stops = _get_code_block_start_stops(outputs, si=si)
    txt_outputs = _get_cell_txt_outputs(outputs, comment)

    txt_chunks = [
        i + j if j else i
        for i, j in zip(statement_chunks, txt_outputs)
    ]
    if venue == 'so':
        txt_chunks = [['    ' + j for j in i] for i in txt_chunks]
    txt_chunks = ['\n'.join(i) for i in txt_chunks]

    code_blocks = [txt_chunks[i[0]:(i[1] + 1)] for i in start_stops]
    code_blocks = ['\n'.join(i) for i in code_blocks]
    if venue == 'gh':
        code_blocks = ["```python\n" + i + "\n```" for i in code_blocks]

    client = pyimgur.Imgur("14fb4fdc5c02a96")
    plot_txt_outputs = [
        _get_plot_output_txt(outputs[i[1]], client)
        for i in start_stops
    ]
    all_chunks_fin = [i + j for i, j in zip(code_blocks, plot_txt_outputs)]

    if venue == 'gh' and si:
        all_chunks_fin[-1] = '<details><summary>Session info</summary>\n\n' + \
                             all_chunks_fin[-1] + '\n\n</details>'
    if advertise:
        if si:
            all_chunks_fin[-1] = _get_advertisement() + '\n\n' + \
                                 all_chunks_fin[-1]
        else:
            all_chunks_fin[-1] = all_chunks_fin[-1] + '\n\n' + \
                                 _get_advertisement()

    out = '\n\n'.join(all_chunks_fin)
    if venue == 'so':
        out = '# <!-- language-all: lang-py -->\n\n' + out

    try:
        pyperclip.copy(out.encode('utf8'))
    except:
        warnings.warn("Could not copy rendered reprex to the clipboard.")

    return out
