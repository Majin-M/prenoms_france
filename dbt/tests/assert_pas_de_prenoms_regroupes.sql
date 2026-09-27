-- Constat : aucune ligne ne regroupe les prénoms rares (pas de prénom commençant par _).
-- Si l'INSEE en réintroduisait, les sommes de naissances changeraient de sens.
select prenom, count(*) as lignes
from {{ ref('stg_insee__prenoms') }}
where starts_with(prenom, '_')
group by prenom
