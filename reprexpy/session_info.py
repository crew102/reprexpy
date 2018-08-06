import re
import platform
import sys
import datetime

import IPython.core.getipython
import pkg_resources


class SessionInfo:

    def __init__(self):
        self.session_info = self._get_sesh_info_sectn()
        self.modules = self._get_module_sectn()

    def __repr__(self):
        return self._print()

    def __str__(self):
        return self._print()

    def _print(self):
        fl = (
            ["Session info ----------------------------------------------------------"] +
            [key + ": " + value for key, value in self.session_info.items()] +
            ["Modules ---------------------------------------------------------------"] +
            [key + ": " + value for key, value in self.modules.items()] +
            ["*Imported by reprexpy"]
        )
        return "\n".join(fl)

    def _get_sesh_info_sectn(self):
        pf = platform.platform() + " (64-bit)" if sys.maxsize > 2 ** 32 else " (32-bit)"

        major, minor, _ = platform.python_version_tuple()
        python_v = major + "." + minor

        now = datetime.datetime.now()
        date = now.strftime("%Y-%m-%d")

        return {
            "Platform": pf,
            "Python": python_v,
            "Date": date
        }

    def _get_imported_mods(self):
        ip_inst = IPython.core.getipython.get_ipython()
        un = ip_inst.user_ns
        return {re.split("\\.", value.__name__)[0]: value for key, value in un.items() if
                type(value).__name__ == "module"}

    def _get_version_info(self, modname, mod):
        try:
            dist_info = pkg_resources.get_distribution(modname)
            return dist_info.version
        except pkg_resources.DistributionNotFound:
            try:
                return mod.__version__
            except AttributeError:
                return "version unknown"

    def _get_module_sectn(self):
        imp_mods = self._get_imported_mods()
        imp_by_repx = ["IPython", "matplotlib", "reprexpy"]
        return {modname + "*" if modname in imp_by_repx else modname: self._get_version_info(modname, mod)
                for modname, mod in imp_mods.items() if modname != "builtins"}
