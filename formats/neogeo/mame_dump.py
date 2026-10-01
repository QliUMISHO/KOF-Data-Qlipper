from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


def _lua_path(path: str | Path) -> str:
    value = str(Path(path).resolve()).replace("\\", "/")
    return value.replace('"', '\\"')


def build_sprite_dump_lua(output_path: str | Path) -> str:
    output = _lua_path(output_path)
    return (
        'local output_path = "' + output + '"\n'
        'local region = manager.machine.memory.regions[":sprites"]\n'
        '\n'
        'if region == nil then\n'
        '    error("KOF Studio: memory region :sprites was not found")\n'
        'end\n'
        '\n'
        'local file, err = io.open(output_path, "wb")\n'
        'if file == nil then\n'
        '    error("KOF Studio: cannot open output file: " .. tostring(err))\n'
        'end\n'
        '\n'
        'local chunk_size = 1024 * 1024\n'
        'local offset = 0\n'
        'while offset < region.size do\n'
        '    local remaining = region.size - offset\n'
        '    local amount = math.min(chunk_size, remaining)\n'
        '    file:write(region:read(offset, amount))\n'
        '    offset = offset + amount\n'
        'end\n'
        '\n'
        'file:close()\n'
        'manager.machine:popmessage("KOF Studio sprite dump complete")\n'
        'manager.machine:exit()\n'
    )


@dataclass
class MameDumpJob:
    program: Path
    arguments: list[str]
    script_path: Path
    output_path: Path


def create_mame_dump_job(
    mame_executable: str | Path,
    rompath: str | Path,
    output_path: str | Path,
    system_name: str = "kof2003",
) -> MameDumpJob:
    exe = Path(mame_executable)
    if not exe.is_file():
        raise FileNotFoundError(f"MAME executable not found: {exe}")

    rompath = Path(rompath)
    if not rompath.exists():
        raise FileNotFoundError(f"MAME ROM path not found: {rompath}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    script_dir = output_path.parent / ".kofstudio"
    script_dir.mkdir(parents=True, exist_ok=True)
    script_path = script_dir / "dump_neogeo_sprites.lua"
    script_path.write_text(build_sprite_dump_lua(output_path), encoding="utf-8")

    args = [
        system_name,
        "-rompath", str(rompath),
        "-autoboot_delay", "1",
        "-autoboot_script", str(script_path),
        "-skip_gameinfo",
        "-nothrottle",
    ]

    return MameDumpJob(
        program=exe,
        arguments=args,
        script_path=script_path,
        output_path=output_path,
    )
