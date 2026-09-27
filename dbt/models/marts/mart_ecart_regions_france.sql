/*
=============================================================================
Modèle : mart_ecart_regions_france
=============================================================================
Objectif :
    Écart annuel entre le total France et la somme des régions, tous sexes
    confondus. Illustre une limite du fichier : un prénom publié au niveau
    national peut être trop rare dans chaque région pour y figurer.
Source :
    stg_insee__prenoms, niveaux FRANCE et REG.
Grain :
    Une ligne = une année.
Attention :
    Mayotte (REG 06) n'est dans les régions qu'à partir de 2012, comme dans
    le total France : l'écart reste comparable d'une année à l'autre.
=============================================================================
*/

with totaux as (
    select
        annee,
        cast(sum(nombre_naissances) filter (where niveau_geo = 'FRANCE') as integer) as nombre_naissances_france,
        cast(sum(nombre_naissances) filter (where niveau_geo = 'REG') as integer)    as nombre_naissances_regions
    from {{ ref('stg_insee__prenoms') }}
    group by annee
)

select
    annee,
    nombre_naissances_france,
    nombre_naissances_regions,
    (nombre_naissances_france - nombre_naissances_regions) * 1.0
        / nombre_naissances_france                          as part_ecart   -- part des naissances France absentes des régions
from totaux
