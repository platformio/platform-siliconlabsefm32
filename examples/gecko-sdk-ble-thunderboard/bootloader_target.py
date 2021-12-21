import os

Import("env")

from SCons.Script import COMMAND_LINE_TARGETS

if "idedata" in COMMAND_LINE_TARGETS:
    env.Exit(0)


BOOTLOADER_BINARY = "brd4184a_boot.bin"
assert os.path.isfile(BOOTLOADER_BINARY), "Missing bootloader binary!"

if "program_bootloader" in COMMAND_LINE_TARGETS:
    env.Replace(
        UPLOADCMD='$UPLOADER $UPLOADERFLAGS -CommanderScript "${__jlink_cmd_script(__env__, "%s")}"'
        % BOOTLOADER_BINARY
    )

    env.BoardConfig().update("upload.offset_address", "0x0")

env.AddCustomTarget(
    "program_bootloader",
    None,
    env.VerboseAction("$UPLOADCMD", "Programming bootloader..."),
    title=None,
    description=None,
    always_build=True,
)
