from __future__ import annotations

import hashlib
import zlib
from pathlib import Path


def crc32_bytes(data: bytes | bytearray) -> str:
    return f"{zlib.crc32(data) & 0xFFFFFFFF:08x}"


def sha1_bytes(data: bytes | bytearray) -> str:
    return hashlib.sha1(data).hexdigest()


def sha256_bytes(data: bytes | bytearray) -> str:
    return hashlib.sha256(data).hexdigest()


def file_checksums(path: str | Path, chunk_size: int = 1024 * 1024) -> dict[str, str]:
    path = Path(path)

    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    crc = 0

    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            sha1.update(chunk)
            sha256.update(chunk)
            crc = zlib.crc32(chunk, crc)

    return {
        "crc32": f"{crc & 0xFFFFFFFF:08x}",
        "sha1": sha1.hexdigest(),
        "sha256": sha256.hexdigest(),
    }
