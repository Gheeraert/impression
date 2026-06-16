import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image


def convertir_tiff_en_jpg(dossier_icono):
    """
    Parcourt récursivement le dossier 'hr' à l'intérieur du dossier icono,
    puis recrée la même arborescence dans 'br' en y enregistrant les images
    converties en .jpg.
    """
    dossier_hr = os.path.join(dossier_icono, "hr")
    dossier_br = os.path.join(dossier_icono, "br")

    # Vérifications de base
    if not os.path.isdir(dossier_hr):
        messagebox.showerror(
            "Erreur",
            f"Le dossier suivant est introuvable :\n{dossier_hr}"
        )
        return

    os.makedirs(dossier_br, exist_ok=True)

    # Récupération récursive de tous les TIFF dans hr
    fichiers_tiff = []
    for racine, _, fichiers in os.walk(dossier_hr):
        for nom_fichier in fichiers:
            if nom_fichier.lower().endswith((".tif", ".tiff")):
                fichiers_tiff.append(os.path.join(racine, nom_fichier))

    if not fichiers_tiff:
        messagebox.showinfo(
            "Information",
            "Aucun fichier TIFF trouvé dans le dossier 'hr' ni dans ses sous-dossiers."
        )
        return

    # Configuration de la barre de progression
    barre_progression["maximum"] = len(fichiers_tiff)
    barre_progression["value"] = 0
    variable_statut.set(f"Conversion en cours... (0/{len(fichiers_tiff)})")
    fenetre.update()

    compteur_succes = 0

    for i, chemin_source in enumerate(fichiers_tiff):
        # Chemin relatif par rapport à hr, ex. chapitre 1/image1.tif
        chemin_relatif = os.path.relpath(chemin_source, dossier_hr)

        # On remplace l'extension par .jpg
        chemin_relatif_jpg = os.path.splitext(chemin_relatif)[0] + ".jpg"

        # Chemin de destination dans br
        chemin_sortie = os.path.join(dossier_br, chemin_relatif_jpg)

        # Création du sous-dossier cible si nécessaire
        os.makedirs(os.path.dirname(chemin_sortie), exist_ok=True)

        try:
            with Image.open(chemin_source) as img:
                # Conversion systématique en RGB pour JPEG
                if img.mode != "RGB":
                    img = img.convert("RGB")

                img.save(chemin_sortie, "JPEG", quality=85, optimize=True)
                compteur_succes += 1

        except Exception as e:
            print(f"Erreur lors de la conversion de {chemin_source} : {e}")

        # Mise à jour de l'interface
        barre_progression["value"] = i + 1
        variable_statut.set(f"Conversion en cours... ({i + 1}/{len(fichiers_tiff)})")
        fenetre.update()

    variable_statut.set("Opération terminée !")
    messagebox.showinfo(
        "Succès",
        f"Conversion achevée.\n"
        f"{compteur_succes} fichier(s) converti(s).\n"
        f"Images enregistrées dans :\n{dossier_br}"
    )


def action_selectionner_dossier():
    dossier = filedialog.askdirectory(
        title="Sélectionner le dossier icono contenant hr et br"
    )
    if dossier:
        convertir_tiff_en_jpg(dossier)


# --- Configuration de l'interface Tkinter ---
fenetre = tk.Tk()
fenetre.title("Convertisseur TIFF -> JPG sRGB")
fenetre.geometry("520x170")
fenetre.resizable(False, False)

variable_statut = tk.StringVar()
variable_statut.set("En attente de sélection du dossier icono...")

cadre_principal = ttk.Frame(fenetre, padding="20")
cadre_principal.pack(fill=tk.BOTH, expand=True)

bouton_parcourir = ttk.Button(
    cadre_principal,
    text="Choisir le dossier icono et convertir",
    command=action_selectionner_dossier
)
bouton_parcourir.pack(pady=(0, 15))

barre_progression = ttk.Progressbar(
    cadre_principal,
    orient="horizontal",
    mode="determinate"
)
barre_progression.pack(fill=tk.X, pady=(0, 10))

label_statut = ttk.Label(
    cadre_principal,
    textvariable=variable_statut,
    justify=tk.CENTER
)
label_statut.pack()

if __name__ == "__main__":
    fenetre.mainloop()