from __future__ import annotations

import traceback
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .config import BuildConfig
from .site_builder import SiteBuilder


class App(ttk.Frame):
    """Interface graphique pour lancer les builds TEI -> site multi-pages."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=12)
        self.master = master
        self.builder = SiteBuilder()
        self.master_xml_var = tk.StringVar()
        self.assets_dir_var = tk.StringVar()
        self.output_dir_var = tk.StringVar()
        self.xml_files: list[Path] = []
        self._build_ui()

    def _build_ui(self) -> None:
        self.master.title("PURH — livre web TEI")
        self.master.geometry("1020x720")
        self.pack(fill="both", expand=True)

        title = ttk.Label(
            self,
            text="PURH — génération d’un livre web multi-pages à partir de TEI Métopes",
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
        self._add_path_selector(4, "Dossier de sortie", self.output_dir_var, self._choose_output_dir, "Choisir…")

        helper = ttk.Label(
            self,
            text="Conseil : placez vos médias dans assets/images, assets/audio et assets/video.",
        )
        helper.grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 8))

        button_bar = ttk.Frame(self)
        button_bar.grid(row=6, column=0, columnspan=3, sticky="w", pady=(8, 12))
        ttk.Button(button_bar, text="Construire le site", command=self._build).grid(row=0, column=0, padx=(0, 8))
        ttk.Button(button_bar, text="Ouvrir le dossier de sortie", command=self._open_output_dir).grid(row=0, column=1, padx=(0, 8))
        ttk.Button(button_bar, text="Effacer le journal", command=self._clear_log).grid(row=0, column=2)

        log_label = ttk.Label(self, text="Journal")
        log_label.grid(row=7, column=0, sticky="w")
        self.log = tk.Text(self, wrap="word", height=24)
        self.log.grid(row=8, column=0, columnspan=3, sticky="nsew")
        self.log.configure(state="disabled")

        self.columnconfigure(1, weight=1)
        self.rowconfigure(8, weight=1)
        self._log("Interface prête.")

    def _add_path_selector(self, row: int, label: str, variable: tk.StringVar, browse_command, button_text: str) -> None:
        ttk.Label(self, text=label).grid(row=row, column=0, sticky="w", pady=(0, 6))
        ttk.Entry(self, textvariable=variable).grid(row=row, column=1, sticky="ew", pady=(0, 6))
        ttk.Button(self, text=button_text, command=browse_command).grid(row=row, column=2, sticky="ew", pady=(0, 6))

    def _choose_master_xml(self) -> None:
        path = filedialog.askopenfilename(title="Choisir un fichier XML maître", filetypes=[("Fichiers XML", "*.xml")])
        if path:
            self.master_xml_var.set(path)
            self._log(f"Fichier maître : {path}")

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
            self._log(f"Dossier assets : {path}")

    def _choose_output_dir(self) -> None:
        path = filedialog.askdirectory(title="Choisir un dossier de sortie")
        if path:
            self.output_dir_var.set(path)
            self._log(f"Dossier de sortie : {path}")

    def _build(self) -> None:
        output_dir_text = self.output_dir_var.get().strip()
        if not output_dir_text:
            messagebox.showwarning("Sortie manquante", "Veuillez choisir un dossier de sortie.")
            return

        output_dir = Path(output_dir_text)
        assets_dir = Path(self.assets_dir_var.get()).resolve() if self.assets_dir_var.get().strip() else None
        master_xml_text = self.master_xml_var.get().strip()

        try:
            if master_xml_text:
                master_xml = Path(master_xml_text).resolve()
                self._log("Build multi-pages à partir du fichier maître…")
                result = self.builder.build_from_master(
                    master_xml,
                    BuildConfig(output_dir=output_dir, assets_dir=assets_dir),
                )
                self._log(f"Site généré : {result.html_path}")
                self._log(f"Rapport : {result.report_path}")
                return

            if self.xml_files:
                self._log("Build de plusieurs fichiers XML indépendants…")
                results = self.builder.build_from_many(self.xml_files, output_dir, assets_dir=assets_dir)
                self._log(f"{len(results)} site(s) généré(s).")
                return

            messagebox.showwarning("Aucun XML", "Choisissez un fichier maître XML ou un ensemble de fichiers XML.")
        except Exception as exc:
            self._log(f"Erreur : {exc}")
            self._log(traceback.format_exc())
            messagebox.showerror("Erreur pendant le build", str(exc))

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
