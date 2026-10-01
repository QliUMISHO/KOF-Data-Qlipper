from __future__ import annotations

from pathlib import Path


def _lua_string(
    value: str | Path,
) -> str:
    """
    Convert a path into something safe for
    a basic Lua quoted string.

    Forward slashes avoid Windows backslash
    escaping problems.
    """

    text = (
        str(
            Path(value).resolve()
        )
        .replace("\\", "/")
    )

    return text.replace(
        '"',
        '\\"',
    )


def build_sprite_dump_script(
    output_path: str | Path,
) -> str:
    """
    Generate the Lua program that MAME runs
    after KOF 2003 boots.

    MAME has already processed the game's
    graphics protection before this script
    reads the :sprites memory region.
    """

    output = _lua_string(
        output_path
    )

    return f'''
local output_path = "{output}"

local region =
    manager.machine.memory.regions[":sprites"]

if region == nil then
    error(
        "KOF Studio: MAME memory region :sprites was not found"
    )
end


local file, err =
    io.open(
        output_path,
        "wb"
    )

if file == nil then
    error(
        "KOF Studio: unable to create sprite dump: "
        .. tostring(err)
    )
end


local chunk_size =
    1024 * 1024

local offset =
    0


while offset < region.size do

    local remaining =
        region.size - offset

    local amount =
        math.min(
            chunk_size,
            remaining
        )

    local data =
        region:read(
            offset,
            amount
        )

    if data == nil or #data == 0 then

        file:close()

        error(
            "KOF Studio: MAME returned no sprite data at offset "
            .. tostring(offset)
        )

    end

    file:write(data)

    offset =
        offset + #data

end


file:close()


manager.machine:popmessage(
    "KOF Studio sprite extraction completed"
)


manager.machine:exit()
'''.strip() + "\n"


def build_extraction_arguments(
    system_name: str,
    rom_root: str | Path,
    lua_script: str | Path,
) -> list[str]:
    """
    Command arguments passed to MAME.

    MAME is being used as a backend here,
    therefore video/audio are disabled.
    """

    return [

        system_name,

        "-rompath",
        str(
            Path(rom_root).resolve()
        ),

        "-autoboot_delay",
        "1",

        "-autoboot_script",
        str(
            Path(lua_script).resolve()
        ),

        "-video",
        "none",

        "-sound",
        "none",

        "-nothrottle",

        "-skip_gameinfo",

        "-noconfirm_quit",

        # Safety fallback in case the Lua
        # script doesn't exit MAME.
        "-seconds_to_run",
        "60",
    ]