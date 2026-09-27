-- Constat : l'INSEE arrondit les effectifs à 5, le minimum vaut 5.
-- Une année sans naissance n'a pas de ligne : aucun effectif ne doit valoir 0.
select *
from {{ ref('stg_insee__prenoms') }}
where nombre_naissances % 5 <> 0
   or nombre_naissances < 5
