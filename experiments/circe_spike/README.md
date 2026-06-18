# Spike Circé

Ce dossier contient un petit client experimental pour evaluer Circé avec nos XML TEI / Metopes normalises. Il n'est pas branche a l'application, ne modifie pas la chaine de generation existante et ne declare pas Circé comme dependance applicative.

L'objectif est d'explorer, une fois l'API reelle documentee, si Circé peut produire une sortie LaTeX exploitable a partir d'un XML Metopes.

## Configuration

Copier `circe_config.example.json` vers `circe_config.json`, puis completer les endpoints reels apres inspection de l'API ou de la documentation Circé.

Tant que les endpoints requis sont vides, le script echoue proprement avec le message :

```text
Configuration Circé incomplète : renseigner les endpoints dans circe_config.json après inspection de l'API ou de la documentation.
```

Le script ne suppose pas les routes Circé. Les champs disponibles sont :

- `base_url` : URL racine de l'instance Circé.
- `upload_endpoint` : endpoint d'envoi du XML.
- `conversions_endpoint` : endpoint listant les conversions, si disponible.
- `convert_endpoint` : endpoint demandant une conversion.
- `download_endpoint` : endpoint de telechargement, si necessaire.
- `convert_payload_extra` : champs JSON additionnels a envoyer a la conversion.

## Usage

Exemple une fois `circe_config.json` complete :

```powershell
python experiments/circe_spike/circe_client.py `
  --config experiments/circe_spike/circe_config.json `
  --input samples/metopes_normalized.xml `
  --conversion "tei-to-latex" `
  --output-dir experiments/circe_spike/out
```

Lister les conversions si l'API le permet :

```powershell
python experiments/circe_spike/circe_client.py `
  --config experiments/circe_spike/circe_config.json `
  --list-conversions `
  --output-dir experiments/circe_spike/out
```

Verifier la configuration et les URLs construites sans appeler le reseau :

```powershell
python experiments/circe_spike/circe_client.py `
  --config experiments/circe_spike/circe_config.json `
  --input samples/metopes_normalized.xml `
  --conversion "tei-to-latex" `
  --dry-run `
  --output-dir experiments/circe_spike/out
```

## Sorties locales

Le dossier de sortie contient les reponses brutes utiles, les fichiers telecharges, une extraction automatique si une archive zip est retournee, une copie de `out.log` si elle est presente dans l'archive, et un `REPORT.md` resumant l'experience. Le rapport contient un champ `Verdict` a remplir apres analyse : exploitable, partiellement exploitable ou non exploitable.

## Limites

Ce script est volontairement un squelette configurable. Il faudra probablement ajuster le payload de conversion et les noms de champs apres lecture de l'API Circé reelle. Ces ajustements doivent rester dans ce dossier experimental tant que Circé n'est pas integre officiellement.
