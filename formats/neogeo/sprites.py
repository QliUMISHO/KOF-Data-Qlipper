from __future__ import annotations

TILE_BYTES = 0x80
TILE_WIDTH = 16
TILE_HEIGHT = 16


class SpriteDecodeError(ValueError):
    pass


def _bit(value: int, n: int) -> int:
    return (value >> n) & 1


def decode_decrypted_tile(
    region: bytes | bytearray | memoryview,
    tile_index: int,
) -> list[int]:
    """
    Decode one 16x16 Neo Geo 4bpp tile into palette indices 0..15.

    The input must already be the decrypted Neo Geo sprite region. For KOF 2003
    do not feed the encrypted C1/C2/etc. files directly into this routine.
    """
    if tile_index < 0:
        raise SpriteDecodeError("Tile index cannot be negative")

    start = tile_index * TILE_BYTES
    end = start + TILE_BYTES
    if end > len(region):
        raise SpriteDecodeError(
            f"Tile 0x{tile_index:X} exceeds sprite region ({len(region):,} bytes)"
        )

    src = region[start:end]
    pixels: list[int] = []

    for y in range(16):
        row = y << 2

        for x in range(8):
            pixels.append(
                (_bit(src[0x43 | row], x) << 3)
                | (_bit(src[0x41 | row], x) << 2)
                | (_bit(src[0x42 | row], x) << 1)
                | _bit(src[0x40 | row], x)
            )

        for x in range(8):
            pixels.append(
                (_bit(src[0x03 | row], x) << 3)
                | (_bit(src[0x01 | row], x) << 2)
                | (_bit(src[0x02 | row], x) << 1)
                | _bit(src[0x00 | row], x)
            )

    return pixels


def tile_count(region: bytes | bytearray | memoryview) -> int:
    return len(region) // TILE_BYTES
