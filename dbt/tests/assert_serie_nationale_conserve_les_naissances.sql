-- Le complément par 0 ne doit ni perdre ni ajouter de naissances :
-- par année et par sexe, le mart doit donner le même total que le niveau FRANCE de staging.
with mart as (
    select annee, sexe, sum(nombre_naissances) as nombre_naissances, count(*) filter (where est_publie) as lignes_publiees
    from {{ ref('mart_prenoms_serie_nationale') }}
    group by annee, sexe
),

staging as (
    select annee, sexe, sum(nombre_naissances) as nombre_naissances, count(*) as lignes_publiees
    from {{ ref('stg_insee__prenoms') }}
    where niveau_geo = 'FRANCE'
    group by annee, sexe
)

select *
from mart
full outer join staging using (annee, sexe)
where mart.nombre_naissances is distinct from staging.nombre_naissances
   or mart.lignes_publiees is distinct from staging.lignes_publiees
