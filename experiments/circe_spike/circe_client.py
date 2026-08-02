from __future__ import annotations

import argparse
import json
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zipfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

INCOMPLETE_CONFIG_MESSAGE = (
    "Configuration Circé incomplète : renseigner les endpoints dans "
    "circe_config.json après inspection de l'API ou de la documentation."
)


class CirceConfigurationError(RuntimeError):
    """Raised when the local Circe API configuration is missing required data."""


class CirceClientError(RuntimeError):
    """Raised when a Circe exploration request cannot be completed."""


@dataclass
class ExperimentState:
    """Tracks local artifacts created during one experimental run."""

    input_file: Path | None
    output_dir: Path
    conversion: str | None = None
    started_at: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    config_path: Path | None = None
    uploaded_response_path: Path | None = None
    conversions_response_path: Path | None = None
    conversion_response_path: Path | None = None
    downloaded_paths: list[Path] = field(default_factory=list)
    extracted_dir: Path | None = None
    out_log_path: Path | None = None
    messages: list[str] = field(default_factory=list)


def load_config(config_path: Path) -> dict[str, Any]:
    """Load a Circe spike JSON configuration file."""

    if not config_path.exists():
        raise CirceConfigurationError(f"Fichier de configuration introuvable : {config_path}")
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise CirceConfigurationError(f"Configuration JSON invalide : {exc}") from exc
    if not isinstance(data, dict):
        raise CirceConfigurationError("La configuration Circe doit etre un objet JSON.")
    return data


def validate_input_file(input_file: Path) -> Path:
    """Return the input path when it exists, otherwise fail with a clear message."""

    if not input_file.exists():
        raise FileNotFoundError(f"Fichier XML d'entree introuvable : {input_file}")
    if not input_file.is_file():
        raise FileNotFoundError(f"Le chemin d'entree n'est pas un fichier : {input_file}")
    return input_file


def prepare_output_dir(output_dir: Path) -> Path:
    """Create the output directory used for Circe experiment artifacts."""

    output_dir.mkdir(parents=True, exist_ok=True)
    return output_dir


def upload_file(config: dict[str, Any], input_file: Path, output_dir: Path) -> dict[str, Any]:
    """Upload an XML file to Circe using the configured upload endpoint."""

    endpoint = _require_endpoint(config, "upload_endpoint")
    boundary = f"----circe-spike-{uuid.uuid4().hex}"
    file_bytes = input_file.read_bytes()
    body = b"".join(
        [
            f"--{boundary}\r\n".encode("ascii"),
            (
                'Content-Disposition: form-data; name="file"; '
                f'filename="{input_file.name}"\r\n'
            ).encode(),
            b"Content-Type: application/xml\r\n\r\n",
            file_bytes,
            b"\r\n",
            f"--{boundary}--\r\n".encode("ascii"),
        ]
    )
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    response = _request("POST", _absolute_url(config, endpoint), headers=headers, data=body, error_dir=output_dir)
    return _save_response(output_dir / "upload_response", response)


def list_conversions(config: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """Fetch the conversion list if Circe exposes a configured endpoint."""

    endpoint = _require_endpoint(config, "conversions_endpoint")
    response = _request("GET", _absolute_url(config, endpoint), error_dir=output_dir)
    return _save_response(output_dir / "conversions_response", response)


def request_conversion(
    config: dict[str, Any],
    upload_response: dict[str, Any],
    conversion: str,
    output_dir: Path,
) -> dict[str, Any]:
    """Ask Circe to run one conversion using the configured conversion endpoint."""

    endpoint = _require_endpoint(config, "convert_endpoint")
    payload = {
        "conversion": conversion,
        "upload_response": upload_response.get("json") or upload_response.get("text"),
    }
    extra_payload = config.get("convert_payload_extra")
    if isinstance(extra_payload, dict):
        payload.update(extra_payload)

    data = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json", "Accept": "application/json, */*"}
    response = _request("POST", _absolute_url(config, endpoint), headers=headers, data=data, error_dir=output_dir)
    return _save_response(output_dir / "conversion_response", response)


def download_results(
    config: dict[str, Any],
    conversion_response: dict[str, Any],
    output_dir: Path,
) -> list[Path]:
    """Download result archives or files referenced by Circe responses."""

    urls = _result_urls(config, conversion_response)
    downloaded: list[Path] = []
    for index, url in enumerate(urls, start=1):
        response = _request("GET", url, error_dir=output_dir)
        filename = _download_filename(url, response.get("headers", {}), index)
        target = output_dir / filename
        target.write_bytes(response["body"])
        downloaded.append(target)
    return downloaded


def extract_archive_if_needed(paths: list[Path], output_dir: Path) -> tuple[Path | None, Path | None]:
    """Extract returned zip archives and locate out.log when present."""

    extracted_dir: Path | None = None
    out_log_path: Path | None = None
    for path in paths:
        if not zipfile.is_zipfile(path):
            continue
        extracted_dir = output_dir / f"{path.stem}_extracted"
        extracted_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(extracted_dir)
        found_logs = sorted(extracted_dir.rglob("out.log"))
        if found_logs:
            out_log_path = output_dir / "out.log"
            shutil.copy2(found_logs[0], out_log_path)
    return extracted_dir, out_log_path


def write_report(state: ExperimentState, config: dict[str, Any]) -> Path:
    """Write a local Markdown report describing the Circe experiment run."""

    report_path = state.output_dir / "REPORT.md"
    lines = [
        "# Rapport d'experimentation Circe",
        "",
        f"- Date : {state.started_at}",
        f"- Fichier XML : `{state.input_file or 'non fourni'}`",
        f"- Conversion demandee : `{state.conversion or 'non renseignee'}`",
        f"- Configuration : `{state.config_path or 'non renseignee'}`",
        f"- Base URL : `{config.get('base_url', '')}`",
        "- Verdict : ",
        "",
        "## Artefacts",
        "",
    ]
    artifact_paths = [
        state.uploaded_response_path,
        state.conversions_response_path,
        state.conversion_response_path,
        *state.downloaded_paths,
        state.extracted_dir,
        state.out_log_path,
    ]
    existing = [path for path in artifact_paths if path is not None]
    if existing:
        lines.extend(f"- `{path}`" for path in existing)
    else:
        lines.append("- Aucun artefact produit.")
    lines.extend(["", "## Observations", ""])
    if state.messages:
        lines.extend(f"- {message}" for message in state.messages)
    else:
        lines.append("- Completer apres analyse des sorties Circe.")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def dry_run(config: dict[str, Any], args: argparse.Namespace) -> list[str]:
    """Validate configured endpoints for the requested operation without network calls."""

    urls: list[str] = []
    if args.list_conversions:
        urls.append(_absolute_url(config, _require_endpoint(config, "conversions_endpoint")))
    if args.conversion:
        urls.append(_absolute_url(config, _require_endpoint(config, "upload_endpoint")))
        urls.append(_absolute_url(config, _require_endpoint(config, "convert_endpoint")))
        download_endpoint = str(config.get("download_endpoint", "")).strip()
        if download_endpoint:
            urls.append(_absolute_url(config, download_endpoint))
    if not urls:
        raise CirceConfigurationError("Indiquer --list-conversions ou --conversion pour le dry-run.")
    return urls


def run(args: argparse.Namespace) -> int:
    """Run the CLI workflow for the configured Circe experiment."""

    config_path = Path(args.config)
    output_dir = prepare_output_dir(Path(args.output_dir))
    config = load_config(config_path)
    input_file = validate_input_file(Path(args.input)) if args.input else None
    state = ExperimentState(
        input_file=input_file,
        output_dir=output_dir,
        conversion=args.conversion,
        config_path=config_path,
    )

    try:
        if args.dry_run:
            urls = dry_run(config, args)
            state.messages.extend([f"Dry-run URL : `{url}`" for url in urls])
            print("Dry-run Circe : aucun appel reseau effectue.")
            for url in urls:
                print(f"- {url}")
            return 0

        if args.list_conversions:
            conversions = list_conversions(config, output_dir)
            state.conversions_response_path = Path(conversions["path"])
            state.messages.append("Liste des conversions demandee a Circe.")

        if args.conversion:
            if input_file is None:
                raise FileNotFoundError("Fichier XML d'entree requis pour demander une conversion.")
            upload_response = upload_file(config, input_file, output_dir)
            state.uploaded_response_path = Path(upload_response["path"])
            conversion_response = request_conversion(config, upload_response, args.conversion, output_dir)
            state.conversion_response_path = Path(conversion_response["path"])
            state.downloaded_paths = download_results(config, conversion_response, output_dir)
            state.extracted_dir, state.out_log_path = extract_archive_if_needed(
                state.downloaded_paths,
                output_dir,
            )
            if state.out_log_path:
                state.messages.append("out.log trouve et copie a la racine du dossier de sortie.")
            else:
                state.messages.append("Aucun out.log trouve dans les fichiers telecharges.")

        if not args.list_conversions and not args.conversion:
            raise CirceConfigurationError("Indiquer --list-conversions ou --conversion.")
    except CirceConfigurationError:
        raise
    finally:
        write_report(state, config)

    print(f"Experience Circe terminee. Rapport : {output_dir / 'REPORT.md'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""

    parser = argparse.ArgumentParser(description="Client experimental pour tester Circe avec du XML TEI/Metopes.")
    parser.add_argument("--config", required=True, help="Chemin du fichier circe_config.json.")
    parser.add_argument("--input", help="Chemin du fichier XML TEI/Metopes a envoyer.")
    parser.add_argument("--conversion", help="Nom de la conversion Circe a demander, ex. tei-to-latex.")
    parser.add_argument("--output-dir", required=True, help="Dossier local pour les sorties et le rapport.")
    parser.add_argument(
        "--list-conversions",
        action="store_true",
        help="Lister les conversions disponibles si l'API Circe expose un endpoint configure.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Verifier configuration et URLs sans appeler le reseau.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""

    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run(args)
    except CirceConfigurationError as exc:
        print(INCOMPLETE_CONFIG_MESSAGE, file=sys.stderr)
        print(f"Detail : {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, CirceClientError) as exc:
        print(f"Erreur : {exc}", file=sys.stderr)
        return 1


def _require_endpoint(config: dict[str, Any], key: str) -> str:
    value = str(config.get(key, "")).strip()
    if not value:
        raise CirceConfigurationError(f"Endpoint manquant : {key}")
    return value


def _absolute_url(config: dict[str, Any], endpoint: str) -> str:
    if endpoint.startswith(("http://", "https://")):
        return endpoint
    base_url = str(config.get("base_url", "")).strip()
    if not base_url:
        raise CirceConfigurationError("base_url manquant")
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", endpoint.lstrip("/"))


def _request(
    method: str,
    url: str,
    headers: dict[str, str] | None = None,
    data: bytes | None = None,
    error_dir: Path | None = None,
) -> dict[str, Any]:
    request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = response.read()
            return {
                "url": url,
                "status": response.status,
                "headers": dict(response.headers.items()),
                "body": body,
            }
    except urllib.error.HTTPError as exc:
        body = exc.read()
        excerpt = body.decode("utf-8", errors="replace")[:500]
        saved_message = ""
        if error_dir is not None:
            error_dir.mkdir(parents=True, exist_ok=True)
            error_path = error_dir / f"http_error_{exc.code}.txt"
            error_path.write_bytes(body)
            saved_message = f" Corps sauvegarde dans {error_path}."
        raise CirceClientError(
            f"Requete Circe echouee pour {url} : HTTP {exc.code} {exc.reason}. "
            f"Extrait du corps d'erreur : {excerpt}{saved_message}"
        ) from exc
    except urllib.error.URLError as exc:
        raise CirceClientError(f"Requete Circe echouee pour {url} : {exc}") from exc


def _save_response(prefix: Path, response: dict[str, Any]) -> dict[str, Any]:
    content_type = response.get("headers", {}).get("Content-Type", "")
    raw_path = prefix.with_suffix(".bin")
    raw_path.write_bytes(response["body"])
    result: dict[str, Any] = {
        "path": str(raw_path),
        "status": response.get("status"),
        "content_type": content_type,
    }

    if "json" in content_type or _looks_like_json(response["body"]):
        json_path = prefix.with_suffix(".json")
        text = response["body"].decode("utf-8", errors="replace")
        json_path.write_text(text, encoding="utf-8")
        result["path"] = str(json_path)
        try:
            result["json"] = json.loads(text)
        except json.JSONDecodeError:
            result["text"] = text
    else:
        text_path = prefix.with_suffix(".txt")
        text = response["body"].decode("utf-8", errors="replace")
        if "\ufffd" not in text:
            text_path.write_text(text, encoding="utf-8")
            result["path"] = str(text_path)
            result["text"] = text
    return result


def _looks_like_json(body: bytes) -> bool:
    stripped = body.lstrip()
    return stripped.startswith(b"{") or stripped.startswith(b"[")


def _result_urls(config: dict[str, Any], conversion_response: dict[str, Any]) -> list[str]:
    urls: list[str] = []
    configured_download = str(config.get("download_endpoint", "")).strip()
    if configured_download:
        urls.append(_absolute_url(config, configured_download))

    payload = conversion_response.get("json")
    if isinstance(payload, dict):
        for key in ("download_url", "archive_url", "result_url", "url"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                urls.append(_absolute_url(config, value.strip()))
        files = payload.get("files")
        if isinstance(files, list):
            for item in files:
                if isinstance(item, str):
                    urls.append(_absolute_url(config, item))
                elif isinstance(item, dict) and isinstance(item.get("url"), str):
                    urls.append(_absolute_url(config, item["url"]))

    unique_urls = list(dict.fromkeys(urls))
    if not unique_urls:
        raise CirceConfigurationError("Aucun endpoint ou URL de telechargement disponible.")
    return unique_urls


def _download_filename(url: str, headers: dict[str, str], index: int) -> str:
    disposition = headers.get("Content-Disposition", "")
    if "filename=" in disposition:
        filename = disposition.split("filename=", 1)[1].strip().strip('"')
        if filename:
            return Path(filename).name
    parsed_name = Path(urllib.parse.urlparse(url).path).name
    return parsed_name or f"circe_result_{index}.bin"


if __name__ == "__main__":
    raise SystemExit(main())
