from __future__ import annotations

from pathlib import Path

from lxml import etree

from purh_site.latei_running_titles import package_latei_running_titles
from purh_site.latei_typography import RUNNING_TITLE_STOPWORDS, _short_running_title
from purh_site.reversible_integration import run_reversible_export_for_file


LONG_TITLE = (
    "Les usages politiques et spirituels de l'héraldique pontificale "
    "dans les cérémonies romaines du XVIIe siècle"
)

# Title that contains U+00A0 (non-breaking space) between a first name and Roman numeral.
# This is the canonical reproduction of the F2-audit failure case.
NBSP_TITLE = (
    "Aspects ludiques dans l’appareil h\xe9raldique des manuscrits de L\xe9on X (1513-1521)"
)

_TEI_WRAPPER = """\
<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <text>
    <group type="book">
      <group type="article" data-page-title="{title}">
        <text><body><div><p>Contenu.</p></div></body></text>
      </group>
    </group>
  </text>
</TEI>"""


def test_latei_running_titles_reuse_stable_shortening_logic(tmp_path: Path) -> None:
    short = _short_running_title(LONG_TITLE)
    last_word = short.removesuffix("â€¦").strip().split()[-1].strip(" ,;:.!?()[]{}").lower()

    assert short != LONG_TITLE
    assert len(short) <= 59
    assert last_word not in RUNNING_TITLE_STOPWORDS


def test_latei_running_titles_map_is_generated_without_touching_body(tmp_path: Path) -> None:
    xml_path = tmp_path / "running_titles.xml"
    xml_path.write_text(
        f"""<TEI xmlns="http://www.tei-c.org/ns/1.0">
  <teiHeader>
    <fileDesc>
      <titleStmt><title>Running Titles Test</title></titleStmt>
      <publicationStmt><publisher>PURH</publisher></publicationStmt>
      <sourceDesc><p>Source</p></sourceDesc>
    </fileDesc>
  </teiHeader>
  <text>
    <group type="book">
      <group type="chapter" data-page-title="{LONG_TITLE}">
        <text><body><div><p>Texte.</p></div></body></text>
      </group>
    </group>
  </text>
</TEI>""",
        encoding="utf-8",
    )
    result = run_reversible_export_for_file(xml_path, tmp_path / "out")
    body = result.latei_body_path.read_text(encoding="utf-8")
    main = result.latei_main_path.read_text(encoding="utf-8")
    macros = result.latei_macros_path.read_text(encoding="utf-8")
    running_map = result.latei_running_titles_map_path.read_text(encoding="utf-8")
    short = _short_running_title(LONG_TITLE)

    assert result.latei_running_titles_map_path.exists()
    assert result.latei_short_running_titles_count == 1
    assert LONG_TITLE in body
    assert "latei_running_titles_map" not in body
    assert rf'\input{{"{result.latei_running_titles_map_path.name}"}}' in main
    assert main.index(result.latei_running_titles_map_path.name) < main.index(result.latei_body_path.name)
    assert r"\lateiDeclareRunningTitle" in running_map
    assert short in running_map
    assert r"\lateiMarkBoth" in macros
    assert r"\latei_markboth:n" in macros
    assert r"\prop_new:N \g_latei_running_titles_map_prop" in macros


# ---------------------------------------------------------------------------
# Tests F3 — U+00A0 preservation in running-title map keys
# ---------------------------------------------------------------------------

def _make_root_with_title(title: str):
    """Return a minimal TEI lxml root with one group carrying the given page title."""
    xml = (
        '<TEI xmlns="http://www.tei-c.org/ns/1.0">'
        "<text><group type=\"book\">"
        f'<group type="article" data-page-title="{title}">'
        "<text><body><div><p>Contenu.</p></div></body></text>"
        "</group></group></text></TEI>"
    )
    return etree.fromstring(xml.encode("utf-8"))


def test_running_title_key_preserves_nbsp(tmp_path: Path) -> None:
    """Map key must contain U+00A0 (not a regular space) so that LaTeX's
    \\newunicodechar{ }{~} converts it to ~ identically in both the map and
    the body-attribute runtime lookup, making \\prop_get succeed."""
    root = _make_root_with_title(NBSP_TITLE)
    map_path = tmp_path / "running_titles_map.tex"
    pkg = package_latei_running_titles(root, map_path)

    assert pkg.shortened_count == 1
    running_map = map_path.read_text(encoding="utf-8")

    assert "L\xe9on\xa0X" in running_map, "NBSP must be preserved in map key"
    assert "L\xe9on X" not in running_map, "Regular space must not replace NBSP in key"


def test_running_title_short_value_still_generated_for_nbsp_title(tmp_path: Path) -> None:
    """The short (truncated) value produced for an NBSP title must still be correct."""
    root = _make_root_with_title(NBSP_TITLE)
    map_path = tmp_path / "running_titles_map.tex"
    package_latei_running_titles(root, map_path)

    expected_short = _short_running_title(NBSP_TITLE)
    assert expected_short != NBSP_TITLE

    running_map = map_path.read_text(encoding="utf-8")
    assert expected_short in running_map


def test_running_title_without_nbsp_unchanged(tmp_path: Path) -> None:
    """A long title with only regular spaces must still produce a map entry
    with the correct key (no NBSP introduced, regular spaces preserved)."""
    root = _make_root_with_title(LONG_TITLE)
    map_path = tmp_path / "running_titles_map.tex"
    pkg = package_latei_running_titles(root, map_path)

    assert pkg.shortened_count == 1
    running_map = map_path.read_text(encoding="utf-8")

    assert "\xa0" not in running_map
    assert LONG_TITLE in running_map
    expected_short = _short_running_title(LONG_TITLE)
    assert expected_short in running_map
