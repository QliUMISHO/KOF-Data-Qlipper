from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class BinaryWriteError(ValueError):
    pass


@dataclass
class BinaryWriter:
    data: bytearray

    @classmethod
    def from_bytes(cls, data: bytes | bytearray) -> "BinaryWriter":
        return cls(bytearray(data))

    @property
    def size(self) -> int:
        return len(self.data)

    def _check_range(self, offset: int, count: int) -> None:
        if offset < 0 or count < 0 or offset + count > len(self.data):
            raise BinaryWriteError(
                f"Write of {count} bytes at 0x{offset:X} exceeds buffer "
                f"size 0x{len(self.data):X}"
            )

    def write_bytes(self, offset: int, value: bytes | bytearray) -> None:
        self._check_range(offset, len(value))
        self.data[offset:offset + len(value)] = value

    def write_u8(self, offset: int, value: int) -> None:
        self.write_bytes(offset, int(value).to_bytes(1, "big", signed=False))

    def write_u16_be(self, offset: int, value: int) -> None:
        self.write_bytes(offset, int(value).to_bytes(2, "big", signed=False))

    def write_i16_be(self, offset: int, value: int) -> None:
        self.write_bytes(offset, int(value).to_bytes(2, "big", signed=True))

    def write_u32_be(self, offset: int, value: int) -> None:
        self.write_bytes(offset, int(value).to_bytes(4, "big", signed=False))

    def save(self, path: str | Path) -> None:
        Path(path).write_bytes(self.data)
