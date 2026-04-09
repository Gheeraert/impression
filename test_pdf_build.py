from __future__ import annotations

"""Script minimal pour tester la chaîne PDF d'Impressions.

Usage :
    python test_pdf_build.py chemin/vers/book.normalized.xml chemin/vers/sortie_pdf

Exemple :
    python test_pdf_build.py \
        C:/mes_livres/heraldique/book.normalized.xml \
        C:/mes_livres/heraldique/test_pdf

Options utiles :
    python test_pdf_build.py XML SORTIE --no-compile
    python test_pdf_build.py XML SORTIE --engine lualatex
"""

import argparse
import sys
from pathlib import Path

from purh_site.pdf_builder import PdfBuilder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Teste la génération PDF à partir d'un XML TEI normalisé."
    )
    parser.add_argument(
        "xml",
        type=Path,
        help="Chemin vers le fichier book.normalized.xml",
    )
    parser.add_argument(
        "output_dir",
        type=Path,
        help="Dossier de sortie pour le .tex, le .pdf et les logs",
    )
    parser.add_argument(
        "--engine",
        default="lualatex",
        help="Moteur LaTeX à utiliser (par défaut : lualatex)",
    )
    parser.add_argument(
        "--no-compile",
        action="store_true",
        help="Génère seulement le fichier LaTeX sans compiler le PDF",
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=2,
        help="Nombre de passes LaTeX (par défaut : 2)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout par passe de compilation, en secondes (par défaut : 120)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    xml_path: Path = args.xml.resolve()
    output_dir: Path = args.output_dir.resolve()

    if not xml_path.exists():
        print(f"[ERREUR] Fichier XML introuvable : {xml_path}")
        return 1

    builder = PdfBuilder(
        latex_engine=args.engine,
        compile_pdf=not args.no_compile,
        latex_runs=args.runs,
        timeout_seconds=args.timeout,
    )

    print("=== Build PDF Impressions ===")
    print(f"XML     : {xml_path}")
    print(f"Sortie  : {output_dir}")
    print(f"Moteur  : {args.engine}")
    print(f"Compile : {'non' if args.no_compile else 'oui'}")
    print()

    result = builder.build_from_normalized_tei(xml_path, output_dir)

    print("=== Résultat ===")
    print(f"Succès        : {'oui' if result.success else 'non'}")
    print(f"LaTeX         : {result.tex_path}")
    print(f"PDF           : {result.pdf_path}")
    print(f"Log           : {result.log_path}")
    print(f"Rapport       : {result.report_path}")
    print()
    print("=== Statistiques ===")
    print(f"Divisions     : {result.stats.divisions}")
    print(f"Sections      : {result.stats.sections}")
    print(f"Figures       : {result.stats.figures}")
    print(f"Notes         : {result.stats.notes}")

    if result.warnings:
        print()
        print("=== Avertissements ===")
        for warning in result.warnings:
            print(f"- {warning}")

    if result.error_message:
        print()
        print("=== Erreur ===")
        print(result.error_message)

    return 0 if result.success else 2


if __name__ == "__main__":
    sys.exit(main())
