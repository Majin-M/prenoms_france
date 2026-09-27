/*
=============================================================================
Modèle : stg_insee__prenoms
=============================================================================
Objectif :
    Première couche de nettoyage des prénoms INSEE : noms de colonnes
    explicites, sexe lisible ('M' / 'F' au lieu de '1' / '2') et année
    typée en entier. Aucune ligne n'est filtrée ni agrégée : les
    regroupements (_PRENOMS_RARES...) et les niveaux géographiques sont
    conservés tels quels, les choix métier se font dans les couches suivantes.
Source :
    raw.prenoms (chargée par ingest.py)
Grain :
    Une ligne = un prénom, un sexe, une année, une zone géographique.
=============================================================================
*/

select
    case sexe
        when '1' then 'M'
        when '2' then 'F'
    end                                  as sexe,          -- 'M' ou 'F' au lieu de '1' / '2'
    prenom,
    cast(periode as integer)             as annee,         -- periode est du texte : la convertir en entier
    valeur                               as nombre_naissances,
    rang,
    niveau_geographique                  as niveau_geo,
    geographie                           as geo_code,
    _loaded_at,
    _source_sha256
from {{ source('insee', 'prenoms') }}
