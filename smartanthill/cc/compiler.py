# Copyright (c) 2015, OLogN Technologies AG. All rights reserved.
#
# Redistribution and use of this file in source and compiled
# forms, with or without modification, are permitted
# provided that the following conditions are met:
#     * Redistributions in source form must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in compiled form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the OLogN Technologies AG nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL OLogN Technologies AG BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE

from base64 import b64encode
from os import environ
from os.path import getsize, isdir, isfile, join

from platformio.util import get_pioenvs_dir
from twisted.internet import utils
from twisted.internet.defer import Deferred
from twisted.python import log
from twisted.python.util import sibpath

from smartanthill import FIRMWARE_VERSION


class PlatformIOBuilder(object):

    def __init__(self, pioenvs_dir, env_name):
        self.pioenvs_dir = pioenvs_dir
        self.env_name = env_name

        self._defer = Deferred()
        self._defines = []

        self.append_define("VERSION_MAJOR", FIRMWARE_VERSION[0])
        self.append_define("VERSION_MINOR", FIRMWARE_VERSION[1])

    def get_env_dir(self):
        return join(get_pioenvs_dir(), self.env_name)

    def get_firmware_path(self):
        if not isdir(self.get_env_dir()):
            return None
        for ext in ["bin", "hex"]:
            firm_path = join(self.get_env_dir(), "firmware." + ext)
            if isfile(firm_path):
                return firm_path
        return None

    def append_define(self, name, value=None):
        self._defines.append((name, value))

    def run(self):
        newenvs = dict(
            PLATFORMIO_SETTING_ENABLE_PROMPTS="false",
            PLATFORMIO_ENVS_DIR=self.pioenvs_dir,
            PLATFORMIO_SRCBUILD_FLAGS=self._get_srcbuild_flags()
        )

        d = utils.getProcessOutputAndValue(
            "platformio", args=("run", "-e", self.env_name),
            env=environ.update(newenvs),
            path=sibpath(__file__, join("embedded", "firmware"))
        )
        d.addBoth(self._on_run_callback)
        return self._defer

    def _get_srcbuild_flags(self):
        flags = []
        for d in self._defines:
            if d[1] is not None:
                flags.append("-D%s=%s" % (d[0], d[1]))
            else:
                flags.append("-D%s" % d[0])
        return " ".join(flags)

    def _on_run_callback(self, result):
        log.msg(result)

        fw_path = self.get_firmware_path()
        # result[2] is return code
        if result[2] != 0 or not fw_path or not isfile(fw_path):
            return self._defer.errback(Exception(result))

        data = dict(
            version=".".join([str(s) for s in FIRMWARE_VERSION]),
            size=getsize(fw_path),
            type=fw_path[-3:],
            firmware=b64encode(open(fw_path).read())
        )
        self._defer.callback(data)
