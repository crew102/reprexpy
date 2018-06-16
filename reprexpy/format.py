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
