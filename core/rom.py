from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from core.binary_reader import BinaryReader
from core.binary_writer import BinaryWriter
from core.checksum import crc32_bytes, sha1_bytes, sha256_bytes


@dataclass
class RomFile:
    path: Path
    data: bytearray
    original_data: bytes = field(repr=False)

    @classmethod
    def load(cls, path: str | Path) -> "RomFile":
        path = Path(path)
        raw = path.read_bytes()
        return cls(path=path, data=bytearray(raw), original_data=raw)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def size(self) -> int:
        return len(self.data)

    @property
    def modified(self) -> bool:
        return bytes(self.data) != self.original_data

    def reader(self, offset: int = 0) -> BinaryReader:
        return BinaryReader(self.data, offset)

    def writer(self) -> BinaryWriter:
        return BinaryWriter(self.data)

    def reset(self) -> None:
        self.data[:] = self.original_data

    def hashes(self) -> dict[str, str]:
        return {
            "crc32": crc32_bytes(self.data),
            "sha1": sha1_bytes(self.data),
            "sha256": sha256_bytes(self.data),
        }

    def save_as(self, path: str | Path) -> None:
        Path(path).write_bytes(self.data)
