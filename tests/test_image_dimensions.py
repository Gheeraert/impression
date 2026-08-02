from __future__ import annotations

"""Tests du lecteur de dimensions d'image sans dépendance
(purh_site/image_dimensions.py). Les images de test sont de vrais
fichiers PNG/JPEG/GIF/WebP minimaux (générés une fois avec Pillow puis
figés en base64 ici, pour ne pas faire dépendre la suite de tests de
Pillow)."""

import base64
from pathlib import Path

from purh_site.image_dimensions import read_image_dimensions

PNG_15x10_B64 = "iVBORw0KGgoAAAANSUhEUgAAAA8AAAAKCAIAAADkeZOuAAAAGElEQVR4nGP8z0ACYCJFMcOoakxAyzABAN0IARNDUhaOAAAAAElFTkSuQmCC"
JPEG_20x12_B64 = "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAAMABQDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDi6KKK+ZP3EKKKKAP/2Q=="
GIF_8x6_B64 = "R0lGODdhCAAGAIEAAP8AAAAAAAAAAAAAACwAAAAACAAGAAAIDgABCBxIsKDBgwgTDgwIADs="
WEBP_11x7_B64 = "UklGRjwAAABXRUJQVlA4IDAAAADQAQCdASoLAAcAAUAmJaACdLoB+AADsAD+8ut//NgVzXPv9//S4P0uD9Lg/9KQAAA="


def _write(tmp_path: Path, name: str, b64: str) -> Path:
    path = tmp_path / name
    path.write_bytes(base64.b64decode(b64))
    return path


def test_png_dimensions(tmp_path: Path) -> None:
    path = _write(tmp_path, "img.png", PNG_15x10_B64)
    assert read_image_dimensions(path) == (15, 10)


def test_jpeg_dimensions(tmp_path: Path) -> None:
    path = _write(tmp_path, "img.jpg", JPEG_20x12_B64)
    assert read_image_dimensions(path) == (20, 12)


def test_gif_dimensions(tmp_path: Path) -> None:
    path = _write(tmp_path, "img.gif", GIF_8x6_B64)
    assert read_image_dimensions(path) == (8, 6)


def test_webp_dimensions(tmp_path: Path) -> None:
    path = _write(tmp_path, "img.webp", WEBP_11x7_B64)
    assert read_image_dimensions(path) == (11, 7)


def test_missing_file_returns_none(tmp_path: Path) -> None:
    assert read_image_dimensions(tmp_path / "absent.png") is None


def test_truncated_file_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "truncated.jpg"
    path.write_bytes(b"\xff\xd8\xff")
    assert read_image_dimensions(path) is None


def test_unsupported_format_returns_none(tmp_path: Path) -> None:
    path = tmp_path / "notes.txt"
    path.write_bytes(b"Ceci n'est pas une image.")
    assert read_image_dimensions(path) is None
