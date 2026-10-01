from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json

from core.rom import RomFile


class PatchError(RuntimeError):
    pass


def _hex_to_bytes(value: str) -> bytes:
    cleaned = value.replace(" ", "").replace("_", "")
    if len(cleaned) % 2:
        raise PatchError(f"Hex string must contain complete bytes: {value!r}")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise PatchError(f"Invalid hex string: {value!r}") from exc


@dataclass(frozen=True)
class PatchChange:
    offset: int
    expected: bytes
    replace: bytes
    description: str = ""

    @classmethod
    def from_dict(cls, item: dict) -> "PatchChange":
        offset_value = item["offset"]
        offset = (
            int(offset_value, 0)
            if isinstance(offset_value, str)
            else int(offset_value)
        )
        return cls(
            offset=offset,
            expected=_hex_to_bytes(item.get("expected", "")),
            replace=_hex_to_bytes(item["replace"]),
            description=item.get("description", ""),
        )


@dataclass
class RomPatch:
    name: str
    changes: list[PatchChange]
    description: str = ""

    @classmethod
    def from_dict(cls, payload: dict) -> "RomPatch":
        return cls(
            name=payload["name"],
            description=payload.get("description", ""),
            changes=[PatchChange.from_dict(x) for x in payload.get("changes", [])],
        )

    @classmethod
    def load(cls, path: str | Path) -> "RomPatch":
        with Path(path).open("r", encoding="utf-8") as handle:
            return cls.from_dict(json.load(handle))

    def validate(self, rom: RomFile) -> list[str]:
        problems: list[str] = []

        for change in self.changes:
            end = change.offset + max(len(change.expected), len(change.replace))
            if change.offset < 0 or end > rom.size:
                problems.append(
                    f"0x{change.offset:X}: patch exceeds ROM size"
                )
                continue

            if change.expected:
                actual = bytes(
                    rom.data[change.offset:change.offset + len(change.expected)]
                )
                if actual != change.expected:
                    problems.append(
                        f"0x{change.offset:X}: expected "
                        f"{change.expected.hex(' ')}, found {actual.hex(' ')}"
                    )

        return problems

    def apply(self, rom: RomFile, strict: bool = True) -> None:
        problems = self.validate(rom)
        if problems and strict:
            raise PatchError("\n".join(problems))

        for change in self.changes:
            end = change.offset + len(change.replace)
            if end > rom.size:
                if strict:
                    raise PatchError(
                        f"Patch write at 0x{change.offset:X} exceeds ROM size"
                    )
                continue
            rom.data[change.offset:end] = change.replace
