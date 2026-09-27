{{ config(severity = 'warn') }}
-- Constat : par année et par sexe, la somme des régions est toujours inférieure au total France.
-- Un prénom assez fréquent au niveau national peut être trop rare dans chaque région
-- pour y être diffusé : il compte alors pour la France mais pour aucune région.
-- L'écart grandit avec la diversité des prénoms : 1,1 % en 1900, 11,6 % au maximum (2024).
-- On signale sans bloquer :
--   - une somme régionale supérieure au national (jamais observé, incohérent) ;
--   - un écart au-delà de 15 %, nettement au-dessus du maximum observé.
with totaux as (
    select
        annee,
        sexe,
        sum(nombre_naissances) filter (where niveau_geo = 'REG')    as nombre_naissances_regions,
        sum(nombre_naissances) filter (where niveau_geo = 'FRANCE') as nombre_naissances_france
    from {{ ref('stg_insee__prenoms') }}
    group by annee, sexe
)

select
    *,
    round(100.0 * (nombre_naissances_france - nombre_naissances_regions) / nombre_naissances_france, 1) as ecart_pct
from totaux
where nombre_naissances_regions > nombre_naissances_france
   or nombre_naissances_france - nombre_naissances_regions > 0.15 * nombre_naissances_france
