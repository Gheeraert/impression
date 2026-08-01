# tools/

Utilitaires autonomes, non intégrés au pipeline principal d'Impressions (pas
d'import depuis `purh_site/`). Chacun a ses propres dépendances, distinctes
de `requirements.txt`.

## convertisseur_tiff.py

Petit outil Tkinter destiné aux éditrices/éditeurs pour convertir en lot les
images TIFF haute résolution (`icono/hr/`) en JPEG basse résolution
(`icono/br/`), avant intégration dans un projet Impressions.

Dépendance : Pillow (voir `requirements-tools.txt`).

```
pip install -r tools/requirements-tools.txt
python tools/convertisseur_tiff.py
```
