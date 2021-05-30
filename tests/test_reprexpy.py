import textwrap
import re
import os
import os.path

import pyperclip
import pytest

from reprexpy import reprex

skip_on_github = pytest.mark.skipif(
    'CI' in os.environ,
    reason='Skipping during Github workflow.'
)


def _read_ex_fi(file):
    with open(file) as fi:
        lns = fi.read()
        return lns.rstrip('\n')


def _read_ex_fi_pair(pref):
    x = os.path.join('tests', 'reprexes', pref)
    return [_read_ex_fi(x + i) for i in ['.py', '.md']]


def _ptxt(txt):
    dind = textwrap.dedent(txt)
    return dind.strip('\n')


def _all_match(out, regex_lst):
    lns = out.splitlines()
    return [any([re.search(rgx, line) for line in lns]) for rgx in regex_lst]


def _reprex_basic(*args, **kargs):
    return reprex(si=False, advertise=False, *args, **kargs)


def test_spliting_txt_output():
    ex = _read_ex_fi_pair('txt-outputs')
    out = _reprex_basic(ex[0])
    assert out == ex[1]


def test_two_statements_per_line():
    ex = _read_ex_fi_pair('two-statements-per-line')
    out = _reprex_basic(ex[0])
    assert out == ex[1]


def test_plot_outputs():
    ex = _read_ex_fi('tests/reprexes/plot-output.py')
    out = _reprex_basic(ex)
    assert len(re.findall('https://i\\.imgur\\.com', out)) == 3


def test_exception_handling():
    out = _reprex_basic('10 / 0')
    one_t = _all_match(out, ['ZeroDivisionError'])
    assert one_t[0], 'ZeroDivisionError not found in output'


@skip_on_github
def test_input_types():
    ex = _read_ex_fi('tests/reprexes/txt-outputs.py')
    out_x = _reprex_basic(ex)
    out_infile = _reprex_basic(code_file='tests/reprexes/txt-outputs.py')
    pyperclip.copy(ex)
    out_clip = _reprex_basic()
    assert len(set([out_x, out_infile, out_clip])) == 1


@skip_on_github
def test_output_to_clipboard():
    _reprex_basic('x = "hi there"; print(x)')
    assert pyperclip.paste() == '```python\nx = "hi there"; ' \
                                'print(x)\n#> hi there\n```'


def test_misc_params():
    code = """
    var = 'some var'
    var
    """
    out = reprex(_ptxt(code), venue='so', comment='#<>', advertise=True)
    mlst = [
        '    var = \'some var\'', '#<>',
        'Created on.*by the \\[reprexpy package\\]'
    ]
    mout = _all_match(out, mlst)
    for i, j in zip(mout, mlst):
        assert i, '%r not found in output' % j


def test_si_imports():
    x = _read_ex_fi('tests/reprexes/imports.py')
    out = reprex(code=x, si=True)
    x_in = [
        'nbconvert', 'asttokens', 'pyimgur', 'stdlib-list', 'ipython', 'pyzmq'
    ]
    x_in = [i + '==' for i in x_in]

    mout = _all_match(out, x_in)
    for i, j in zip(mout, x_in):
        assert i, '%r not found in output' % j


def test_si_non_imports():
    x = _read_ex_fi('tests/reprexes/non-imports.py')
    out = reprex(code=x, si=True)
    not_in_x = ['pickledb', 'matplotlib', 'ipython']
    not_in_x = [i + '==' for i in not_in_x]

    mout = _all_match(out, not_in_x)
    for i, j in zip(mout, not_in_x):
        assert not i, '%r found in session info' % j


def test_docstring_venue():
    ex = _read_ex_fi_pair('docstring-venue')
    out = reprex(ex[0], venue='sx')
    assert out == ex[1]