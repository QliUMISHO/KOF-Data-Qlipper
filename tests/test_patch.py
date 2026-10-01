from pathlib import Path

import pytest

from core.patch import PatchError, RomPatch
from core.rom import RomFile


def make_rom(tmp_path: Path, data: bytes) -> RomFile:
    path = tmp_path / "test.bin"
    path.write_bytes(data)
    return RomFile.load(path)


def test_patch_applies_when_expected_bytes_match(tmp_path):
    rom = make_rom(tmp_path, bytes.fromhex("00 11 22 33"))
    patch = RomPatch.from_dict({
        "name": "test",
        "changes": [{
            "offset": "0x1",
            "expected": "11 22",
            "replace": "AA BB"
        }]
    })

    patch.apply(rom)

    assert bytes(rom.data) == bytes.fromhex("00 AA BB 33")


def test_patch_rejects_mismatch(tmp_path):
    rom = make_rom(tmp_path, bytes.fromhex("00 11 22 33"))
    patch = RomPatch.from_dict({
        "name": "test",
        "changes": [{
            "offset": "0x1",
            "expected": "FE ED",
            "replace": "AA BB"
        }]
    })

    with pytest.raises(PatchError):
        patch.apply(rom)
