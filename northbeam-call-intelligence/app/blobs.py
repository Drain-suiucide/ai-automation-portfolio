"""Local filesystem blob store for audio. The seam for S3/MinIO is the same four methods."""

from __future__ import annotations

import re
import shutil
from pathlib import Path


class BlobError(ValueError):
    pass


def safe_name(name: str) -> str:
    base = name.replace("\\", "/").rsplit("/", 1)[-1]
    return re.sub(r"[^A-Za-z0-9._-]", "_", base)[:120] or "audio"


class LocalBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def path(self, key: str) -> Path:
        p = (self.root / key).resolve()
        if not p.is_relative_to(self.root.resolve()):
            raise BlobError("key escapes the blob root")
        return p

    def put(self, key: str, data: bytes) -> None:
        p = self.path(key)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def read(self, key: str) -> bytes:
        return self.path(key).read_bytes()

    def exists(self, key: str) -> bool:
        return self.path(key).is_file()

    def move(self, src_key: str, dst_key: str) -> None:
        src, dst = self.path(src_key), self.path(dst_key)
        if not src.is_file():
            raise BlobError(f"no such object: {src_key}")
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    def delete_prefix(self, prefix: str) -> int:
        """Delete every object under prefix (a 'directory'). Returns number of files removed."""
        p = self.path(prefix)
        if not p.exists():
            return 0
        if p.is_file():
            p.unlink()
            return 1
        n = sum(1 for f in p.rglob("*") if f.is_file())
        shutil.rmtree(p)
        return n

    def all_keys(self) -> list[str]:
        return sorted(str(f.relative_to(self.root)) for f in self.root.rglob("*") if f.is_file())
