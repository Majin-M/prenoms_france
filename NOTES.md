# Notes d'exploration

Constats tirés de [exploration/explore.py](exploration/explore.py) sur le fichier `prenoms-2025.parquet` (édition juillet 2026).

## Constats

- 6 622 949 lignes : FRANCE 724 645, REG 1 928 764, DEP 3 969 540.
- 126 années distinctes (1900-2025), vérifiées avec `count(DISTINCT periode)`. Le 117 donné par `SUMMARIZE` est une estimation (`approx_unique`), pas un vrai trou.
- Aucune valeur nulle, aucun doublon sur (`prenom`, `sexe`, `periode`, `niveau_geographique`, `geographie`).
- Effectifs tous multiples de 5, minimum 5.
- Colonnes en minuscules dans le Parquet, en majuscules dans la documentation INSEE. `ingest.py` compare les noms en minuscules et accepte donc les deux.
- **Une année absente n'a pas de ligne, pas de 0.** STEVEN a 78 lignes au niveau FRANCE ; il manque par exemple 1947 et 1948.
- **Pas de ligne qui regroupe les prénoms rares** (aucun prénom en `_`) : ils sont absents du fichier.
- **2020 : 677 665 naissances dans le fichier, contre 735 186 selon l'INSEE (France).** Il manque 57 521 naissances, soit 7,8 %, environ une sur treize.
- **La somme des régions est toujours inférieure au total France**, par année et par sexe, sur les 252 couples (année, sexe). L'écart moyen passe de 1,1 % dans les années 1900 à 2,5 % dans les années 1970, 6,1 % dans les années 2000 et 10,0 % dans les années 2020, avec un maximum de 11,6 % (filles, 2024). Surveillé par le test `assert_regions_coherentes_avec_france` (avertissement au-delà de 15 %).
- **Une zone = `niveau_geographique` + `geographie`.** `11` désigne l'Île-de-France au niveau REG et l'Aude au niveau DEP ; `01` désigne la Guadeloupe ou l'Ain.
- Prénoms avec apostrophe (92 prénoms distincts, dont `A'LIA`, le premier par ordre alphabétique) et caractères non français (`ÜMMÜ`). Les requêtes doivent être paramétrées, jamais construites par concaténation.

## Décisions de modélisation

| Sujet | Décision | Statut |
|---|---|---|
| Années sans ligne | Compléter par 0 dans le mart `mart_prenoms_serie_nationale` (colonne `est_publie` pour distinguer un 0 complété d'une ligne publiée) | Décidé |
| Clé d'une zone | Toujours joindre sur `niveau_geographique` + `geographie` | Décidé |
| Part de naissances | Colonne `part_naissances` du mart : `nombre_naissances` / total du fichier pour la même année et le même sexe. Affichée avec la mention « part parmi les naissances recensées dans le fichier des prénoms ». Légèrement surestimée, surtout les années récentes | Décidé |
| Export vers le site | Le mart reste complet (89 % de zéros complétés) pour l'analyse en SQL ; l'export n'envoie que les lignes `est_publie`, le site complète les années manquantes par 0 | Décidé |

## Interprétations

- **Écart régions / France : les prénoms trop rares au niveau régional ne sont pas publiés.** Un prénom assez fréquent en France pour être diffusé peut être sous le seuil dans chaque région : il compte alors pour la France et pour aucune région. L'arrondi à 5 ne suffit pas à l'expliquer, car il ferait varier l'écart dans les deux sens, alors qu'il va toujours dans le même sens. L'écart grandit avec la diversité des prénoms. Explication fortement appuyée, mais non prouvée directement : les données sous le seuil ne sont pas accessibles.

## Hypothèses à vérifier

- **La part des naissances absentes augmente avec le temps.** Les parents choisissent des prénoms de plus en plus variés depuis les années 1970, donc davantage d'enfants portent un prénom trop rare pour figurer dans le fichier. Pour le vérifier, il faut refaire le calcul de 2020 sur 1950, 1980 et 2000, avec les totaux de naissances publiés par l'INSEE.
- **L'indicateur de diversité sous-estime la variété réelle des prénoms**, puisque les prénoms les plus rares ne sont pas comptés.

## Pistes d'amélioration

- Ajouter les naissances annuelles de l'INSEE comme seconde source, pour calculer les parts sur le vrai nombre de naissances.
