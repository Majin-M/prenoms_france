-- Constat : chaque zone est couverte de 1900 à la dernière année publiée, sans trou,
-- sauf Mayotte (DEP 976, REG 06), présente seulement à partir de 2012.
-- D'après l'INSEE, les données d'avant 2012 portent sur la France hors Mayotte.
-- Une autre zone qui commencerait en cours de série serait un nouveau changement de périmètre.
with couverture as (
    select
        niveau_geo,
        geo_code,
        min(annee)            as premiere_annee,
        max(annee)            as derniere_annee,
        count(distinct annee) as annees
    from {{ ref('stg_insee__prenoms') }}
    group by niveau_geo, geo_code
),

attendu as (
    select
        *,
        case
            when (niveau_geo, geo_code) in (('DEP', '976'), ('REG', '06')) then 2012
            else 1900
        end as premiere_annee_attendue
    from couverture
)

select *
from attendu
where premiere_annee <> premiere_annee_attendue
   or derniere_annee <> {{ var('derniere_annee') }}
   or annees <> derniere_annee - premiere_annee + 1
