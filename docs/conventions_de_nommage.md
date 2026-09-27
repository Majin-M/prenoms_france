# Conventions de nommage

Règles de nommage des schémas, tables, colonnes et scripts du projet.

## Principes généraux

- **snake_case** : lettres minuscules, mots séparés par `_`.
- **Pas d'accents ni d'espaces** dans les noms d'objets : `prenom`, pas `prénom`.
- **Pas de mots réservés SQL** comme noms de colonnes (`year`, `order`, `group`…).
- **Langue** : les colonnes métier sont en français, avec le vocabulaire de l'INSEE (`sexe`, `prenom`, `annee`). Les colonnes techniques sont en anglais, comme le veut l'usage dans dbt.

## Schémas

| Schéma | Contenu | Alimenté par |
|---|---|---|
| `raw` | Données source telles quelles | `ingest.py` |
| `staging` | Données nettoyées et typées, une table par source | dbt |
| `marts` | Tables prêtes pour l'analyse | dbt |

## Tables

### `raw`

- **`<entité>`** : le nom de l'entité, sans préfixe. Le schéma `raw` suffit à indiquer la couche.
- Les colonnes gardent **exactement** leur nom dans le fichier source, sans renommage ni changement de type.
- Exemple : `raw.prenoms`.

### `staging`

- **`stg_<source>__<entité>`**, avec un double underscore entre la source et l'entité, selon la convention dbt.
- C'est ici que les colonnes sont renommées et typées. Par exemple, `periode` (texte) devient `annee` (entier) et `valeur` devient `nombre_naissances`.
- Exemple : `staging.stg_insee__prenoms`.

### `marts`

- **`mart_<sujet>`** : un nom qui dit à quelle question la table répond.
- Exemple : `marts.mart_prenoms_par_annee`.

## Colonnes

### Colonnes techniques

- Préfixe **`_`** : ces colonnes décrivent le chargement, pas la donnée.
- On les repère ainsi tout de suite, et elles restent en fin de table.

| Colonne | Type | Signification |
|---|---|---|
| `_loaded_at` | `TIMESTAMP WITH TIME ZONE` | Date et heure du chargement dans `raw` |
| `_source_sha256` | `VARCHAR` | Empreinte sha256 du fichier source chargé |

### Suffixes

| Suffixe | Signification | Exemple |
|---|---|---|
| `_at` | Horodatage | `_loaded_at` |
| `_code` | Code officiel | `departement_code` |
| `nombre_` (préfixe) | Comptage | `nombre_naissances` |

## Scripts Python

- Un script par étape du pipeline, nommé d'après son rôle : `ingest.py`, `explore.py`.
- Les fonctions portent un verbe à l'infinitif : `telecharger`, `verifier_schema`, `charger`.
- Les constantes de configuration sont en majuscules en haut du fichier : `URL`, `PARQUET`, `DB`.
