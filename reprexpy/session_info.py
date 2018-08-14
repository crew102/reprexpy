import platform
import sys
import datetime
import os
import re

import IPython.core.getipython
import asttokens
import stdlib_list
import pkg_resources


class SessionInfo:

    def __init__(self):
        self.session_info = self._get_sesh_info_sectn()
        self.pkg_info = self._get_pkg_info_sectn()

    def __repr__(self):
        return self._print()

    def __str__(self):
        return self._print()

    def _print(self):
        fl = (
            [self._as_heading("Session info")] +
            [key + ": " + value for key, value in self.session_info.items()] +
            [self._as_heading("Packages")] +
            sorted(set(i[0] + "==" + i[1] for i in self.pkg_info.values()))
        )
        return "\n".join(fl)

    def _as_heading(self, x):
        to_rep = 79 - len(x) + 1
        return x + " " + "-" * to_rep

    # method used to initialize session_info field ---------------------------

    def _get_sesh_info_sectn(self):
        pf = platform.platform() + \
             " (64-bit)" if sys.maxsize > 2 ** 32 else " (32-bit)"

        major, minor, _ = platform.python_version_tuple()
        python_v = major + "." + minor

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")

        return {
            "Platform": pf,
            "Python": python_v,
            "Date": date
        }

    # methods used to initialize pkg_info field ---------------------------

    def _get_potential_mods(self):
        ip_inst = IPython.core.getipython.get_ipython()
        assert ip_inst, "SessionInfo() doesn't work outside of IPython"
        code = ip_inst.user_ns["In"]
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
            if tnode == "Import":
                return [i.name for i in node.names]
            elif tnode == "ImportFrom":
                return [node.module]

        mlist = [_get_one_mod(i) for i in asttokens.util.walk(tokes.tree)]
        return {j for i in mlist if i is not None for j in i}

    def _get_dist_info(self, dist):
        try:
            md = dist.get_metadata("top_level.txt")
            mods = md.splitlines()
        except:
            mods = []
        return {
            "project_name": dist.project_name,
            "version": dist.version,
            "mods": mods
        }

    def _get_version_info(self, modname, all_dist_info):
        try:
            dist_info = pkg_resources.get_distribution(modname)
            return dist_info.project_name, dist_info.version
        except pkg_resources.DistributionNotFound:
            ml = modname.split(".")
            if len(ml) > 1:
                modname = '.'.join(ml[:-1])
                return self._get_version_info(modname, all_dist_info)
            else:
                tmod = modname.split(".")[0]
                x = [
                    (i['project_name'], i['version'])
                    for i in all_dist_info if tmod in i['mods']
                ]
                if x:
                    return x[0]
                else:
                    return _, _

    def _get_stdlib_list(self):
        this_py = self.session_info["Python"]
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
