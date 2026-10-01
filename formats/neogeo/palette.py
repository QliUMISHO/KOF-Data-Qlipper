from __future__ import annotations

"""
Neo Geo palette support.

For now this module intentionally keeps colors as raw 16-bit words.
KOF Studio should not silently assume a bit layout until the exact Neo Geo
palette encoding used by the target pipeline has been verified.

The GUI can still inspect, compare, export and later decode these words.
"""


def read_palette_words(
    data: bytes | bytearray,
    offset: int,
    count: int = 16,
) -> list[int]:
    end = offset + count * 2
    if offset < 0 or end > len(data):
        raise ValueError("Palette range exceeds buffer")

    return [
        int.from_bytes(data[pos:pos + 2], "big")
        for pos in range(offset, end, 2)
    ]


def write_palette_words(
    data: bytearray,
    offset: int,
    words: list[int],
) -> None:
    end = offset + len(words) * 2
    if offset < 0 or end > len(data):
        raise ValueError("Palette range exceeds buffer")

    for index, word in enumerate(words):
        if not 0 <= word <= 0xFFFF:
            raise ValueError(f"Palette word out of range: {word}")
        pos = offset + index * 2
        data[pos:pos + 2] = word.to_bytes(2, "big")
