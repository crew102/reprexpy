import textwrap
import re
import os
import os.path

import pyperclip
import pytest

from reprexpy import reprexpy

skip_on_travis = pytest.mark.skipif(
    "TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
    reason="Skipping this test on Travis CI."
)


def _read_ex_fi(file):
    with open(file) as fi:
        lns = fi.read()
        return lns.rstrip('\n')


def _read_ex_fi_pair(pref):
    x = os.path.join("tests", "reprexes", pref)
    return [_read_ex_fi(x + i) for i in [".py", ".md"]]


def _ptxt(txt):
    dind = textwrap.dedent(txt)
    return dind.strip('\n')


def _all_match(out, regex_lst):
    lns = out.splitlines()
    return [any([re.search(rgx, line) for line in lns]) for rgx in regex_lst]


def _reprexpy_basic(*args, **kargs):
    return reprexpy(si=False, advertise=False, *args, **kargs)


def test_spliting_txt_output():
    ex = _read_ex_fi_pair("txt-outputs")
    out = _reprexpy_basic(ex[0])
    assert out == ex[1]


def test_two_statements_per_line():
    ex = _read_ex_fi_pair("two-statements-per-line")
    out = _reprexpy_basic(ex[0])
    assert out == ex[1]


def test_plot_outputs():
    ex = _read_ex_fi("tests/reprexes/plot-output.py")
    out = _reprexpy_basic(ex)
    assert len(re.findall("https://i.imgur.com", out)) == 3


def test_exception_handling():
    out = _reprexpy_basic("10 / 0")
    one_t = _all_match(out, ["ZeroDivisionError"])
    assert one_t[0], "ZeroDivisionError not found in output"


@skip_on_travis
def test_input_types():
    ex = _read_ex_fi("tests/reprexes/txt-outputs.py")
    out_x = _reprexpy_basic(ex)
    out_infile = _reprexpy_basic(infile="tests/reprexes/txt-outputs.py")
    pyperclip.copy(ex)
    out_clip = _reprexpy_basic()
    assert len(set([out_x, out_infile, out_clip])) == 1


@skip_on_travis
def test_output_to_clipboard():
    _reprexpy_basic('x = "hi there"; print(x)')
    assert pyperclip.paste() == '```python\nx = "hi there"; ' \
                                'print(x)\n#> hi there\n```'


def test_misc_params():
    code = """
    var = "some var"
    var
    """
    out = reprexpy(
        _ptxt(code), venue='so', comment='#<>', advertise=True
    )
    mlst = [
        '    var = "some var"', '#<>',
        'Created on.*by the \[reprexpy package\]'
    ]
    mout = _all_match(out, mlst)
    for i, j in zip(mout, mlst):
        assert i, '%r not found in output' % j


def test_si_imports():
    x = _read_ex_fi("tests/reprexes/imports.py")
    out = reprexpy(x=x)
    x_in = [
        'nbconvert', 'asttokens', 'pyimgur', 'stdlib-list', 'ipython', 'pyzmq'
    ]
    x_in = [i + "==" for i in x_in]

    mout = _all_match(out, x_in)
    for i, j in zip(mout, x_in):
        assert i, '%r not found in output' % j


def test_si_non_imports():

    x = _read_ex_fi("tests/reprexes/non-imports.py")
    out = reprexpy(x=x)
    not_in_x = ['pickledb', 'matplotlib', 'ipython']
    not_in_x = [i + "==" for i in not_in_x]

    mout = _all_match(out, not_in_x)
    for i, j in zip(mout, not_in_x):
        assert not i, '%r found in session info' % j
