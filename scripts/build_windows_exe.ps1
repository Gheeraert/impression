# Reconstruit dist/main.exe et dist/main.cmd à l'identique du build actuel.
#
# Mode « accéléré » (ni --standalone, ni --onefile) : l'exécutable produit
# reste dépendant du .venv utilisé pour la compilation (DLL Python, paquets
# installés). dist/main.cmd, généré par Nuitka, positionne PYTHONHOME et
# PYTHONPATH vers ce .venv avant de lancer main.exe. Ce n'est donc PAS un
# exécutable autonome/portable : la machine cible doit disposer du même
# .venv (ou d'un .venv équivalent) au même chemin.
#
# Prérequis : pip install -r requirements-build.txt
#
# Usage : powershell -File scripts\build_windows_exe.ps1

$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

python -m nuitka `
    --windows-console-mode=disable `
    --output-dir=dist `
    main.py
