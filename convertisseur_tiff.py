import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image


def convertir_tiff_en_jpg(dossier_source):
    # Création du sous-dossier de destination pour garder les choses propres
    dossier_dest = os.path.join(dossier_source, "convertis_jpg")
    os.makedirs(dossier_dest, exist_ok=True)

    # Récupération de la liste des fichiers TIFF
    fichiers_tiff = [f for f in os.listdir(dossier_source) if f.lower().endswith(('.tif', '.tiff'))]

    if not fichiers_tiff:
        messagebox.showinfo("Information", "Aucun fichier TIFF trouvé dans le dossier sélectionné.")
        return

    # Configuration de la barre de progression
    barre_progression['maximum'] = len(fichiers_tiff)
    barre_progression['value'] = 0
    variable_statut.set(f"Conversion en cours... (0/{len(fichiers_tiff)})")
    fenetre.update()

    compteur_succes = 0

    for i, nom_fichier in enumerate(fichiers_tiff):
        chemin_source = os.path.join(dossier_source, nom_fichier)
        nom_sortie = os.path.splitext(nom_fichier)[0] + ".jpg"
        chemin_sortie = os.path.join(dossier_dest, nom_sortie)

        try:
            # Traitement de l'image
            with Image.open(chemin_source) as img:
                # Conversion du mode colorimétrique
                # Si l'image est en CMJN (CMYK) ou a une couche alpha (RGBA) / palette (P)
                if img.mode in ('CMYK', 'RGBA', 'P'):
                    img = img.convert('RGB')

                # Sauvegarde avec optimisation pour le web
                img.save(chemin_sortie, "JPEG", quality=85, optimize=True)
                compteur_succes += 1

        except Exception as e:
            print(f"Erreur lors de la conversion de {nom_fichier} : {e}")

        # Mise à jour de l'interface
        barre_progression['value'] = i + 1
        variable_statut.set(f"Conversion en cours... ({i + 1}/{len(fichiers_tiff)})")
        fenetre.update()

    variable_statut.set("Opération terminée !")
    messagebox.showinfo("Succès",
                        f"Conversion achevée.\n{compteur_succes} fichier(s) converti(s).\nEnregistrés dans :\n{dossier_dest}")


def action_selectionner_dossier():
    dossier = filedialog.askdirectory(title="Sélectionner le dossier contenant les images TIFF")
    if dossier:
        convertir_tiff_en_jpg(dossier)


# --- Configuration de l'interface Tkinter ---
fenetre = tk.Tk()
fenetre.title("Convertisseur TIFF -> JPG sRGB")
fenetre.geometry("500x160")
fenetre.resizable(False, False)

# Variables de contrôle Tkinter
variable_statut = tk.StringVar()
variable_statut.set("En attente de sélection d'un dossier...")

# Éléments de l'interface
cadre_principal = ttk.Frame(fenetre, padding="20")
cadre_principal.pack(fill=tk.BOTH, expand=True)

bouton_parcourir = ttk.Button(cadre_principal, text="Choisir un dossier et convertir",
                              command=action_selectionner_dossier)
bouton_parcourir.pack(pady=(0, 15))

barre_progression = ttk.Progressbar(cadre_principal, orient='horizontal', mode='determinate')
barre_progression.pack(fill=tk.X, pady=(0, 10))

label_statut = ttk.Label(cadre_principal, textvariable=variable_statut, justify=tk.CENTER)
label_statut.pack()

# Lancement de la boucle d'événements
if __name__ == "__main__":
    fenetre.mainloop()