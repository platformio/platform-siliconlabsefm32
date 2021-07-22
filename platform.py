# Copyright 2014-present PlatformIO <contact@platformio.org>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import copy
import json
import os

from platformio.managers.platform import PlatformBase
from platformio.util import get_systype


class Siliconlabsefm32Platform(PlatformBase):

    def is_embedded(self):
        return True

    def configure_default_packages(self, variables, targets):
        board = variables.get("board")
        frameworks = variables.get("pioframework", [])
        if "mbed" in frameworks:
            deprecated_boards_file = os.path.join(
                self.get_dir(), "misc", "mbed_deprecated_boards.json")
            if os.path.isfile(deprecated_boards_file):
                with open(deprecated_boards_file) as fp:
                    if board in json.load(fp):
                        self.packages["framework-mbed"]["version"] = "~6.51506.0"
            self.packages["toolchain-gccarmnoneeabi"]["version"] = "~1.90201.0"

        if "zephyr" in frameworks:
            for p in self.packages:
                if p in ("tool-cmake", "tool-dtc", "tool-ninja"):
                    self.packages[p]["optional"] = False
            if "windows" not in get_systype():
                self.packages["tool-gperf"]["optional"] = False

        return PlatformBase.configure_default_packages(self, variables, targets)

    def get_boards(self, id_=None):
        result = PlatformBase.get_boards(self, id_)
        if not result:
            return result
        if id_:
            return self._add_default_debug_tools(result)
        else:
            for key, value in result.items():
                result[key] = self._add_default_debug_tools(result[key])
        return result

    def _add_default_debug_tools(self, board):
        debug = board.manifest.get("debug", {})
        upload_protocols = board.manifest.get("upload", {}).get(
            "protocols", [])
        if "tools" not in debug:
            debug["tools"] = {}

        # J-Link / BlackMagic Probe
        for link in ("blackmagic", "jlink"):
            if link not in upload_protocols or link in debug["tools"]:
                continue
            if link == "blackmagic":
                debug["tools"]["blackmagic"] = {
                    "hwids": [["0x1d50", "0x6018"]],
                    "require_debug_port": True
                }
            else:
                assert debug.get("jlink_device"), (
                    "Missed J-Link Device ID for %s" % board.id)
                debug["tools"][link] = {
                    "server": {
                        "package": "tool-jlink",
                        "arguments": [
                            "-singlerun",
                            "-if", "SWD",
                            "-select", "USB",
                            "-device", debug.get("jlink_device"),
                            "-port", "2331"
                        ],
                        "executable": ("JLinkGDBServerCL.exe"
                                       if "windows" in get_systype() else
                                       "JLinkGDBServer")
                    },
                    "onboard": link in debug.get("onboard_tools", [])
                }

        board.manifest["debug"] = debug
        return board

    def configure_debug_options(self, initial_debug_options, ide_data):
        debug_options = copy.deepcopy(initial_debug_options)
        adapter_speed = initial_debug_options.get("speed")
        if adapter_speed:
            server_options = debug_options.get("server") or {}
            server_executable = server_options.get("executable", "").lower()
            if "jlink" in server_executable:
                debug_options["server"]["arguments"].extend(
                    ["-speed", adapter_speed]
                )

        return debug_options
