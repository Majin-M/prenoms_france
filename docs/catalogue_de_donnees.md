# Catalogue de données

Description des tables produites par le pipeline, de la source aux fichiers exportés. Les volumes correspondent à l'édition 2026 du fichier INSEE (naissances 1900-2025).

## Vue d'ensemble

| Couche | Objet | Type | Grain | Lignes |
|---|---|---|---|---|
| `raw` | `raw.prenoms` | table | prénom, sexe, année, zone | 6 622 949 |
| `staging` | `staging.stg_insee__prenoms` | vue | prénom, sexe, année, zone | 6 622 949 |
| `marts` | `marts.mart_prenoms_serie_nationale` | table | prénom, sexe, année | 6 594 840 |
| `marts` | `marts.mart_diversite_prenoms_par_annee` | table | année, sexe | 252 |
| `marts` | `marts.mart_ecart_regions_france` | table | année | 126 |

![Flux de données, du fichier Parquet aux fichiers JSON](img/flux_de_donnees.png)

## `raw.prenoms`

Copie fidèle du fichier Parquet de l'INSEE, chargée par `ingest.py`. Les colonnes gardent leur nom et leur type d'origine ; deux colonnes techniques sont ajoutées.

| Colonne | Type | Description |
|---|---|---|
| `sexe` | VARCHAR | `1` (garçons) ou `2` (filles) |
| `prenom` | VARCHAR | Prénom en majuscules |
| `periode` | VARCHAR | Année de naissance, en texte |
| `niveau_geographique` | VARCHAR | `FRANCE`, `REG` ou `DEP` |
| `geographie` | VARCHAR | Code de la zone, à lire avec `niveau_geographique` |
| `valeur` | INTEGER | Nombre de naissances, arrondi à un multiple de 5 |
| `rang` | INTEGER | Rang du prénom pour l'année, le sexe et la zone |
| `_loaded_at` | TIMESTAMP WITH TIME ZONE | Date et heure du chargement |
| `_source_sha256` | VARCHAR | Empreinte sha256 du fichier chargé |

## `staging.stg_insee__prenoms`

Nettoyage et typage de `raw.prenoms`, sans filtre ni agrégation : tous les niveaux géographiques sont conservés.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `sexe` | VARCHAR | `M` ou `F` | `M` |
| `prenom` | VARCHAR | Prénom en majuscules, accents et apostrophes conservés | `STEVEN` |
| `annee` | INTEGER | Année de naissance | `1992` |
| `nombre_naissances` | INTEGER | Naissances, arrondies à un multiple de 5 (minimum 5) | `2045` |
| `rang` | INTEGER | Rang du prénom pour l'année, le sexe et la zone (1 = le plus donné) | `43` |
| `niveau_geo` | VARCHAR | `FRANCE`, `REG` ou `DEP` | `FRANCE` |
| `geo_code` | VARCHAR | Code de la zone : `F` pour la France, 2 chiffres pour une région, 2 chiffres, `2A`, `2B` ou `971` à `976` pour un département | `F` |
| `_loaded_at` | TIMESTAMP WITH TIME ZONE | Repris de `raw` | |
| `_source_sha256` | VARCHAR | Repris de `raw` | |

Une zone s'identifie par `niveau_geo` + `geo_code` : `11` désigne l'Île-de-France en `REG` et l'Aude en `DEP`.

## `marts.mart_prenoms_serie_nationale`

Série annuelle complète de chaque prénom au niveau France, de 1900 à la dernière année publiée. Les années où le prénom est absent du fichier sont complétées par 0.

- **Grain** : un prénom, un sexe, une année.
- **Source** : `stg_insee__prenoms`, niveau `FRANCE`.
- **Volume** : 52 340 couples (prénom, sexe) × 126 années.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `prenom` | VARCHAR | Prénom | `STEVEN` |
| `sexe` | VARCHAR | `M` ou `F` | `M` |
| `annee` | INTEGER | Année de naissance | `1992` |
| `nombre_naissances` | INTEGER | Naissances publiées ; `0` si le prénom est absent du fichier cette année-là | `2045` |
| `rang` | INTEGER | Rang national ; vide si le prénom est absent du fichier | `43` |
| `est_publie` | BOOLEAN | Vrai si l'INSEE publie une ligne pour ce prénom, ce sexe et cette année | `true` |
| `part_naissances` | DOUBLE | Part du prénom parmi les naissances recensées dans le fichier, même année et même sexe (entre 0 et 1) | `0.0053` |

**À savoir**

- `nombre_naissances = 0` signifie « absent du fichier » : aucune naissance, ou trop peu pour être publiées. `est_publie` distingue ce 0 complété d'une valeur publiée.
- `part_naissances` est légèrement surestimée, car le dénominateur ne compte que les naissances recensées dans le fichier.
- Avant 2012, le niveau France exclut Mayotte.

## `marts.mart_diversite_prenoms_par_annee`

Indicateurs de diversité des prénoms donnés chaque année, au niveau France.

- **Grain** : une année, un sexe.
- **Source** : `mart_prenoms_serie_nationale`, lignes publiées uniquement.

| Colonne | Type | Description | Exemple (filles, 2025) |
|---|---|---|---|
| `annee` | INTEGER | Année de naissance | `2025` |
| `sexe` | VARCHAR | `M` ou `F` | `F` |
| `nombre_prenoms` | INTEGER | Prénoms distincts publiés | `7482` |
| `nombre_naissances` | INTEGER | Naissances recensées dans le fichier ; dénominateur des parts | `286795` |
| `part_top_10` | DOUBLE | Part des naissances portée par les 10 prénoms les plus donnés | `0.0868` |
| `nombre_prenoms_moitie_naissances` | INTEGER | Nombre minimal de prénoms, du plus au moins donné, pour couvrir la moitié des naissances | `180` |
| `nombre_effectif_prenoms` | DOUBLE | Inverse de l'indice de Simpson (1 / somme des parts au carré) : nombre de prénoms qui, donnés à parts égales, produiraient la même concentration | `427.4` |

**À savoir** : les prénoms trop rares ne sont pas dans le fichier, donc ces indicateurs sous-estiment la diversité réelle. Mayotte entre dans le périmètre en 2012 et apporte environ 2 % des prénoms publiés chaque année.

## `marts.mart_ecart_regions_france`

Écart annuel entre le total France et la somme des régions, tous sexes confondus. Un prénom publié au niveau national peut être trop rare dans chaque région pour y figurer.

- **Grain** : une année.
- **Source** : `stg_insee__prenoms`, niveaux `FRANCE` et `REG`.

| Colonne | Type | Description | Exemple |
|---|---|---|---|
| `annee` | INTEGER | Année de naissance | `2025` |
| `nombre_naissances_france` | INTEGER | Total des naissances au niveau France | `589485` |
| `nombre_naissances_regions` | INTEGER | Somme des naissances des régions | `528105` |
| `part_ecart` | DOUBLE | Part des naissances France absentes de la somme des régions | `0.1041` |

## Fichiers exportés

Écrits par `export.py` dans `exports/`, pour le portfolio. Seules les lignes publiées sont exportées.

| Fichier | Contenu | Source |
|---|---|---|
| `series/<INITIALE>.json` | `{"STEVEN": {"M": [[1946, 5], [1949, 5], ...]}}` : un fichier par initiale, sans accent et en majuscule (ÉLODIE est dans `E.json`) ; une année absente vaut 0 | `mart_prenoms_serie_nationale` |
| `diversite.json` | Une ligne par année et par sexe, avec toutes les colonnes du mart | `mart_diversite_prenoms_par_annee` |
| `ecart_regions.json` | Une ligne par année, avec toutes les colonnes du mart | `mart_ecart_regions_france` |
| `metadata.json` | Date de génération, empreinte de la source, années couvertes, nombres de lignes, règles de lecture, résumé de la dernière exécution dbt | Staging et `dbt/target/run_results.json` |
