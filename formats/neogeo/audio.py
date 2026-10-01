from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioRegion:
    name: str
    offset: int
    size: int


def extract_region(
    data: bytes | bytearray,
    region: AudioRegion,
) -> bytes:
    if region.offset < 0 or region.offset + region.size > len(data):
        raise ValueError("Audio region exceeds ROM")
    return bytes(data[region.offset:region.offset + region.size])
