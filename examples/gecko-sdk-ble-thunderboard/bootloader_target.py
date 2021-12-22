import os

Import("env")

from SCons.Script import COMMAND_LINE_TARGETS

if "idedata" in COMMAND_LINE_TARGETS:
    env.Exit(0)


custom_bootloader_bin = env.GetProjectOption("custom_bootloader_bin", "")
assert os.path.isfile(custom_bootloader_bin), "Missing bootloader binary!"

if "program_bootloader" in COMMAND_LINE_TARGETS:
    env.Replace(
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, "%s")}"'
        % custom_bootloader_bin
    )

    env.BoardConfig().update("upload.offset_address", "0x0")

env.AddCustomTarget(
    "program_bootloader",
    None,
    env.VerboseAction("$UPLOADCMD", "Programming bootloader..."),
    title="Program bootloader",
    description="A custom target for programming bootloader binary within a standalone project",
    always_build=True,
)
