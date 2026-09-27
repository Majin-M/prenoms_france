-- Constat : aucun doublon sur le grain (prénom, sexe, année, zone).
-- Une zone s'identifie par niveau_geo + geo_code, les deux font partie de la clé.
select prenom, sexe, annee, niveau_geo, geo_code, count(*) as lignes
from {{ ref('stg_insee__prenoms') }}
group by all
having count(*) > 1
