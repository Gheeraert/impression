from __future__ import annotations

import json
import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .config import BuildConfig
from .local_server import PreviewServer
from .reversible_integration import run_reversible_export_for_file
from .site_builder import SiteBuilder, has_editor_pdf


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

        files_label = ttk.Label(self, text="Fichiers XML indépendants (optionnel)")
        files_label.grid(row=2, column=0, sticky="nw", pady=(0, 6))
        self.files_list = tk.Listbox(self, height=6)
        self.files_list.grid(row=2, column=1, sticky="nsew", pady=(0, 6))
        files_buttons = ttk.Frame(self)
        files_buttons.grid(row=2, column=2, sticky="n")
        ttk.Button(files_buttons, text="Ajouter…", command=self._choose_xml_files).grid(row=0, column=0, sticky="ew")
        ttk.Button(files_buttons, text="Vider", command=self._clear_xml_files).grid(row=1, column=0, sticky="ew", pady=(6, 0))

        self._add_path_selector(3, "Dossier assets", self.assets_dir_var, self._choose_assets_dir, "Choisir…")
        self._add_path_selector(4, "Quatrième de couverture (optionnel : .md, .markdown, .html, .txt)", self.back_cover_var, self._choose_back_cover, "Choisir…")
        self._add_entry_row(5, "Nom de la collection (optionnel)", self.collection_title_var)
        self._add_entry_row(6, "Numéro dans la collection (optionnel)", self.collection_number_var)
        self._add_entry_row(7, "ISSN de la collection (optionnel)", self.collection_issn_var)
        self._add_path_selector(8, "Dossier de sortie", self.output_dir_var, self._choose_output_dir, "Choisir…")

        self._add_pdf_export_controls(9)

        preview_bar = ttk.Frame(self)
        preview_bar.grid(row=10, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(preview_bar, text="Ports de prévisualisation").grid(row=0, column=0, sticky="w")
        ttk.Entry(preview_bar, textvariable=self.port_var, width=18).grid(row=0, column=1, sticky="w", padx=(8, 16))
        ttk.Checkbutton(preview_bar, text="Lancer le serveur local et ouvrir le navigateur après build", variable=self.auto_preview_var).grid(row=0, column=2, sticky="w")

        helper = ttk.Label(
            self,
            text=(
                "Le dossier choisi sera copié tel quel dans la sortie sous assets/. "
                "La collection est lue d’abord dans le TEI ; les champs ci-dessus ne servent que de repli. "
                "Même logique pour la quatrième : XML d’abord, puis fichier externe si nécessaire."
            ),
            wraplength=920,
        )
        helper.grid(row=11, column=0, columnspan=3, sticky="w", pady=(0, 8))

        button_bar = ttk.Frame(self)
        button_bar.grid(row=12, column=0, columnspan=3, sticky="w", pady=(8, 12))
        ttk.Button(button_bar, text="Charger config…", command=self._load_config).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Enregistrer config…", command=self._save_config).grid(row=0, column=1, padx=(0, 8))
        self.build_button = ttk.Button(button_bar, text="Construire le site", command=self._build)
        self.build_button.grid(row=0, column=2, padx=(0, 8))
        ttk.Button(button_bar, text="Relancer la prévisualisation", command=self._preview_existing_site).grid(row=0,
                                                                                                              column=3,
                                                                                                              padx=(
                                                                                                              0, 8))
        ttk.Button(button_bar, text="Ouvrir le dossier de sortie", command=self._open_output_dir).grid(row=0, column=4,
                                                                                                       padx=(0, 8))
        ttk.Button(button_bar, text="Effacer le journal", command=self._clear_log).grid(row=0, column=5)

        log_label = ttk.Label(self, text="Journal")
        log_label.grid(row=13, column=0, sticky="w")
        self.log = tk.Text(self, wrap="word", height=24)
        self.log.grid(row=14, column=0, columnspan=3, sticky="nsew")
        self.log.configure(state="disabled")

        self.columnconfigure(1, weight=1)
        self.rowconfigure(14, weight=1)
        self._refresh_pdf_export_controls()
        self._log("Interface prête.")

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.master)
        tools_menu = tk.Menu(menubar, tearoff=False)
        tools_menu.add_command(
            label="Tester la réversibilité TEI ↔ LaTeX…",
            command=self._run_reversible_export,
        )
        menubar.add_cascade(label="Outils", menu=tools_menu)
        self.master.config(menu=menubar)

    def _add_path_selector(self, row: int, label: str, variable: tk.StringVar, browse_command, button_text: str) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(0, 6))
        ttk.Button(self, text=button_text, command=browse_command).grid(row=row, column=2, sticky="ew", pady=(0, 6))

    def _add_entry_row(self, row: int, label: str, variable: tk.StringVar) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(0, 6))

    def _add_pdf_export_controls(self, row: int) -> None:
        ttk.Label(self, text="Sorties PDF / LaTeX").grid(row=row, column=0, sticky="w", pady=(0, 6))
        frame = ttk.Frame(self)
        frame.grid(row=row, column=1, columnspan=2, sticky="w", pady=(0, 6))
        options = [
            ("Ne rien générer", "none"),
            ("Générer le LaTeX seul", "latex"),
            ("Générer le LaTeX + PDF", "latex_pdf"),
        ]
        for index, (label, value) in enumerate(options):
            radio = ttk.Radiobutton(frame, text=label, variable=self.pdf_export_mode_var, value=value)
            radio.grid(row=0, column=index, sticky="w", padx=(0, 16))
            self.pdf_export_widgets.append(radio)
        ttk.Label(frame, textvariable=self.pdf_export_status_var).grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 0))

    def _choose_master_xml(self) -> None:
        path = filedialog.askopenfilename(title="Choisir un fichier XML maître", filetypes=[("Fichiers XML", "*.xml")])
        if path:
            self.master_xml_var.set(path)
            self._log(f"Fichier maître : {path}")

    def _run_reversible_export(self) -> None:
        path = filedialog.askopenfilename(
            title="Choisir un fichier XML TEI à tester",
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
            self._log(f"Erreur export réversible : {exc}")
            self._log(traceback.format_exc())
            messagebox.showerror("Réversibilité TEI / LaTeX", str(exc))
            return

        self._log(result.message)
        self._log(f"LaTeX réversible : {result.latex_path}")
        self._log(f"XML round-trip : {result.roundtrip_xml_path}")
        self._log(f"Diagnostics : {result.diagnostics_path}")

        details = (
            f"{result.message}\n\n"
            f"LaTeX : {result.latex_path}\n"
            f"XML round-trip : {result.roundtrip_xml_path}\n"
            f"Diagnostics : {result.diagnostics_path}"
        )
        if result.success:
            messagebox.showinfo("Réversibilité TEI / LaTeX", details)
        else:
            messagebox.showwarning("Réversibilité TEI / LaTeX", details)

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
            self.pdf_export_status_var.set("PDF éditeur détecté : la génération LaTeX/PDF est désactivée.")
        else:
            self.pdf_export_status_var.set("")
        for widget in self.pdf_export_widgets:
            widget.configure(state=state)

    def _build(self) -> None:
        output_dir_text = self.output_dir_var.get().strip()
        if not output_dir_text:
            messagebox.showwarning("Sortie manquante", "Veuillez choisir un dossier de sortie.")
            return

        output_dir = Path(output_dir_text)
        assets_dir = Path(self.assets_dir_var.get()).resolve() if self.assets_dir_var.get().strip() else None
        master_xml_text = self.master_xml_var.get().strip()
        self._refresh_pdf_export_controls()

        wait_dialog = self._show_build_wait_dialog()
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
            messagebox.showerror("Erreur pendant le build", str(exc))
        finally:
            self._close_build_wait_dialog(wait_dialog)

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
            text="Veuillez patienter pendant la génération.",
        ).grid(row=1, column=0, sticky="w", pady=(6, 12))
        progress = ttk.Progressbar(frame, mode="indeterminate", length=280)
        progress.grid(row=2, column=0, sticky="ew")
        progress.start(12)

        dialog.update_idletasks()
        x = self.master.winfo_rootx() + max((self.master.winfo_width() - dialog.winfo_width()) // 2, 0)
        y = self.master.winfo_rooty() + max((self.master.winfo_height() - dialog.winfo_height()) // 2, 0)
        dialog.geometry(f"+{x}+{y}")
        dialog.lift(self.master)
        self.update_idletasks()
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


def run_gui() -> None:
    root = tk.Tk()
    App(root)
    root.mainloop()
