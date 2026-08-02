from __future__ import annotations

import json
import tkinter as tk
import traceback
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .config import BuildConfig
from .local_server import PreviewServer
from .reversible_integration import (
    restore_xml_from_latei_body,
    restore_xml_from_latei_monofile,
    run_reversible_export_for_file,
)
from .site_builder import SiteBuilder, has_editor_pdf

LATEI_PACKAGE_HELP = (
    "Le paquet LaTEI contient le corps réversible, le driver compilable, "
    "les macros locales, le mapping d’images, les assets copiés, le PDF éventuel, "
    "le XML restauré et les diagnostics."
)

LATEI_USAGE_HELP = """Le paquet LaTEI contient plusieurs fichiers.

Fichier éditorial principal :
*.latei.tex

C’est le monofichier LaTEI complet. L’éditrice corrige uniquement la zone lateiDocument,
le compile avec LuaLaTeX et le transmet pour restaurer le XML Métopes.

À corriger :
*.latei.tex (zone lateiDocument uniquement)

À compiler :
*.latei.tex (avec LuaLaTeX)

À restaurer en XML :
*.latei.tex

Fragments techniques (debug) — à ne pas corriger directement :
*.latei_body.tex     — corps réversible pur (le fichier *.latei_body.tex ne compile pas seul)
*.latei_main.tex     — ancien driver de compilation fragmenté
*.latei_macros.tex   — macros locales
*.latei_graphics_map.tex — mappings d’images
latei_assets/        — images copiées

Pour restaurer un XML Métopes après corrections :
Outils → Restaurer un XML Métopes depuis un monofichier LaTEI…

Ancien format fragmenté (debug/legacy) :
Outils → Restaurer un XML Métopes depuis un corps LaTEI…"""

ASSETS_STRUCTURE_HELP = """Structure attendue du dossier assets

Le dossier assets doit contenir les fichiers appelés par le XML : images, figures, fac-similés ou autres documents liés.

Les chemins doivent correspondre exactement aux chemins indiqués dans le XML.

Exemple :
si le XML contient :

  <graphic url="images/figure-01.jpg"/>

alors le dossier assets doit contenir :

  images/
    figure-01.jpg

Si le XML contient :

  <graphic url="figures/chapitre-2/schema.png"/>

alors le dossier assets doit contenir :

  figures/
    chapitre-2/
      schema.png

En pratique, le dossier assets peut par exemple avoir cette structure :

  assets/
    images/
      figure-01.jpg
      figure-02.jpg
    figures/
      chapitre-1/
        carte-01.png
    documents/
      annexe.pdf

Il est conseillé d’éviter les noms de fichiers trop complexes : préférer des noms courts, sans espaces, sans accents, et stables."""

EDITORIAL_USAGE_HELP = """Mode d’emploi éditorial

1. Choisir le fichier XML maître

Sélectionnez le fichier XML principal du livre. Dans la plupart des cas, il s’agit du fichier complet ou normalisé fourni à partir de Métopes.

2. Ajouter des fichiers XML indépendants si nécessaire

Ce champ sert uniquement lorsque le livre est constitué de plusieurs fichiers XML séparés. Si vous disposez d’un seul fichier XML complet, laissez cette zone vide.

3. Choisir le dossier assets

Le dossier assets contient les images et les fichiers appelés par le XML.

Il doit conserver la même organisation que les chemins indiqués dans le XML.

Exemple :
si le XML appelle images/figure-01.jpg, le dossier assets doit contenir un sous-dossier images avec le fichier figure-01.jpg.

Structure possible :

  assets/
    images/
      figure-01.jpg
      figure-02.jpg
    figures/
      chapitre-1/
        carte-01.png
    documents/
      annexe.pdf

4. Ajouter une quatrième de couverture si nécessaire

Si le XML contient déjà une quatrième de couverture, elle sera utilisée en priorité. Le fichier externe ne sert que de repli.

Formats acceptés : .md, .markdown, .html, .txt.

5. Compléter les informations de collection

Les champs collection, numéro et ISSN ne sont utilisés que si ces informations ne sont pas déjà présentes dans le XML.

6. Choisir l’export LaTEI / PDF

Aucun export PDF/LaTeX : construit seulement le site web.
LaTEI monofichier (.tex) : produit le fichier de composition du livre.
LaTEI monofichier + PDF : produit le fichier de composition et tente de compiler le PDF.

7. Construire le site

Choisissez le dossier de sortie, puis cliquez sur « Construire le site ».
Le site généré peut ensuite être prévisualisé dans le navigateur.

Les informations déjà présentes dans le XML sont toujours prioritaires.
Les champs optionnels ne servent qu’à compléter ou remplacer une information manquante."""


class App(ttk.Frame):
    """Interface graphique pour lancer les builds TEI -> site multi-pages."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master = master
        self.builder = SiteBuilder()
        self.master_xml_var = tk.StringVar()
        self.assets_dir_var = tk.StringVar()
        self.back_cover_var = tk.StringVar()
        self.collection_title_var = tk.StringVar()
        self.collection_number_var = tk.StringVar()
        self.collection_issn_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.pdf_export_mode_var = tk.StringVar(value="none")
        self.pdf_export_status_var = tk.StringVar(value="")
        self.pdf_export_widgets: list[ttk.Radiobutton] = []
        self.build_button: ttk.Button | None = None
        self.xml_files: list[Path] = []
        self.port_var = tk.StringVar(value="8000,8080")
        self.auto_preview_var = tk.BooleanVar(value=True)
        self.preview_server: PreviewServer | None = None
        self.current_config_path: Path | None = None
        self._build_ui()
        self.master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_ui(self) -> None:
        self.master.title("IMPRESSIONS — livre web TEI")
        self.master.geometry("1080x780")
        self._build_menu()
        self.pack(fill="both", expand=True)

        title = ttk.Label(
            self,
            text="IMPRESSIONS — génération d’un livre web à partir de TEI Métopes",
            font=("TkDefaultFont", 12, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))

        self._add_path_selector(1, "Fichier XML maître", self.master_xml_var, self._choose_master_xml, "Choisir…")
        ttk.Label(
            self,
            text="Choisir le fichier XML principal du livre. Dans le cas le plus courant, c’est le fichier complet ou normalisé du livre.",
            foreground="gray",
        ).grid(row=2, column=1, columnspan=2, sticky="w", pady=(0, 6))

        files_label = ttk.Label(self, text="Fichiers XML indépendants (optionnel)")
        files_label.grid(row=3, column=0, sticky="nw", pady=(0, 6))
        self.files_list = tk.Listbox(self, height=6)
        self.files_list.grid(row=3, column=1, sticky="nsew", pady=(0, 6))
        files_buttons = ttk.Frame(self)
        files_buttons.grid(row=3, column=2, sticky="n")
        ttk.Button(files_buttons, text="Ajouter…", command=self._choose_xml_files).grid(row=0, column=0, sticky="ew")
        ttk.Button(files_buttons, text="Vider", command=self._clear_xml_files).grid(row=1, column=0, sticky="ew", pady=(6, 0))
        ttk.Label(
            self,
            text="À utiliser seulement si le livre est fourni en plusieurs fichiers XML séparés. Sinon, laisser vide.",
            foreground="gray",
        ).grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 6))

        self._add_path_selector(5, "Dossier assets", self.assets_dir_var, self._choose_assets_dir, "Choisir…")
        ttk.Label(
            self,
            text="Choisir le dossier qui contient les images et fichiers liés au livre. Il sera copié dans le site de sortie sous le nom assets.",
            foreground="gray",
        ).grid(row=6, column=1, sticky="w", pady=(0, 6))
        ttk.Button(
            self,
            text="Structure attendue du dossier assets…",
            command=self._show_assets_structure_help,
        ).grid(row=6, column=2, sticky="ew", pady=(0, 6))

        self._add_path_selector(7, "Quatrième de couverture (optionnel)", self.back_cover_var, self._choose_back_cover, "Choisir…")
        ttk.Label(
            self,
            text="Si le XML contient déjà une quatrième de couverture, elle sera utilisée en priorité. Ce champ sert seulement à fournir un fichier de repli.\nFormats acceptés : .md, .markdown, .html, .txt.",
            foreground="gray",
        ).grid(row=8, column=1, columnspan=2, sticky="w", pady=(0, 6))

        self._add_entry_row(9, "Nom de la collection (optionnel)", self.collection_title_var)
        self._add_entry_row(10, "Numéro dans la collection (optionnel)", self.collection_number_var)
        self._add_entry_row(11, "ISSN de la collection (optionnel)", self.collection_issn_var)
        ttk.Label(
            self,
            text="Ces champs ne sont utilisés que si l’information n’est pas déjà présente dans le XML.",
            foreground="gray",
        ).grid(row=12, column=1, columnspan=2, sticky="w", pady=(0, 6))

        self._add_path_selector(13, "Dossier de sortie", self.output_dir_var, self._choose_output_dir, "Choisir…")

        self._add_pdf_export_controls(14)
        ttk.Label(
            self,
            text="LaTEI est le fichier de composition du livre. Il peut être relu, corrigé et compilé en PDF.",
            foreground="gray",
        ).grid(row=15, column=1, columnspan=2, sticky="w", pady=(0, 6))

        preview_bar = ttk.Frame(self)
        preview_bar.grid(row=16, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(preview_bar, text="Ports de prévisualisation").grid(row=0, column=0, sticky="w")
        ttk.Entry(preview_bar, textvariable=self.port_var, width=18).grid(row=0, column=1, sticky="w", padx=(8, 16))
        ttk.Checkbutton(preview_bar, text="Lancer le serveur local et ouvrir le navigateur après build", variable=self.auto_preview_var).grid(row=0, column=2, sticky="w")

        button_bar = ttk.Frame(self)
        button_bar.grid(row=17, column=0, columnspan=3, sticky="w", pady=(8, 12))
        ttk.Button(button_bar, text="Charger config…", command=self._load_config).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Enregistrer config…", command=self._save_config).grid(row=0, column=1, padx=(0, 8))
        self.build_button = ttk.Button(button_bar, text="Construire le site", command=self._build)
        self.build_button.grid(row=0, column=2, padx=(0, 8))
        ttk.Button(button_bar, text="Relancer la prévisualisation", command=self._preview_existing_site).grid(row=0, column=3, padx=(0, 8))
        ttk.Button(button_bar, text="Ouvrir le dossier de sortie", command=self._open_output_dir).grid(row=0, column=4, padx=(0, 8))
        ttk.Button(button_bar, text="Effacer le journal", command=self._clear_log).grid(row=0, column=5)

        log_label = ttk.Label(self, text="Journal")
        log_label.grid(row=18, column=0, sticky="w")
        self.log = tk.Text(self, wrap="word", height=24)
        self.log.grid(row=19, column=0, columnspan=3, sticky="nsew")
        self.log.configure(state="disabled")

        self.columnconfigure(1, weight=1)
        self.rowconfigure(19, weight=1)
        self._refresh_pdf_export_controls()
        self._log("Interface prête.")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(
            label="Exporter un paquet LaTEI depuis un XML…",
            command=self._run_reversible_export,
        )
        tools_menu.add_command(
            label="Restaurer un XML Métopes depuis un monofichier LaTEI…",
            command=self._restore_xml_from_latei_monofile,
        )
        tools_menu.add_command(
            label="Restaurer un XML Métopes depuis un corps LaTEI…",
            command=self._restore_xml_from_latei_body,
        )
        menubar.add_cascade(label="Outils", menu=tools_menu)
        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(
            label="Mode d’emploi éditorial…",
            command=self._show_editorial_usage_help,
        )
        menubar.add_cascade(label="Aide", menu=help_menu)
        self.master.config(menu=menubar)

    def _add_path_selector(self, row: int, label: str, variable: tk.StringVar, browse_command, button_text: str) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(0, 6))
        ttk.Button(self, text=button_text, command=browse_command).grid(row=row, column=2, sticky="ew", pady=(0, 6))

    def _add_entry_row(self, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(0, 6))

    def _add_pdf_export_controls(self, row: int) -> None:
        ttk.Label(self, text="Export LaTEI / PDF PURH").grid(row=row, column=0, sticky="nw", pady=(0, 6))
        frame = ttk.Frame(self)
        frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(0, 6))

        options = [
            ("Aucun export PDF/LaTeX", "none"),
            ("LaTEI monofichier (.tex)", "latei"),
            ("LaTEI monofichier + PDF", "latei_pdf"),
        ]
        for i, (label, value) in enumerate(options):
            radio = ttk.Radiobutton(frame, text=label, variable=self.pdf_export_mode_var, value=value)
            radio.grid(row=i, column=0, sticky="w", padx=(12, 0))
            self.pdf_export_widgets.append(radio)

        ttk.Label(frame, textvariable=self.pdf_export_status_var).grid(row=len(options), column=0, sticky="w", pady=(4, 0))

    def _choose_master_xml(self) -> None:
        path = filedialog.askopenfilename(title="Choisir un fichier XML maître", filetypes=[("Fichiers XML", "*.xml")])
        if path:
            self.master_xml_var.set(path)
            self._log(f"Fichier maître : {path}")

    def _run_reversible_export(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir un fichier XML TEI à exporter en LaTEI",
            filetypes=[("Fichiers XML", "*.xml"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return

        output = filedialog.askdirectory(
            title="Choisir le dossier de sortie expérimental (annuler = dossier du XML)"
        )
        output_dir = Path(output) if output else None

        try:
            result = run_reversible_export_for_file(Path(path), output_dir)
        except Exception as exc:
            self._log(f"Erreur export LaTEI réversible : {exc}")
            self._log(traceback.format_exc())
            messagebox.showerror("Export LaTEI réversible", str(exc))
            return

        missing_artifacts = missing_latei_package_artifacts(result)
        details = format_latei_export_summary(result, missing_artifacts=missing_artifacts)
        for line in details.splitlines():
            self._log(line)

        if result.success and not missing_artifacts:
            messagebox.showinfo("Export LaTEI réversible", details)
        else:
            messagebox.showwarning("Export LaTEI réversible", details)

    def _restore_xml_from_latei_body(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir un corps LaTEI réversible",
            filetypes=[
                ("Corps LaTEI", "*.latei_body.tex"),
                ("Fichiers TeX", "*.tex"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return

        body_path = Path(path)
        default_output = body_path.with_name(f"{latei_body_restored_stem(body_path)}.restored.xml")
        output = filedialog.asksaveasfilename(
            title="Écrire l’XML Métopes restauré",
            defaultextension=".xml",
            filetypes=[("Fichiers XML", "*.xml"), ("Tous les fichiers", "*.*")],
            initialdir=str(default_output.parent),
            initialfile=default_output.name,
        )
        if not output:
            return

        try:
            restored_path = restore_xml_from_latei_body(body_path, Path(output))
        except Exception as exc:
            self._log(f"Erreur restauration XML depuis LaTEI : {exc}")
            self._log(traceback.format_exc())
            messagebox.showerror("Restauration XML depuis LaTEI", str(exc))
            return

        details = (
            "Restauration XML depuis LaTEI terminée.\n"
            f"Corps LaTEI : {body_path}\n"
            f"XML restauré : {restored_path}"
        )
        for line in details.splitlines():
            self._log(line)
        messagebox.showinfo("Restauration XML depuis LaTEI", details)

    def _restore_xml_from_latei_monofile(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir un monofichier LaTEI",
            filetypes=[
                ("Monofichier LaTEI", "*.latei.tex"),
                ("Fichiers TeX", "*.tex"),
                ("Tous les fichiers", "*.*"),
            ],
        )
        if not path:
            return

        mono_path = Path(path)
        default_output = mono_path.with_name(f"{latei_monofile_restored_stem(mono_path)}.restored.xml")
        output = filedialog.asksaveasfilename(
            title="Écrire l’XML Métopes restauré",
            defaultextension=".xml",
            filetypes=[("Fichiers XML", "*.xml"), ("Tous les fichiers", "*.*")],
            initialdir=str(default_output.parent),
            initialfile=default_output.name,
        )
        if not output:
            return

        try:
            restored_path = restore_xml_from_latei_monofile(mono_path, Path(output))
        except Exception as exc:
            self._log(f"Erreur restauration XML depuis monofichier LaTEI : {exc}")
            self._log(traceback.format_exc())
            messagebox.showerror("Restauration XML depuis monofichier LaTEI", str(exc))
            return

        details = (
            "XML Métopes restauré depuis le monofichier LaTEI.\n"
            f"Monofichier LaTEI : {mono_path}\n"
            f"XML restauré : {restored_path}"
        )
        for line in details.splitlines():
            self._log(line)
        messagebox.showinfo("Restauration XML depuis monofichier LaTEI", details)

    def _show_latei_usage_help(self) -> None:
        messagebox.showinfo("Mode d’emploi LaTEI", LATEI_USAGE_HELP)

    def _show_editorial_usage_help(self) -> None:
        messagebox.showinfo("Mode d’emploi éditorial", EDITORIAL_USAGE_HELP)

    def _show_assets_structure_help(self) -> None:
        messagebox.showinfo("Structure attendue du dossier assets", ASSETS_STRUCTURE_HELP)

    def _choose_xml_files(self) -> None:
        paths = filedialog.askopenfilenames(title="Choisir un ou plusieurs fichiers XML", filetypes=[("Fichiers XML", "*.xml")])
        if not paths:
            return
        for item in paths:
            path = Path(item)
            if path not in self.xml_files:
                self.xml_files.append(path)
                self.files_list.insert("end", str(path))
        self._log(f"{len(paths)} fichier(s) XML ajouté(s).")

    def _clear_xml_files(self) -> None:
        self.xml_files.clear()
        self.files_list.delete(0, "end")
        self._log("Liste des fichiers XML vidée.")

    def _choose_assets_dir(self) -> None:
        path = filedialog.askdirectory(title="Choisir un dossier assets")
        if path:
            self.assets_dir_var.set(path)
            self._refresh_pdf_export_controls()
            self._log(f"Dossier assets : {path}")

    def _choose_back_cover(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir une quatrième de couverture",
            filetypes=[
                ("Fichiers Markdown/HTML/Texte", "*.md *.markdown *.html *.htm *.txt"),
                ("Markdown", "*.md *.markdown"),
                ("HTML", "*.html *.htm"),
                ("Texte", "*.txt"),
            ],
        )
        if path:
            self.back_cover_var.set(path)
            self._log(f"Quatrième de couverture : {path}")

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choisir un dossier de sortie")
        if path:
            self.output_dir_var.set(path)
            self._log(f"Dossier de sortie : {path}")

    def _config_as_dict(self) -> dict[str, object]:
        """Retourne l'état courant de l'interface sous forme sérialisable en JSON."""
        return {
            "version": 1,
            "master_xml": self.master_xml_var.get().strip(),
            "xml_files": [str(path) for path in self.xml_files],
            "assets_dir": self.assets_dir_var.get().strip(),
            "back_cover": self.back_cover_var.get().strip(),
            "collection_title": self.collection_title_var.get().strip(),
            "collection_number": self.collection_number_var.get().strip(),
            "collection_issn": self.collection_issn_var.get().strip(),
            "output_dir": self.output_dir_var.get().strip(),
            "preview_ports": self.port_var.get().strip(),
            "auto_preview": bool(self.auto_preview_var.get()),
            "pdf_export_mode": self.pdf_export_mode_var.get(),
        }

    def _apply_config(self, data: dict[str, object]) -> None:
        """Applique une configuration JSON à l'interface."""

        def as_text(key: str) -> str:
            value = data.get(key, "")
            return "" if value is None else str(value)

        self.master_xml_var.set(as_text("master_xml"))
        self.assets_dir_var.set(as_text("assets_dir"))
        self.back_cover_var.set(as_text("back_cover"))
        self.collection_title_var.set(as_text("collection_title"))
        self.collection_number_var.set(as_text("collection_number"))
        self.collection_issn_var.set(as_text("collection_issn"))
        self.output_dir_var.set(as_text("output_dir"))
        self.port_var.set(as_text("preview_ports") or "8000,8080")
        self.pdf_export_mode_var.set(as_text("pdf_export_mode") or "none")

        raw_auto_preview = data.get("auto_preview", True)
        if isinstance(raw_auto_preview, str):
            self.auto_preview_var.set(raw_auto_preview.strip().lower() not in {"0", "false", "non", "no"})
        else:
            self.auto_preview_var.set(bool(raw_auto_preview))

        raw_xml_files = data.get("xml_files", [])
        self.xml_files.clear()
        self.files_list.delete(0, "end")

        if isinstance(raw_xml_files, list):
            for item in raw_xml_files:
                if item is None:
                    continue
                path = Path(str(item))
                self.xml_files.append(path)
                self.files_list.insert("end", str(path))
        self._refresh_pdf_export_controls()

    def _save_config(self) -> None:
        """Enregistre l'état courant de l'interface dans un fichier JSON."""
        initial_dir = self.output_dir_var.get().strip() or None
        path = filedialog.asksaveasfilename(
            title="Enregistrer la configuration",
            defaultextension=".json",
            filetypes=[("Configuration JSON", "*.json"), ("Tous les fichiers", "*.*")],
            initialdir=initial_dir,
            initialfile="impressions_config.json",
        )
        if not path:
            return

        config_path = Path(path)
        try:
            config_path.write_text(
                json.dumps(self._config_as_dict(), ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except Exception as exc:
            self._log(f"Erreur lors de l'enregistrement de la configuration : {exc}")
            messagebox.showerror("Configuration", f"Impossible d'enregistrer la configuration :\n{exc}")
            return

        self.current_config_path = config_path
        self._log(f"Configuration enregistrée : {config_path}")

    def _load_config(self) -> None:
        """Charge une configuration JSON et remplit l'interface."""
        path = filedialog.askopenfilename(
            title="Charger une configuration",
            filetypes=[("Configuration JSON", "*.json"), ("Tous les fichiers", "*.*")],
        )
        if not path:
            return

        config_path = Path(path)
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            if not isinstance(data, dict):
                raise ValueError("Le fichier JSON ne contient pas un objet de configuration.")
            self._apply_config(data)
        except Exception as exc:
            self._log(f"Erreur lors du chargement de la configuration : {exc}")
            messagebox.showerror("Configuration", f"Impossible de charger la configuration :\n{exc}")
            return

        self.current_config_path = config_path
        self._log(f"Configuration chargée : {config_path}")

    def _make_build_config(self, output_dir: Path, assets_dir: Path | None) -> BuildConfig:
        back_cover = Path(self.back_cover_var.get()).resolve() if self.back_cover_var.get().strip() else None
        pdf_export_mode = "none" if has_editor_pdf(assets_dir) else self.pdf_export_mode_var.get()
        return BuildConfig(
            output_dir=output_dir,
            assets_dir=assets_dir,
            back_cover_path=back_cover,
            collection_title=self.collection_title_var.get().strip(),
            collection_number=self.collection_number_var.get().strip(),
            collection_issn=self.collection_issn_var.get().strip(),
            pdf_export_mode=pdf_export_mode,
        )

    def _refresh_pdf_export_controls(self) -> None:
        assets_dir = Path(self.assets_dir_var.get()).resolve() if self.assets_dir_var.get().strip() else None
        editor_pdf_found = has_editor_pdf(assets_dir)
        state = "disabled" if editor_pdf_found else "normal"
        if editor_pdf_found:
            self.pdf_export_mode_var.set("none")
            self.pdf_export_status_var.set("PDF éditeur détecté : l’export LaTEI/PDF est désactivé.")
        else:
            self.pdf_export_status_var.set("")
        for widget in self.pdf_export_widgets:
            widget.configure(state=state)

    def _build(self) -> None:
        output_dir_text = self.output_dir_var.get().strip()
        if not output_dir_text:
            messagebox.showwarning("Sortie manquante", "Veuillez choisir un dossier de sortie.")
            return

        self._refresh_pdf_export_controls()
        wait_dialog = self._show_build_wait_dialog()
        self.master.after(100, lambda: self._run_build_after_dialog_is_drawn(wait_dialog))

    def _run_build_after_dialog_is_drawn(self, wait_dialog: tk.Toplevel) -> None:
        output_dir_text = self.output_dir_var.get().strip()
        output_dir = Path(output_dir_text)
        assets_dir = Path(self.assets_dir_var.get()).resolve() if self.assets_dir_var.get().strip() else None
        master_xml_text = self.master_xml_var.get().strip()

        try:
            if master_xml_text:
                master_xml = Path(master_xml_text).resolve()
                self._log("Build multi-pages à partir du fichier maître…")
                result = self.builder.build_from_master(
                    master_xml,
                    self._make_build_config(output_dir=output_dir, assets_dir=assets_dir),
                )
                self._log(f"Site généré : {result.html_path}")
                self._log(f"Rapport : {result.report_path}")
                if self.auto_preview_var.get():
                    self._preview_result(result)
                return

            if self.xml_files:
                self._log("Build de plusieurs fichiers XML indépendants…")
                config = self._make_build_config(output_dir=output_dir, assets_dir=assets_dir)
                results = self.builder.build_from_many(
                    self.xml_files,
                    output_dir,
                    assets_dir=assets_dir,
                    config_overrides=config,
                )
                self._log(f"{len(results)} site(s) généré(s).")
                if results and self.auto_preview_var.get():
                    self._preview_result(results[0])
                return

            messagebox.showwarning("Aucun XML", "Choisissez un fichier maître XML ou un ensemble de fichiers XML.")
        except Exception as exc:
            self._log(f"Erreur : {exc}")
            self._log(traceback.format_exc())
            log_path = self._write_build_error_log(output_dir, exc)
            messagebox.showerror(
                "Erreur pendant le build",
                _truncate_for_dialog(str(exc), log_path),
            )
        finally:
            self._close_build_wait_dialog(wait_dialog)

    def _write_build_error_log(self, output_dir: Path, exc: Exception) -> Path | None:
        """Conserve le détail complet de l'erreur sur disque.

        Le journal affiché dans l'interface disparaît si la fenêtre se ferme ;
        et un message d'erreur trop long (des dizaines de milliers de
        caractères pour un livre à nombreux chapitres, par ex. des xml:id
        dupliqués partout) reste peu lisible dans une boîte de dialogue. Le
        détail complet va donc toujours ici, à un emplacement stable que
        l'utilisatrice peut retrouver même si la boîte de dialogue a été
        fermée trop vite ou n'a pas semblé s'afficher correctement.
        """
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            log_path = output_dir / "build_error.log"
            log_path.write_text(f"{exc}\n\n{traceback.format_exc()}", encoding="utf-8")
            return log_path
        except Exception:
            return None

    def _show_build_wait_dialog(self) -> tk.Toplevel:
        if self.build_button is not None:
            self.build_button.configure(state="disabled")

        dialog = tk.Toplevel(self.master)
        dialog.title("Génération en cours")
        dialog.resizable(False, False)
        dialog.transient(self.master)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)

        frame = ttk.Frame(dialog, padding=18)
        frame.grid(row=0, column=0, sticky="nsew")
        ttk.Label(
            frame,
            text="Génération du site en cours…",
            font=("TkDefaultFont", 10, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            frame,
            text="Tout va bien : IMPRESSIONS travaille.",
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))
        ttk.Label(
            frame,
            text="Merci de patienter jusqu'à l'ouverture du rapport de génération.",
        ).grid(row=2, column=0, sticky="w", pady=(0, 12))
        progress = ttk.Progressbar(frame, mode="indeterminate", length=280)
        progress.grid(row=3, column=0, sticky="ew")
        progress.start(12)

        dialog.update_idletasks()
        dialog.update()
        x = self.master.winfo_rootx() + max((self.master.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = self.master.winfo_rooty() + max((self.master.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry(f"+{x}+{y}")
        dialog.lift(self.master)
        self.update_idletasks()
        self.update()
        return dialog

    def _close_build_wait_dialog(self, dialog: tk.Toplevel | None) -> None:
        if dialog is not None:
            try:
                for child in dialog.winfo_children():
                    for grandchild in child.winfo_children():
                        if isinstance(grandchild, ttk.Progressbar):
                            grandchild.stop()
                dialog.destroy()
            except tk.TclError:
                pass
        if self.build_button is not None:
            self.build_button.configure(state="normal")

    def _preview_result(self, result) -> None:
        ports = self._parse_ports()
        self._start_preview_server(result.output_dir, result.html_path.name, ports)

    def _preview_existing_site(self) -> None:
        output_dir_text = self.output_dir_var.get().strip()
        if not output_dir_text:
            messagebox.showinfo("Prévisualisation", "Choisissez d'abord un dossier de sortie.")
            return
        output_dir = Path(output_dir_text)
        index_path = output_dir / "index.html"
        if not index_path.exists():
            messagebox.showinfo("Prévisualisation", "Aucun index.html n'a été trouvé dans le dossier de sortie.")
            return
        self._start_preview_server(output_dir, "index.html", self._parse_ports())

    def _parse_ports(self) -> tuple[int, ...]:
        raw = self.port_var.get().strip()
        if not raw:
            return (8000, 8080)
        ports: list[int] = []
        for item in raw.split(','):
            item = item.strip()
            if not item:
                continue
            try:
                port = int(item)
            except ValueError as exc:
                raise ValueError(f"Port invalide : {item}") from exc
            if port <= 0 or port > 65535:
                raise ValueError(f"Port hors limite : {port}")
            ports.append(port)
        if not ports:
            return (8000, 8080)
        return tuple(ports)

    def _start_preview_server(self, directory: Path, relative_path: str, ports: tuple[int, ...]) -> None:
        if self.preview_server is not None:
            self.preview_server.stop()
        self.preview_server = PreviewServer(directory=directory, preferred_ports=ports)
        self.preview_server.start()
        url = self.preview_server.open_in_browser(relative_path)
        self._log(f"Serveur local : {url}")

    def _on_close(self) -> None:
        if self.preview_server is not None:
            self.preview_server.stop()
        self.master.destroy()

    def _open_output_dir(self) -> None:
        value = self.output_dir_var.get().strip()
        if not value:
            messagebox.showinfo("Dossier de sortie", "Aucun dossier de sortie n'est défini.")
            return
        path = Path(value)
        if path.exists():
            try:
                import os
                os.startfile(path)  # type: ignore[attr-defined]
            except Exception:
                self._log(f"Ouvrez manuellement le dossier : {path}")

    def _clear_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")


_MAX_DIALOG_MESSAGE_LENGTH = 2000


def _truncate_for_dialog(message: str, log_path: Path | None) -> str:
    """Cap an error message for display in a modal dialog.

    A message with no practical bound (e.g. a duplicate-xml:id report across
    a many-chapter book) is not something a dialog box should ever have to
    render whole — the full text is always in build_error.log regardless."""
    if len(message) <= _MAX_DIALOG_MESSAGE_LENGTH:
        pointer = f"\n\nDétail complet : {log_path}" if log_path is not None else ""
        return message + pointer
    truncated = message[:_MAX_DIALOG_MESSAGE_LENGTH]
    pointer = f"\n\n… (message tronqué). Détail complet : {log_path}" if log_path is not None else "\n\n… (message tronqué)."
    return truncated + pointer


def expected_latei_package_artifacts(result) -> list[Path]:
    """Return the expected compilation/documentation artifacts for a LaTEI export."""
    primary_latei = getattr(result, "primary_latei_path", None) or getattr(result, "latei_monofile_path", None)
    manifest = getattr(result, "manifest_path", None)
    artifacts: list[Path] = []
    if primary_latei is not None:
        artifacts.append(primary_latei)
    artifacts.extend([
        result.latei_body_path,
        result.latei_main_path,
        result.latei_macros_path,
        result.latei_graphics_map_path,
        result.latei_running_titles_map_path,
        result.latei_assets_dir,
        result.roundtrip_xml_path,
        result.diagnostics_path,
    ])
    if manifest is not None:
        artifacts.append(manifest)
    if result.latei_log_path is not None:
        artifacts.append(result.latei_log_path)
    if result.latei_pdf_success:
        artifacts.append(result.latei_pdf_path)
    return artifacts


def missing_latei_package_artifacts(result) -> list[Path]:
    """Return expected LaTEI package paths that are not present on disk."""
    return [path for path in expected_latei_package_artifacts(result) if not Path(path).exists()]


def format_latei_export_summary(result, *, missing_artifacts: list[Path] | None = None) -> str:
    """Build the concise GUI/CLI-facing summary for a LaTEI export."""
    missing = missing_latei_package_artifacts(result) if missing_artifacts is None else missing_artifacts

    primary_latei = getattr(result, "primary_latei_path", None) or getattr(result, "latei_monofile_path", None)
    primary_pdf = getattr(result, "primary_pdf_path", None) or getattr(result, "latei_monofile_pdf_path", None)
    manifest = getattr(result, "manifest_path", None)
    monofile_pdf_success = getattr(result, "latei_monofile_pdf_success", False)
    monofile_pdf_message = getattr(result, "latei_monofile_pdf_message", "non produit")

    pdf_debug_status = (
        str(result.latei_pdf_path) if result.latei_pdf_success
        else f"non produit ({result.latei_pdf_message})"
    )

    lines = ["Export LaTEI terminé.", ""]

    if primary_latei is not None:
        lines.extend([
            f"À corriger : {primary_latei}",
            f"À compiler : {primary_latei}",
            f"À restaurer en XML : {primary_latei}",
            f"Fichier LaTEI éditable : {primary_latei}",
        ])
    if primary_pdf is not None:
        mono_pdf_status = (
            str(primary_pdf) if monofile_pdf_success
            else f"non produit ({monofile_pdf_message})"
        )
        lines.append(f"PDF principal : {mono_pdf_status}")
    if manifest is not None:
        lines.append(f"Manifeste : {manifest}")

    lines.extend([
        "",
        "Fragments debug :",
        f"Corps réversible à corriger : {result.latei_body_path}",
        f"Driver compilable : {result.latei_main_path}",
        f"Macros locales : {result.latei_macros_path}",
        f"Mapping images : {result.latei_graphics_map_path}",
        f"Mapping titres courants : {result.latei_running_titles_map_path}",
        f"Titres courants abrégés : {result.latei_short_running_titles_count}",
        f"Assets LaTEI : {result.latei_assets_dir}",
        f"Images copiées : {result.latei_copied_images_count}",
        f"Warnings images : {len(result.latei_asset_warnings)}",
    ])
    for warning in result.latei_asset_warnings:
        lines.append(f"Warning image : {warning}")
    lines.extend([
        f"PDF LaTEI (debug) : {pdf_debug_status}",
        f"Log LaTEI : {result.latei_log_path}",
        f"XML restauré : {result.roundtrip_xml_path}",
        f"Diagnostics round-trip : {result.diagnostics_count}",
        f"Rapport diagnostics : {result.diagnostics_path}",
    ])
    if missing:
        lines.append("Artefacts manquants :")
        lines.extend(f"- {path}" for path in missing)
    else:
        lines.append("Prévol paquet LaTEI : tous les artefacts attendus sont présents.")
    return "\n".join(lines)


def latei_body_restored_stem(path: Path) -> str:
    """Return the source stem used for a restored XML file from a LaTEI body."""
    stem = Path(path).stem
    suffix = ".latei_body"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def latei_monofile_restored_stem(path: Path) -> str:
    """Return the source stem used for a restored XML file from a LaTEI monofile."""
    stem = Path(path).stem
    suffix = ".latei"
    if stem.endswith(suffix):
        return stem[: -len(suffix)]
    return stem


def run_gui() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
