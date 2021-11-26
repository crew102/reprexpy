import os
import re
import textwrap

import pyperclip
import pytest

from reprexpy import reprex

skip_on_github = pytest.mark.skipif(
    'CI' in os.environ,
    reason='Skipping during Github workflow.'
)


def _read_reprex_file(file):
    with open(file) as fi:
        lns = fi.read()
        return lns.rstrip('\n')


def _read_reprex_file_pair(pref):
    x = os.path.join('tests', 'reprexes', pref)
    return [_read_reprex_file(x + i) for i in ['.py', '.md']]


def _assert_reprex_exact_match(file_name, *args, **kargs):
    src, expected_output = _read_reprex_file_pair(file_name)
    out = reprex(src, *args, **kargs)
    assert out == expected_output


def _count_mismatching_lines(file_name, *args, **kargs):
    src, expected_output = _read_reprex_file_pair(file_name)
    out = reprex(src, *args, **kargs)
    out_lines = out.splitlines()
    expected_lines = expected_output.splitlines()
    return sum(
        [i != j for i, j in zip(out_lines, expected_lines)]
    )


def test_spliting_txt_output():
    _assert_reprex_exact_match('txt-outputs')


# Good test to use during interactive debugging
def test_debug_example():
    _assert_reprex_exact_match('debug-example')


def test_two_statements_per_line():
    _assert_reprex_exact_match('two-statements-per-line')


def test_docstring_venue():
    _assert_reprex_exact_match('docstring-venue', venue='sx')


def test_plot_outputs():
    assert _count_mismatching_lines('plot-output') == 3


def test_stack_overflow_venue():
    assert _count_mismatching_lines('so-venue', venue='so') == 1


def test_plot_and_txt_outputs():
    assert _count_mismatching_lines('plot-and-txt-output') == 2


def test_unicode():
    _assert_reprex_exact_match('unicode')


def test_exception_handling():
    out = reprex('10 / 0')
    assert re.search('ZeroDivisionError', out)


@skip_on_github
def test_input_types():
    code = _read_reprex_file('tests/reprexes/txt-outputs.py')
    out_str = reprex(code=code)

    out_infile = reprex(code_file='tests/reprexes/txt-outputs.py')

    pyperclip.copy(code)
    out_clipboard = reprex()

    assert out_str == out_infile == out_clipboard


@skip_on_github
def test_output_to_clipboard():
    code = 'print("hi there")'
    expected_output = '```python\nprint("hi there")\n#> hi there\n```'
    reprex(code)
    assert pyperclip.paste() == expected_output


def test_misc_params():
    raw_code = """
    var = 'some var'
    var
    """
    code = textwrap.dedent(raw_code).strip('\n')
    out = reprex(code, venue='so', comment='#<>', advertise=True)
    regex = (
        '    var = \'some var\''
        '.*#<>'
        '.*Created on.*by the \\[reprexpy package\\]'
    )
    assert re.search(regex, out, flags=re.DOTALL)


def test_si_imports():
    code = _read_reprex_file('tests/reprexes/imports.py')
    out = reprex(code, si=True)
    imports = [
        'nbconvert', 'asttokens', 'pyimgur', 'stdlib-list', 'ipython', 'pyzmq'
    ]
    for distribution in imports:
        distribution_regex = distribution + '=='
        assert re.search(distribution_regex, out)


def test_si_non_imports():
    code = _read_reprex_file('tests/reprexes/non-imports.py')
    out = reprex(code, si=True)
    non_imports = ['pickledb', 'matplotlib', 'ipython']
    for distribution in non_imports:
        distribution_regex = distribution + '=='
        assert not re.search(distribution_regex, out)
