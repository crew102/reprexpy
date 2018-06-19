import asttokens
import nbconvert
import nbformat

# a statement "chunk" includes all lines (including comments/empty line) that come after the preceding statement and
# before the statement in this chunk. each chunk will be placed in a notebook cell.
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


def _extract_outputs(cells):
    outputs = [None if not i["outputs"] else i["outputs"] for i in cells]
    return outputs[3:]


# helper used in _get_code_block_start_stops
def _is_plot_output(el):
    # output of cell can be an empty list
    if not el:
        return False
    # if isn't an empty list, it's a list of length 1 containing a notebooknode
    el = el[0]
    # check if the node is for an image output
    if el.output_type == "display_data":
        if hasattr(el, "data"):
            if hasattr(el.data, "image/png"):
                return True
    return False


def _get_code_block_start_stops(outputs):
    len_outputs = len(outputs)
    last_ind = len_outputs - 1

    # get list of indexes that define "code block" ends... a statement is considered the last statement in a code block
    # if returned plot output
    cb_stops = [i[0] for i in enumerate(outputs) if _is_plot_output(i[1])]
    cb_stops = list(sorted(set(cb_stops + [last_ind])))

    # first start index will always be first statement (i.e., index 0). then, to get the remaining start indexes, we
    # add 1 to the index of the stop indexes (assuming the stop index doesn't also coincide with last index in statement
    # list - i.e., last statement in code). note, we assume here that first statement in code doesn't result in plot
    # output, which seems safe.
    cb_starts = [0] + [i + 1 for i in cb_stops if i + 1 <= last_ind]

    assert len(cb_starts) == len(cb_stops), '\n\nlist of start indexes for code blocks is not' \
        ' the same length of as list of stop indexes. starts is {} while stops is {}'.format(cb_starts, cb_stops)

    return list(zip(cb_starts, cb_stops))
