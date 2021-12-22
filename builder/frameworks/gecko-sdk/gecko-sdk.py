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

"""
Gecko SDK

The Gecko SDK is software development kit developed by Silicon Labs for the EFM32, EFR32
and EZR32. It contains the basic software needed for development, covering everything
from the low-level hardware abstraction layer (HAL) and peripheral drivers to
communication stacks and example code.

https://docs.silabs.com/gecko-platform/
"""

import hashlib
import json
import os
import subprocess
import sys

import click
from SCons.Script import ARGUMENTS, COMMAND_LINE_TARGETS, DefaultEnvironment

from platformio.compat import hashlib_encode_data

env = DefaultEnvironment()
platform = env.PioPlatform()
board_config = env.BoardConfig()

SDK_DIR = platform.get_package_dir("framework-gecko-sdk")
assert SDK_DIR and os.path.isdir(SDK_DIR)

PROJECT_SRC_DIR = env.subst("$PROJECT_SRC_DIR")
BUILD_DIR = env.subst("$BUILD_DIR")
PROJECT_DIR = env.subst("$PROJECT_DIR")
PROJECT_NAME = os.path.basename(PROJECT_DIR)
SDK_EXPORT_DIR = os.path.join(BUILD_DIR, "gsdk-export")
EXPORTED_SDK_CONFIG_FILE = os.path.join(SDK_EXPORT_DIR, f"{PROJECT_NAME}.project.mak")


def run_tool(cmd, custom_env=None):
    kwargs = {}
    verbose = int(ARGUMENTS.get("PIOVERBOSE", 0))
    if not verbose:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE

    result = subprocess.run(
        cmd,
        env=custom_env,
        **kwargs,
    )
    if result.returncode != 0:
        if not verbose:
            print(
                " ".join([result.stdout.decode(), result.stderr.decode()]).strip(),
                file=sys.stderr,
            )
        print("Error: Failed to run external tool.", file=sys.stderr)
        env.Exit(1)


def get_project_slcp_file():
    if board_config.get("build.gecko-sdk.project_file", ""):
        return board_config.get("build.gecko-sdk.project_file")

    project_dir = PROJECT_DIR
    candidates = [item for item in os.listdir(project_dir) if item.endswith(".slcp")]
    if not candidates:
        return ""

    if len(candidates) > 1:
        print(
            "Warning! Detected multiple SCLP configuration files! "
            "%s will be used." % candidates[0]
        )
        print(
            "You can specify a custom SLCP file using the "
            "`board_build.gecko-sdk.project_file = /path/yourfile.slcp` option "
            "in your platformio.ini."
        )

    return candidates[0]


def reload_sdk_configuration(board_config, slcp_config_path):
    make_sdk_trusted()

    if not os.path.isdir(BUILD_DIR):
        os.makedirs(BUILD_DIR)

    args = (
        "generate",
        "--sdk",
        SDK_DIR,
        "--project-file",
        slcp_config_path,
        "--export-destination",
        SDK_EXPORT_DIR,
        "--export-templates",
        os.path.join(
            platform.get_dir(),
            "builder",
            "frameworks",
            "gecko-sdk",
            "exporter_templates",
        ),
        "--project-name",
        PROJECT_NAME,
        "--with",
        board_config.get("build.mcu", "").upper(),
        "--require-clean-project",
        "--no-copy",
        "--output-type=makefile",
    )

    run_slc_cli(args)


def run_slc_cli(args):
    # The SLC tool is run in an isolated environment with a portable JDK package
    sdk_env = os.environ.copy()
    sdk_env["PATH"] = os.pathsep.join(
        [
            os.path.join(platform.get_package_dir("corretto-jdk-portable"), "bin"),
            sdk_env["PATH"],
        ]
    )

    cmd = (
        env.subst("$PYTHONEXE"),
        "%s"
        % os.path.join(
            platform.get_package_dir("tool-silabs-slc-cli"),
            "slc",
        ),
    ) + args

    run_tool(cmd, sdk_env)


def is_project_empty(slcp_config_path):
    if not os.path.isfile(slcp_config_path):
        return True
    return False


def is_sdk_reload_required(slcp_config_path):
    for d in (
        os.path.join(SDK_EXPORT_DIR, "autogen"),
        os.path.join(SDK_EXPORT_DIR, "config"),
    ):
        if not os.path.isdir(d) or not os.listdir(d):
            return True
    if not os.path.isfile(EXPORTED_SDK_CONFIG_FILE):
        return True
    if not os.path.isfile(slcp_config_path) or os.path.getmtime(
        slcp_config_path
    ) > os.path.getmtime(EXPORTED_SDK_CONFIG_FILE):
        return True

    for dep_dir in (
        SDK_DIR,
        platform.get_package_dir("tool-silabs-slc-cli"),
        platform.get_package_dir("toolchain-gccarmnoneeabi"),
    ):
        if os.path.getmtime(dep_dir) > os.path.getmtime(EXPORTED_SDK_CONFIG_FILE):
            return True

    return False


def make_sdk_trusted():
    trusted_file = os.path.join(SDK_DIR, "primary_trusted.trust")
    if os.path.isfile(trusted_file):
        return

    args = (
        "signature",
        "trust",
        "--sdk",
        SDK_DIR,
    )

    run_slc_cli(args)

    with open(trusted_file, "w") as fp:
        fp.write(SDK_DIR)


def load_project_config():
    assert os.path.isfile(
        EXPORTED_SDK_CONFIG_FILE
    ), "Couldn't load exported SDK configuration"
    with open(EXPORTED_SDK_CONFIG_FILE) as fp:
        try:
            return json.load(fp)
        except json.JSONDecodeError as e:
            print("Failed to read project configuration!", file=sys.stderr)
            print(str(e), file=sys.stderr)
            env.Exit(1)


def extract_project_macros(raw_macros):
    if not raw_macros:
        return []

    result = []
    for macro in raw_macros:
        macro = macro.replace("-D", "")
        if "=" in macro:
            name, value = macro.split("=", 1)
            if value.startswith("<"):
                value = '"%s"' % value
            result.append((name, value))
        else:
            result.append(macro)
    return result


def process_build_flags(project_config):
    build_flags = project_config.get("flags", {})
    expected_scopes = ("ASFLAGS", "CFLAGS", "CXXFLAGS", "LINKFLAGS")
    assert all(scope in build_flags for scope in expected_scopes)
    for scope in expected_scopes:
        for flag in build_flags[scope]:
            # Linker script is processed separately
            if scope == "LINKFLAGS" and flag.startswith("-T"):
                continue
            args = click.parser.split_arg_string(flag)
            env[scope].extend(
                ['"%s"' % arg if "$BUILD_DIR" in arg else arg for arg in args]
            )

    env.Append(
        CPPDEFINES=extract_project_macros(
            project_config.get("defines", {}).get("CPPDEFINES", [])
        )
    )


def process_project_includes(project_config):
    env.Append(
        CPPPATH=[
            include if os.path.isabs(include) else os.path.join(SDK_EXPORT_DIR, include)
            for include in project_config.get("includes", {}).get("CPPPATH", [])
        ]
    )


def process_project_libraries(project_config):
    project_libs = project_config.get("libraries", {})

    env.Append(
        LIBS=[lib.replace("-l", "", 1) for lib in project_libs.get("system", [])]
    )

    # Extra precompiled libraries shipped with the SDK
    env.Append(
        _LIBFLAGS=" %s"
        % (" ".join('"%s"' % lib for lib in project_libs.get("user", []))),
    )


def _extract_source_files(project_config):
    return [
        source_path
        if os.path.isabs(source_path)
        else os.path.realpath(os.path.join(SDK_EXPORT_DIR, source_path))
        for source_path in project_config.get("sources", [])
    ]


def extract_linker_script(project_config):
    linkflags = project_config.get("flags", {}).get("LINKFLAGS", [])
    ldscript = None
    for flag in linkflags:
        if flag.startswith("-T"):
            ldscript = flag.replace('"', "").replace("-T", "")

    if not os.path.isabs(ldscript):
        ldscript = os.path.join(SDK_EXPORT_DIR, ldscript)
    return ldscript


def build_source_files(project_config):
    src_dirs = {}
    for file in _extract_source_files(project_config):
        pdir = os.path.dirname(file)
        if pdir not in src_dirs:
            src_dirs[pdir] = []
        src_dirs[pdir].append(file)

    for pdir, files in src_dirs.items():
        # Project sources are compiled by PlatformIO separately
        if pdir.startswith(PROJECT_SRC_DIR):
            continue
        env.BuildSources(
            os.path.join(
                BUILD_DIR,
                "gsdk-build",
                os.path.basename(pdir)
                + hashlib.sha1(hashlib_encode_data(pdir)).hexdigest()[:5],
            ),
            pdir,
            src_filter=["-<*>"] + ["+<%s>" % os.path.basename(f) for f in files],
        )


def generate_default_project(board_config):
    slcp_tpl = f"""project_name: {PROJECT_NAME}
package: platform
quality: development
sdk: {{id: gecko_sdk, version: {platform.get_package_version('framework-gecko-sdk')}}}
description: >
  An autogenerated configuration that can be used as a starting point.
category: Example|Platform
component:
  - id: sl_system
  - id: device_init
  - id: {board_config.get('build.mcu', '').upper()}

"""

    main_tpl = """#include "sl_component_catalog.h"
#include "sl_system_init.h"
#if defined(SL_CATALOG_POWER_MANAGER_PRESENT)
#include "sl_power_manager.h"
#endif
#if defined(SL_CATALOG_KERNEL_PRESENT)
#include "sl_system_kernel.h"
#else // SL_CATALOG_KERNEL_PRESENT
#include "sl_system_process_action.h"
#endif // SL_CATALOG_KERNEL_PRESENT
int main(void)
{
  // Initialize Silicon Labs device, system, service(s) and protocol stack(s).
  // Note that if the kernel is present, processing task(s) will be created by
  // this call.
  sl_system_init();

  // Initialize the application (needs implementation)
  // app_init();

#if defined(SL_CATALOG_KERNEL_PRESENT)
  // Start the kernel. Task(s) created in app_init() will start running.
  sl_system_kernel_start();
#else // SL_CATALOG_KERNEL_PRESENT
  while (1) {
    // Do not remove this call: Silicon Labs components process action routine
    // must be called from the super loop.
    sl_system_process_action();

    // Application process (needs implementation)
    // app_process_action();

#if defined(SL_CATALOG_POWER_MANAGER_PRESENT)
    // Let the CPU go to sleep if the system allows it.
    sl_power_manager_sleep();
#endif
  }
#endif // SL_CATALOG_KERNEL_PRESENT
}
"""

    with open(os.path.join(PROJECT_DIR, f"{PROJECT_NAME}.slcp"), "w") as fp:
        fp.write(slcp_tpl)

    if not len(os.listdir(PROJECT_SRC_DIR)):
        with open(os.path.join(PROJECT_SRC_DIR, "main.c"), "w") as fp:
            fp.write(main_tpl)


slcp_config_path = get_project_slcp_file()
if is_project_empty(slcp_config_path):
    generate_default_project(board_config)

target = board_config.get("build.gecko-sdk.variant", env.subst("$BOARD"))
if is_sdk_reload_required(slcp_config_path):
    print("Reloading SDK configuration...")
    reload_sdk_configuration(board_config, slcp_config_path)


project_config = load_project_config()
process_build_flags(project_config)
process_project_includes(project_config)
process_project_libraries(project_config)

# Temporary fix as SLC CLI doesn't export all flags
env.Append(
    LINKFLAGS=["--specs=nosys.specs"]
)

#
# Target: Build project sources
#

build_source_files(project_config)

#
# Target: Process Linker script
#

if not board_config.get("build.ldscript", ""):
    ldscript = board_config.get(
        "build.gecko-sdk.ldscript", extract_linker_script(project_config)
    )
    if ldscript:
        env.Replace(LDSCRIPT_PATH=ldscript)
    else:
        print("Warning! Failed to extract ldscript from the SDK configuration!")
