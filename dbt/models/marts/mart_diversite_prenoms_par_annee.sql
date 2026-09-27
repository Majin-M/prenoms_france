/*
=============================================================================
Modèle : mart_diversite_prenoms_par_annee
=============================================================================
Objectif :
    Indicateurs de diversité des prénoms donnés chaque année, par sexe, au
    niveau France :
      - nombre_prenoms : prénoms distincts publiés
      - part_top_10 : part des naissances portée par les 10 prénoms les plus donnés
      - nombre_prenoms_moitie_naissances : nombre minimal de prénoms pour
        couvrir la moitié des naissances
      - nombre_effectif_prenoms : inverse de l'indice de Simpson (1 / somme des
        parts au carré). Vaut N si N prénoms étaient donnés à parts égales.
Source :
    mart_prenoms_serie_nationale, lignes publiées uniquement.
Grain :
    Une ligne = une année, un sexe.
Attention :
    Les prénoms trop rares ne sont pas dans le fichier : tous ces indicateurs
    sous-estiment la diversité réelle, et d'autant plus que l'année est récente.
    Le périmètre change en 2012 : Mayotte entre dans le fichier et apporte
    environ 2 % des prénoms publiés chaque année (rares ailleurs en France).
=============================================================================
*/

with publies as (
    select annee, sexe, prenom, nombre_naissances, part_naissances
    from {{ ref('mart_prenoms_serie_nationale') }}
    where est_publie
),

classes as (
    select
        *,
        row_number() over (partition by annee, sexe order by nombre_naissances desc, prenom) as position,
        sum(part_naissances) over (
            partition by annee, sexe
            order by nombre_naissances desc, prenom
            rows between unbounded preceding and current row
        )                                                                                   as part_cumulee
    from publies
)

select
    annee,
    sexe,
    cast(count(*) as integer)                             as nombre_prenoms,
    cast(sum(nombre_naissances) as integer)               as nombre_naissances,
    sum(part_naissances) filter (where position <= 10)    as part_top_10,
    cast(min(position) filter (where part_cumulee >= 0.5) as integer)
                                                          as nombre_prenoms_moitie_naissances,
    1 / sum(part_naissances * part_naissances)            as nombre_effectif_prenoms
from classes
group by annee, sexe
