from __future__ import annotations

from pathlib import Path

from purh_site.latex_renderer import RUNNING_TITLE_STOPWORDS, _short_running_title
from purh_site.reversible_integration import run_reversible_export_for_file


LONG_TITLE = (
    "Les usages politiques et spirituels de l'héraldique pontificale "
    "dans les cérémonies romaines du XVIIe siècle"
)


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
