from __future__ import annotations

from dataclasses import dataclass


class BinaryReadError(ValueError):
    pass


@dataclass
class BinaryReader:
    data: bytes | bytearray | memoryview
    offset: int = 0

    def __post_init__(self) -> None:
        self._view = memoryview(self.data)
        self.seek(self.offset)

    @property
    def size(self) -> int:
        return len(self._view)

    def tell(self) -> int:
        return self.offset

    def seek(self, offset: int) -> None:
        if not 0 <= offset <= len(self._view):
            raise BinaryReadError(
                f"Offset 0x{offset:X} is outside buffer size 0x{len(self._view):X}"
            )
        self.offset = offset

    def skip(self, count: int) -> None:
        self.seek(self.offset + count)

    def _take(self, count: int) -> memoryview:
        end = self.offset + count
        if count < 0 or end > len(self._view):
            raise BinaryReadError(
                f"Read of {count} bytes at 0x{self.offset:X} exceeds buffer"
            )
        chunk = self._view[self.offset:end]
        self.offset = end
        return chunk

    def read_bytes(self, count: int) -> bytes:
        return bytes(self._take(count))

    def read_u8(self) -> int:
        return int.from_bytes(self._take(1), "big", signed=False)

    def read_i8(self) -> int:
        return int.from_bytes(self._take(1), "big", signed=True)

    def read_u16_be(self) -> int:
        return int.from_bytes(self._take(2), "big", signed=False)

    def read_i16_be(self) -> int:
        return int.from_bytes(self._take(2), "big", signed=True)

    def read_u16_le(self) -> int:
        return int.from_bytes(self._take(2), "little", signed=False)

    def read_u32_be(self) -> int:
        return int.from_bytes(self._take(4), "big", signed=False)

    def read_i32_be(self) -> int:
        return int.from_bytes(self._take(4), "big", signed=True)

    def read_u32_le(self) -> int:
        return int.from_bytes(self._take(4), "little", signed=False)

    def peek_bytes(self, offset: int, count: int) -> bytes:
        if offset < 0 or offset + count > len(self._view):
            raise BinaryReadError("Peek exceeds buffer")
        return bytes(self._view[offset:offset + count])
