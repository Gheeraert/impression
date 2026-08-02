"""Lecture des dimensions d'une image depuis son en-tête, sans dépendance.

Ne décode pas l'image : lit uniquement les quelques octets d'en-tête qui
encodent la largeur/hauteur (PNG, JPEG, GIF, WebP). Utilisé pour injecter
width/height dans le HTML et éviter les décalages de mise en page pendant
le chargement (CLS), sans faire dépendre le pipeline principal de Pillow.
"""

from __future__ import annotations

import struct
from pathlib import Path


def read_image_dimensions(path: Path) -> tuple[int, int] | None:
    """Retourne (largeur, hauteur) en pixels, ou None si le format n'est pas
    reconnu ou que le fichier est illisible/corrompu."""

    try:
        with path.open("rb") as file:
            header = file.read(32)
            if header.startswith(b"\x89PNG\r\n\x1a\n"):
                return _png_dimensions(header)
            if header.startswith((b"GIF87a", b"GIF89a")):
                return _gif_dimensions(header)
            if header[0:4] == b"RIFF" and header[8:12] == b"WEBP":
                return _webp_dimensions(header)
            if header.startswith(b"\xff\xd8"):
                return _jpeg_dimensions(file)
    except OSError:
        return None
    return None


def _png_dimensions(header: bytes) -> tuple[int, int] | None:
    if len(header) < 24:
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def _gif_dimensions(header: bytes) -> tuple[int, int] | None:
    if len(header) < 10:
        return None
    width, height = struct.unpack("<HH", header[6:10])
    return width, height


def _webp_dimensions(header: bytes) -> tuple[int, int] | None:
    fourcc = header[12:16]
    if fourcc == b"VP8 " and len(header) >= 30:
        width = struct.unpack("<H", header[26:28])[0] & 0x3FFF
        height = struct.unpack("<H", header[28:30])[0] & 0x3FFF
        return width, height
    if fourcc == b"VP8L" and len(header) >= 25:
        b0, b1, b2, b3 = header[21], header[22], header[23], header[24]
        width = 1 + (((b1 & 0x3F) << 8) | b0)
        height = 1 + (((b3 & 0x0F) << 10) | (b2 << 2) | ((b1 & 0xC0) >> 6))
        return width, height
    if fourcc == b"VP8X" and len(header) >= 30:
        width = 1 + (header[24] | (header[25] << 8) | (header[26] << 16))
        height = 1 + (header[27] | (header[28] << 8) | (header[29] << 16))
        return width, height
    return None


_JPEG_SOF_MARKERS = frozenset(
    {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF}
)


def _jpeg_dimensions(file) -> tuple[int, int] | None:
    file.seek(2)
    try:
        while True:
            marker = file.read(1)
            if not marker:
                return None
            while marker != b"\xff":
                marker = file.read(1)
                if not marker:
                    return None
            code_byte = file.read(1)
            while code_byte == b"\xff":
                code_byte = file.read(1)
            if not code_byte:
                return None
            code = code_byte[0]
            if code in _JPEG_SOF_MARKERS:
                file.read(3)
                dimensions = file.read(4)
                if len(dimensions) < 4:
                    return None
                height, width = struct.unpack(">HH", dimensions)
                return width, height
            length_bytes = file.read(2)
            if len(length_bytes) < 2:
                return None
            length = struct.unpack(">H", length_bytes)[0]
            if length < 2:
                return None
            file.seek(length - 2, 1)
    except (struct.error, OSError):
        return None
