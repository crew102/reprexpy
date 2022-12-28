import platform
import sys
import datetime
import os
import re

import IPython.core.getipython
import asttokens
import stdlib_list
import pkg_resources


# goal: id distribution names + version numbers for all distributions that
# include at least one module that the user has explicitly imported in their
# script (including modules imported in the form `from module import object`).
# don't include modules that were either imported via a relative import or
# those that are part of the python standard lib.
#
# background: we can't rely on just the global symbol table to see what modules
# are loaded b/c we won't find the module name if the module is loaded in the
# form `from module import object`. also, we can't just use sys.modules as our
# list of loaded modules, b/c this list includes all loaded mods (including
# those not loaded explicitly by the user).
#
# approach taken:
# 1. get names of *most* imported modules (including packages) by parsing names
# from code. the one case where we won't get the full module name is when
# import happens in form `from module_a import module_b` (module_b won't be
# added to our list of mods...instead, we will be relying on the module_a's
# name to get us the name of the distribution that these mods belong to).
# 2. ensure that the modules id'd in step 1 are actually loaded by cross
# reffing mod names to sys.modules table. this will ensure that import
# statements that don't actually get executed in users's code don't get
# included...note, mods involved in import statements that don't actually
# get run could still show up in sys.modules if they are loaded by another mod
# that gets imported, so this won't be perfect.
# 3. try to find the name and version of the distribution that the mod is in.
class SessionInfo:
    """Class responsible for gathering IPython session information.

    A SessionInfo object provides basic information about a user's environment
    so that they may easily communicate their environment to others (e.g., when
    posting a question on Stack Overflow). For example, it provides
    info on what Python version you are using, as well as the version numbers
    of packages that you have imported into your IPython session. **You must be
    using the IPython kernel to instantiate this class.**

    Attributes
    ----------
    session_info : dict
        The Python version IPython is using, the OS it's running on, and
        today's date.
    pkg_info : dict
        The packages that the user has imported into their IPython environment,
        excluding those packages that are part of the Python standard library
        (e.g., ``re`` or ``os``). The names/keys of ``pkg_info`` refer to the
        modules that ``SessionInfo()`` has found in your environment (roughly
        speaking). The values in ``pkg_info`` are tuples that provide the
        name of the distribution that the module is packaged in (i.e., the name
        found on PyPI), as well as that distribution's version number. Printing
        a ``SessionInfo()`` object prints these distribution names/versions
        in the format that pip expects (e.g., in the requirements.txt format).

    Examples
    --------
    >>> import asttokens
    >>> import nbconvert.utils
    >>> import reprexpy
    >>> reprexpy.SessionInfo()
    Session info --------------------------------------------------------------------
    Python: 3.6
    Platform: Darwin-17.7.0-x86_64-i386-64bit (64-bit)
    Date: 2018-08-27
    Packages ------------------------------------------------------------------------
    asttokens==1.1.11
    nbconvert==5.3.1
    reprexpy==0.1.0

    """

    def __init__(self):
        self.session_info = self._get_sesh_info_sectn()
        self.pkg_info = self._get_pkg_info_sectn()

    def __repr__(self):
        return self._print()

    def __str__(self):
        return self._print()

    def _print(self):
        fl = (
            [self._as_heading('Session info')] +
            [key + ': ' + value for key, value in self.session_info.items()] +
            [self._as_heading('Packages')] +
            sorted(set(i[0] + '==' + i[1] for i in self.pkg_info.values()))
        )
        return '\n'.join(fl)

    @staticmethod
    def _as_heading(x):
        to_rep = 79 - len(x) + 1
        return x + ' ' + '-' * to_rep

    @staticmethod
    def _get_sesh_info_sectn():
        pf = platform.platform() + \
             ' (64-bit)' if sys.maxsize > 2 ** 32 else ' (32-bit)'

        major, minor, _ = platform.python_version_tuple()
        python_v = major + '.' + minor

        now = datetime.datetime.now()
        date = now.strftime('%Y-%m-%d')

        return {
            'Platform': pf,
            'Python': python_v,
            'Date': date
        }

    @staticmethod
    def _get_potential_mods():
        ip_inst = IPython.core.getipython.get_ipython()
        if not ip_inst:
            raise RuntimeError("SessionInfo() doesn't work outside of IPython")
        code = ip_inst.user_ns['In']
        # drop setup code if a reprex is running
        if os.environ.get('REPREX_RUNNING'):
            x = [
                i
                for i, j in enumerate(code) if re.search('REPREX_RUNNING', j)
            ]
            if x:
                code = code[(x[0] + 1):]
        scode = '\n'.join(code)
        tokes = asttokens.ASTTokens(scode, parse=True)

        def _get_one_mod(node):
            tnode = type(node).__name__
            if tnode == 'Import':
                return [i.name for i in node.names]
            if tnode == 'ImportFrom':
                return [node.module]

        mlist = [_get_one_mod(i) for i in asttokens.util.walk(tokes.tree)]
        return {j for i in mlist if i is not None for j in i}

    @staticmethod
    def _get_dist_info(dist):
        if dist.has_metadata('top_level.txt'):
            md = dist.get_metadata('top_level.txt')
            mods = md.splitlines()
        else:
            mods = []

        return {
            'project_name': dist.project_name,
            'version': dist.version,
            'mods': mods
        }

    def _get_version_info(self, modname, all_dist_info):
        try:
            dist_info = pkg_resources.get_distribution(modname)
            return dist_info.project_name, dist_info.version
        except pkg_resources.DistributionNotFound:
            ml = modname.split('.')
            if len(ml) > 1:
                modname = '.'.join(ml[:-1])
                return self._get_version_info(modname, all_dist_info)
            else:
                tmod = modname.split('.')[0]
                x = [
                    (i['project_name'], i['version'])
                    for i in all_dist_info if tmod in i['mods']
                ]
                if x:
                    return x[0]
                else:
                    return _, _

    def _get_stdlib_list(self):
        this_py = self.session_info['Python']
        if this_py not in stdlib_list.short_versions:
            tpf = float(this_py)
            x = [float(i) for i in stdlib_list.short_versions]
            # if we don't have a lib list for this version of python, use the
            # list that corresponds to the highest version that is below this
            # version (if there is one), or lowest version that is above this
            # version (if there is one)
            next_lowest = [i for i in x if i < tpf]
            if next_lowest:
                this_py = str(max(next_lowest))
            else:
                this_py = str(min([i for i in x if i > tpf]))
        return stdlib_list.stdlib_list(this_py)

    def _get_pkg_info_sectn(self):
        pmods = self._get_potential_mods()
        all_dist_info = [
            self._get_dist_info(i) for i in pkg_resources.working_set
        ]
        libs = self._get_stdlib_list()
        return {
            i: self._get_version_info(i, all_dist_info)
            for i in pmods if i in sys.modules and i not in libs
        }
