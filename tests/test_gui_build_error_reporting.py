from __future__ import annotations

"""_truncate_for_dialog / App._write_build_error_log — a build error must
always be readable and never silently lost, even when the underlying
exception message is impractically long (e.g. hundreds of duplicate xml:id
across a many-chapter book)."""

from pathlib import Path

from purh_site.gui import _MAX_DIALOG_MESSAGE_LENGTH, _truncate_for_dialog


def test_short_message_is_returned_unchanged_with_log_pointer() -> None:
    log_path = Path("build_error.log")
    result = _truncate_for_dialog("Erreur simple.", log_path)

    assert result.startswith("Erreur simple.")
    assert str(log_path) in result


def test_short_message_without_log_path_has_no_pointer() -> None:
    result = _truncate_for_dialog("Erreur simple.", None)

    assert result == "Erreur simple."


def test_long_message_is_truncated_and_points_to_log() -> None:
    message = "x" * (_MAX_DIALOG_MESSAGE_LENGTH * 5)
    log_path = Path("build_error.log")

    result = _truncate_for_dialog(message, log_path)

    assert len(result) < len(message)
    assert result.startswith("x" * 100)
    assert "tronqué" in result
    assert str(log_path) in result


def test_long_message_without_log_path_still_notes_truncation() -> None:
    message = "x" * (_MAX_DIALOG_MESSAGE_LENGTH * 5)

    result = _truncate_for_dialog(message, None)

    assert "tronqué" in result
    assert len(result) < len(message)
