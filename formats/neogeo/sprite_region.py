from __future__ import annotations

from pathlib import Path
from formats.neogeo.sprites import decode_decrypted_tile, tile_count


class DecryptedSpriteRegion:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.data = self.path.read_bytes()

        if len(self.data) < 0x80:
            raise ValueError("Sprite region is too small")
        if len(self.data) % 0x80:
            raise ValueError("Sprite region size is not aligned to 0x80-byte tiles")

    @property
    def tile_count(self) -> int:
        return tile_count(self.data)

    @property
    def size(self) -> int:
        return len(self.data)

    def decode_tile(self, tile_index: int) -> list[int]:
        return decode_decrypted_tile(self.data, tile_index)
