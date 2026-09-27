-- Constat : 126 années distinctes, de 1900 à 2025, sans trou, à chaque niveau géographique.
-- La dernière année vient de la variable derniere_annee (dbt_project.yml) : une édition
-- incomplète, à qui il manquerait la dernière année, est ainsi détectée.
select
    niveau_geo,
    min(annee)            as premiere_annee,
    max(annee)            as derniere_annee,
    count(distinct annee) as annees
from {{ ref('stg_insee__prenoms') }}
group by niveau_geo
having min(annee) <> 1900
    or max(annee) <> {{ var('derniere_annee') }}
    or count(distinct annee) <> max(annee) - min(annee) + 1
