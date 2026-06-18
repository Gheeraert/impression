from __future__ import annotations

import json
import urllib.error
from pathlib import Path
from unittest.mock import Mock

import pytest

import experiments.circe_spike.circe_client as circe_client
from experiments.circe_spike.circe_client import (
    ExperimentState,
    build_parser,
    dry_run,
    load_config,
    prepare_output_dir,
    validate_input_file,
    write_report,
)


def test_load_config_reads_json(tmp_path: Path) -> None:
    config_path = tmp_path / "circe_config.json"
    config_path.write_text(
        json.dumps(
            {
                "base_url": "https://circe.unicaen.fr",
                "upload_endpoint": "/upload",
                "conversions_endpoint": "/conversions",
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config["base_url"] == "https://circe.unicaen.fr"
    assert config["upload_endpoint"] == "/upload"


def test_validate_input_file_rejects_missing_file(tmp_path: Path) -> None:
    missing_file = tmp_path / "missing.xml"

    with pytest.raises(FileNotFoundError, match="introuvable"):
        validate_input_file(missing_file)


def test_prepare_output_dir_creates_directory(tmp_path: Path) -> None:
    output_dir = tmp_path / "nested" / "out"

    prepared = prepare_output_dir(output_dir)

    assert prepared == output_dir
    assert output_dir.exists()
    assert output_dir.is_dir()


def test_list_conversions_can_be_parsed_without_input() -> None:
    args = build_parser().parse_args(
        [
            "--config",
            "circe_config.json",
            "--list-conversions",
            "--output-dir",
            "out",
        ]
    )

    assert args.input is None
    assert args.list_conversions is True


def test_dry_run_builds_urls_without_network() -> None:
    args = build_parser().parse_args(
        [
            "--config",
            "circe_config.json",
            "--input",
            "sample.xml",
            "--conversion",
            "tei-to-latex",
            "--list-conversions",
            "--output-dir",
            "out",
            "--dry-run",
        ]
    )
    config = {
        "base_url": "https://circe.unicaen.fr",
        "upload_endpoint": "/api/upload",
        "conversions_endpoint": "/api/conversions",
        "convert_endpoint": "/api/convert",
        "download_endpoint": "/api/download",
    }

    urls = dry_run(config, args)

    assert urls == [
        "https://circe.unicaen.fr/api/conversions",
        "https://circe.unicaen.fr/api/upload",
        "https://circe.unicaen.fr/api/convert",
        "https://circe.unicaen.fr/api/download",
    ]


def test_write_report_contains_empty_verdict(tmp_path: Path) -> None:
    output_dir = prepare_output_dir(tmp_path / "out")
    state = ExperimentState(
        input_file=None,
        output_dir=output_dir,
        conversion=None,
        config_path=tmp_path / "circe_config.json",
    )

    report_path = write_report(state, {"base_url": "https://circe.unicaen.fr"})

    report = report_path.read_text(encoding="utf-8")
    assert "- Verdict : " in report


def test_upload_file_uses_unique_multipart_boundary(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    input_file = tmp_path / "sample.xml"
    input_file.write_text("<TEI/>", encoding="utf-8")
    config = {"base_url": "https://circe.unicaen.fr", "upload_endpoint": "/upload"}
    content_types: list[str] = []

    def fake_request(method: str, url: str, **kwargs: object) -> dict[str, object]:
        content_types.append(kwargs["headers"]["Content-Type"])  # type: ignore[index]
        return {"status": 200, "headers": {"Content-Type": "application/json"}, "body": b'{"ok": true}'}

    monkeypatch.setattr(circe_client, "_request", fake_request)

    circe_client.upload_file(config, input_file, tmp_path)
    circe_client.upload_file(config, input_file, tmp_path)

    assert content_types[0] != content_types[1]
    assert "----circe-spike-" in content_types[0]


def test_request_saves_http_error_body(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    error = urllib.error.HTTPError(
        url="https://circe.unicaen.fr/api",
        code=500,
        msg="Server Error",
        hdrs={},
        fp=Mock(read=Mock(return_value=b"erreur circe detaillee")),
    )
    monkeypatch.setattr(circe_client.urllib.request, "urlopen", Mock(side_effect=error))

    with pytest.raises(circe_client.CirceClientError, match="HTTP 500"):
        circe_client._request("GET", "https://circe.unicaen.fr/api", error_dir=tmp_path)

    assert (tmp_path / "http_error_500.txt").read_bytes() == b"erreur circe detaillee"
