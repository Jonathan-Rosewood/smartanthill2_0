# Copyright (C) 2015 OLogN Technologies AG
#
# This source file is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License version 2
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import os
import subprocess
import sys
from platform import system
from tempfile import NamedTemporaryFile


CURINTERPRETER_PATH = os.path.normpath(sys.executable)
IS_WINDOWS = system().lower() == "windows"


def fix_winpython_pathenv():
    """
    Add Python & Python Scripts to the search path on Windows
    """
    import ctypes
    from ctypes.wintypes import HWND, UINT, WPARAM, LPARAM, LPVOID
    try:
        import _winreg as winreg
    except ImportError:
        import winreg

    # took these lines from the native "win_add2path.py"
    pythonpath = os.path.dirname(CURINTERPRETER_PATH)
    scripts = os.path.join(pythonpath, "Scripts")
    if not os.path.isdir(scripts):
        os.makedirs(scripts)

    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, u"Environment") as key:
        try:
            envpath = winreg.QueryValueEx(key, u"PATH")[0]
        except WindowsError:
            envpath = u"%PATH%"

        paths = [envpath]
        for path in (pythonpath, scripts):
            if path and path not in envpath and os.path.isdir(path):
                paths.append(path)

        envpath = os.pathsep.join(paths)
        winreg.SetValueEx(key, u"PATH", 0, winreg.REG_EXPAND_SZ, envpath)
    winreg.ExpandEnvironmentStrings(envpath)

    # notify the system about the changes
    SendMessage = ctypes.windll.user32.SendMessageW
    SendMessage.argtypes = HWND, UINT, WPARAM, LPVOID
    SendMessage.restype = LPARAM
    SendMessage(0xFFFF, 0x1A, 0, u"Environment")
    return True


def exec_command(*args, **kwargs):
    kwargs['stdout'] = subprocess.PIPE
    kwargs['stderr'] = subprocess.PIPE
    kwargs['shell'] = IS_WINDOWS

    p = subprocess.Popen(*args, **kwargs)
    out, err = p.communicate()

    if p.returncode != 0:
        raise Exception("\n".join([out, err]))
    return out


def exec_python_cmd(args):
    return exec_command([CURINTERPRETER_PATH] + args).strip()


def install_pip():
    try:
        from urllib2 import urlopen
    except ImportError:
        from urllib.request import urlopen

    f = NamedTemporaryFile(delete=False)
    response = urlopen("https://bootstrap.pypa.io/get-pip.py")
    f.write(response.read())
    f.close()

    try:
        print (exec_python_cmd([f.name]))
    finally:
        os.unlink(f.name)


def install_pypi_packages(packages):
    for pipargs in packages:
        print (exec_python_cmd([
            "-m", "pip.__main__" if sys.version_info < (2, 7, 0) else "pip",
            "install", "-U"] + pipargs))


def main():
    steps = [
        ("Fixing Windows %PATH% Environment", fix_winpython_pathenv, []),
        ("Installing Python Package Manager", install_pip, []),
        ("Installing SmartAnthill and dependencies", install_pypi_packages, [[
            ["setuptools"],
            ["http://cc.smartanthill.org/package/smartanthill.latest.tar.gz"],
            ["https://github.com/platformio/platformio/archive/develop.zip"],
            ["https://github.com/smartanthill/smartanthill-zepto-compiler/"
             "archive/develop.zip"],
            ["--egg", "http://dl.platformio.org/scons.zip"]
        ]])
    ]

    if not IS_WINDOWS:
        del steps[0]

    is_error = False
    for s in steps:
        if is_error:
            break
        print ("\n==> %s ..." % s[0])
        try:
            s[1](*s[2])
            print ("[SUCCESS]")
        except Exception, e:
            is_error = True
            print (str(e))
            print ("[FAILURE]")
            if "Permission denied" in str(e) and not IS_WINDOWS:
                print ("""
-----------------
Permission denied
-----------------

You need the `sudo` permission to install Python packages. Try

$ sudo python get-smartanthill.py
""")

    if is_error:
        print ("The installation process has been FAILED!\n"
               "Please report about this problem here\n"
               "< https://github.com/smartanthill/smartanthill2_0/issues >")
        return
    else:
        print ("\n ==> Installation process has been "
               "successfully FINISHED! <==\n")

    print ("""

----------------------------------------
Please RESTART your Terminal Application
----------------------------------------

Then run `smartanthill` command.

""")


if __name__ == "__main__":
    sys.exit(main())
