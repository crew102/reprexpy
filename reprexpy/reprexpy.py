import asttokens
import nbconvert
import nbformat
import re
import warnings
import pyperclip
import pyimgur


# Helper functions for reprexpy() ---------------------------


# a statement "chunk" includes all lines (including comments/empty lines) that come after the preceding python statement
# and before the python statement in this chunk. each chunk will be placed in a notebook cell.
def _get_statement_chunks(code_str):
    tok = asttokens.ASTTokens(code_str, parse=True)

    ends = {statement.last_token.end[0] for statement in tok.tree.body}
    ends = list(sorted(ends))

    starts = [i + 1 for i in ends]
    # insert 1 as first value and remove last value
    starts.insert(0, 1)
    starts = starts[:-1]

    code_lines = code_str.splitlines()
    return [code_lines[start - 1:end] for start, end in zip(starts, ends)]


def _run_nb(code_chunks, kernel_name):
    code_chunks = [
      ["%matplotlib inline"],  # store plot outputs inline - only works inside notebooks
      ["import IPython.display; IPython.display.set_matplotlib_close(False)"],
      ["import matplotlib; import matplotlib.pyplot; matplotlib.pyplot.ioff()"]  # interactive backend
    ] + code_chunks
    nb = nbformat.v4.new_notebook()
    nb["cells"] = [nbformat.v4.new_code_cell("\n".join(i)) for i in code_chunks]
    ep = nbconvert.preprocessors.ExecutePreprocessor(timeout=600, kernel_name=kernel_name, allow_errors=True)
    node_out, _ = ep.preprocess(nb, {})
    return node_out


def _warn_if_prep_err(lst):
    if lst:
        if lst[0].output_type == "error":
            warnings.warn("Problem with using matplotlib when rendering your code")


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


def _get_code_block_start_stops(outputs):
    len_outputs = len(outputs)
    last_ind = len_outputs - 1

    # get list of indexes that define "code block" ends... a statement is considered the last statement in a code block
    # if returned plot output. note i[1] is the actual element here, i[0] is the element's index
    cb_stops = [i[0] for i in enumerate(outputs) if _any_plot_outputs(i[1])]
    cb_stops = list(sorted(set(cb_stops + [last_ind])))

    # first start index will always be first statement (i.e., index 0). then, to get the remaining start indexes, we
    # add 1 to the index of the stop indexes (assuming the stop index doesn't also coincide with last index in statement
    # list - i.e., last statement in code). note, we assume here that first statement in code doesn't result in plot
    # output, which seems safe.
    cb_starts = [0] + [i + 1 for i in cb_stops if i + 1 <= last_ind]

    assert len(cb_starts) == len(cb_stops), '\n\nlist of start indexes for code blocks is not' \
        ' the same length of as list of stop indexes. starts is {} while stops is {}'.format(cb_starts, cb_stops)

    return list(zip(cb_starts, cb_stops))


# we need to extract the text output for all output types except display_data. during this process we also process
# some of the text outputs where needed (e.g., strip ansi color codes from error traceback text) and add our output
# comment char to the beginning of each text output line.
def _get_one_txt_output(output_el, comment):
    if not output_el:
        pass
        return None
    elif output_el.output_type == 'execute_result':
        # results of type execute_result should always be strings, so have to convert to list (of strings)
        txt = [output_el["data"]["text/plain"]]
    elif output_el.output_type == 'stream':
        print_txt = output_el['text']
        # stream results will also be presented as strings, but we need to add the comment char after each newline of
        # printed text. note, this will strip the trailing newlines that usually come with calling `print`, which is
        # desired behavior in our case.
        txt = print_txt.splitlines()
    elif output_el.output_type == "error":
        # error traceback is given in a list, usually with one line of traceback per element. we need to remove ansi
        # color codes from traceback text and split any elements in list that are actually two lines, then concat lists.
        txt = [re.sub('\x1b\\[(.*?)([@-~])', '', i) for i in output_el["traceback"]]
        txt = [i.splitlines() for i in txt]
        txt = [x for i in txt for x in i]
    elif output_el.output_type == "display_data":
        return None
    else:
        assert False, "Ran into an unknown output_type"

    return [comment + ' ' + i for i in txt]


# for each element of the output list (i.e., for each output for a given cell), get all the text outputs of that cell
# and merge them into a single list (each line of output is given a single el in list)
def _get_cell_txt_outputs(outputs, comment):
    tmp_out = [[_get_one_txt_output(j, comment) for j in i] for i in outputs]

    # remove None values in lists
    tmp_out = [[j for j in i if j] for i in tmp_out]

    # merge multi-element lists (that are nested within temp_out) into single element lists
    return [[x for i in one for x in i] for one in tmp_out]


def _proc_one_display_data_node(node, client):
    data = node["data"]["image/png"].encode()
    req = client._send_request('https://api.imgur.com/3/image', method='POST', params={'image': data})
    return "![](" + req["link"] + ")"


def _get_plot_output_txt(one_out, client):
    anyp = _any_plot_outputs(one_out)

    if anyp:
        ptxt_out = [_proc_one_display_data_node(i, client) for i in one_out if _is_plot_output(i)]
        ptxt_out = '\n'.join(ptxt_out)
        return '\n' + ptxt_out
    else:
        return ""


# reprexpy() dev ---------------------------


def reprexpy(x=None, infile=None, venue='gh', kernel_name='python3', outfile=None, comment='#>'):

    # get code input string
    if x is not None:
        code_str = x
    elif infile is not None:
        with open(infile) as fi:
            code_str = fi.read()
    else:
        code_str = pyperclip.paste()

    statement_chunks = _get_statement_chunks(code_str)

    node_out = _run_nb(statement_chunks, kernel_name)
    outputs = _extract_outputs(node_out.cells)

    start_stops = _get_code_block_start_stops(outputs)

    # extract outputs that are text (i.e., outputs that are of type execute_result, stream, or error)
    txt_outputs = _get_cell_txt_outputs(outputs, comment)

    # add txt_outputs to statement_chunks
    txt_chunks = [i + j if j else i for i, j in zip(statement_chunks, txt_outputs)]

    if venue == 'so':
        txt_chunks = [['    ' + j for j in i] for i in txt_chunks]

    txt_chunks = ['\n'.join(i) for i in txt_chunks]

    code_blocks = [txt_chunks[i[0]:(i[1] + 1)] for i in start_stops]
    code_blocks = ['\n'.join(i) for i in code_blocks]

    if venue == 'gh':
        code_blocks = ["```python\n" + i + "\n```" for i in code_blocks]

    client = pyimgur.Imgur("9f3460e67f308f6")

    plot_txt_outputs = [_get_plot_output_txt(outputs[i[1]], client) for i in start_stops]

    all_chunks_fin = [i + j for i, j in zip(code_blocks, plot_txt_outputs)]
    out = '\n'.join(all_chunks_fin)

    if venue == 'so':
        out = '# <!-- language-all: lang-py -->\n' + out

    return out
