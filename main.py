"""Validate the competition image and copy it to the Make.fun output folder."""

from __future__ import annotations

import os
import shutil
import struct
from pathlib import Path


MAX_FILE_SIZE = 1_048_576
EXPECTED_DIMENSIONS = (1024, 1024)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_dimensions(path: Path) -> tuple[int, int]:
    """Read the width and height from a PNG's IHDR chunk."""
    try:
        with path.open("rb") as image:
            if image.read(len(PNG_SIGNATURE)) != PNG_SIGNATURE:
                raise ValueError("不是有效的 PNG 文件")

            chunk_length_bytes = image.read(4)
            chunk_type = image.read(4)
            if len(chunk_length_bytes) != 4 or chunk_type != b"IHDR":
                raise ValueError("缺少 PNG IHDR 信息")

            chunk_length = struct.unpack(">I", chunk_length_bytes)[0]
            if chunk_length < 8:
                raise ValueError("PNG IHDR 信息不完整")

            dimensions = image.read(8)
            if len(dimensions) != 8:
                raise ValueError("PNG IHDR 信息不完整")
            return struct.unpack(">II", dimensions)
    except OSError as error:
        raise ValueError(f"无法读取 PNG 文件：{error}") from error


def main() -> None:
    """Validate the sibling ``entry.png`` and copy it to the output directory.

    The output directory is taken from ``MAKEFUN_OUTPUT_DIR`` and defaults to
    ``/output``. Validation requires a 1024x1024 PNG no larger than 1,048,576
    bytes; any failure exits with a human-readable reason.
    """
    source = Path(__file__).resolve().parent / "entry.png"

    if not source.is_file():
        raise SystemExit(f"校验失败：同目录不存在 {source.name}")

    try:
        dimensions = _png_dimensions(source)
    except ValueError as error:
        raise SystemExit(f"校验失败：{error}") from error
    if dimensions != EXPECTED_DIMENSIONS:
        width, height = dimensions
        raise SystemExit(
            f"校验失败：entry.png 尺寸为 {width}x{height}，要求 1024x1024"
        )

    file_size = source.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise SystemExit(
            f"校验失败：entry.png 大小为 {file_size} 字节，不能超过 {MAX_FILE_SIZE} 字节"
        )

    output_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / source.name
    shutil.copy2(source, destination)
    destination_size = destination.stat().st_size
    if destination_size != source.stat().st_size: raise SystemExit("校验失败：拷贝后的文件大小与源文件不一致")
    print(f"verified: {dimensions[0]}x{dimensions[1]}, {destination_size} bytes")
    print(destination)


if __name__ == "__main__":
    main()
