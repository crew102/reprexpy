import pyperclip
import asttokens
import nbconvert

# a statement "chunk" includes all lines (including comments/whitelines) that come after the preceding statement but
# come before this statement
def _get_statement_chunks(code_str):
    tok = asttokens.ASTTokens(code_str, parse=True)

    ends = {statement.last_token.end[0] for statement in tok.tree.body}
    ends = list(ends)

    starts = [i + 1 for i in ends]
    # insert 1 as first value and remove last value
    starts.insert(0, 1)
    starts = starts[:-1]

    code_lines = code_str.split("\r\n") # will need to make this more generic
    return [code_lines[start - 1:end] for start, end in zip(starts, ends)]
