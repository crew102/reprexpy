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

