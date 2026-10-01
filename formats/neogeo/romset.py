from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import re

from core.rom import RomFile


_ROM_PATTERNS = (
    (re.compile(r"(?:^|[-_.])p\d+[a-z]?(?:[-_.]|$)", re.I), "P / 68000 program"),
    (re.compile(r"(?:^|[-_.])s\d*[a-z]?(?:[-_.]|$)", re.I), "S / fixed layer"),
    (re.compile(r"(?:^|[-_.])c\d+[a-z]?(?:[-_.]|$)", re.I), "C / sprites"),
    (re.compile(r"(?:^|[-_.])m\d+[a-z]?(?:[-_.]|$)", re.I), "M / sound CPU"),
    (re.compile(r"(?:^|[-_.])v\d+[a-z]?(?:[-_.]|$)", re.I), "V / audio samples"),
)


def classify_rom(filename: str) -> str:
    stem = Path(filename).stem.lower()
    for pattern, role in _ROM_PATTERNS:
        if pattern.search(stem):
            return role
    return "Unknown"


@dataclass
class NeoGeoRomSet:
    directory: Path
    roms: list[RomFile] = field(default_factory=list)

    @classmethod
    def load_directory(cls, directory: str | Path) -> "NeoGeoRomSet":
        directory = Path(directory)

        if not directory.is_dir():
            raise NotADirectoryError(directory)

        candidates = [
            p for p in sorted(directory.iterdir())
            if p.is_file()
            and p.suffix.lower() in {".bin", ".rom", ".p1", ".p2", ".c1", ".c2",
                                     ".s1", ".m1", ".v1", ".v2", ".sp1", ".sp2"}
        ]

        # Some sets use extension-less files. If no conventional files were
        # found, show all files rather than pretending the folder is empty.
        if not candidates:
            candidates = [p for p in sorted(directory.iterdir()) if p.is_file()]

        return cls(
            directory=directory,
            roms=[RomFile.load(path) for path in candidates],
        )

    def find_by_name(self, name: str) -> RomFile | None:
        name = name.lower()
        return next((rom for rom in self.roms if rom.name.lower() == name), None)

    def program_roms(self) -> list[RomFile]:
        return [r for r in self.roms if classify_rom(r.name).startswith("P /")]

    def sprite_roms(self) -> list[RomFile]:
        return [r for r in self.roms if classify_rom(r.name).startswith("C /")]
