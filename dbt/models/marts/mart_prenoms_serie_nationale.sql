/*
=============================================================================
Modèle : mart_prenoms_serie_nationale
=============================================================================
Objectif :
    Série annuelle complète de chaque prénom au niveau France, base de la
    courbe « tape ton prénom » et des autres marts. Les années sans ligne
    dans le fichier INSEE sont complétées par 0, de 1900 à la dernière
    année publiée (variable derniere_annee).
Source :
    stg_insee__prenoms, niveau FRANCE uniquement.
Grain :
    Une ligne = un prénom, un sexe, une année.
Attention :
    nombre_naissances = 0 signifie « absent du fichier » : aucune naissance, ou
    trop peu pour être diffusées. Ce n'est pas forcément zéro naissance.
    part_naissances est calculée sur les naissances recensées dans le
    fichier des prénoms (même année, même sexe), pas sur toutes les
    naissances : elle est légèrement surestimée, surtout les années
    récentes (7,8 % des naissances absentes du fichier en 2020).
=============================================================================
*/

with national as (
    select prenom, sexe, annee, nombre_naissances, rang
    from {{ ref('stg_insee__prenoms') }}
    where niveau_geo = 'FRANCE'
),

annees as (
    select unnest(range(1900, {{ var('derniere_annee') }} + 1)) as annee
),

prenoms as (
    select distinct prenom, sexe
    from national
)

select
    p.prenom,
    p.sexe,
    a.annee,
    coalesce(n.nombre_naissances, 0)        as nombre_naissances,
    n.rang,                                             -- null quand le prénom est absent du fichier
    n.nombre_naissances is not null         as est_publie,
    coalesce(n.nombre_naissances, 0) * 1.0
        / sum(coalesce(n.nombre_naissances, 0)) over (partition by a.annee, p.sexe)
                                            as part_naissances   -- part parmi les naissances recensées dans le fichier
from prenoms as p
cross join annees as a
left join national as n
    on  n.prenom = p.prenom
    and n.sexe   = p.sexe
    and n.annee  = a.annee
