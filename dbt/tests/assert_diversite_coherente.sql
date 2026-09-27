-- Une ligne par année et par sexe, avec des indicateurs cohérents entre eux :
--   - le total des naissances est celui de la série nationale ;
--   - part_top_10 est une part, entre 0 et 1 ;
--   - 1 <= nombre_prenoms_moitie_naissances <= nombre_prenoms ;
--   - 1 <= nombre_effectif_prenoms <= nombre_prenoms (égalité si toutes les parts sont égales).
with serie as (
    select annee, sexe, sum(nombre_naissances) as nombre_naissances
    from {{ ref('mart_prenoms_serie_nationale') }}
    group by annee, sexe
),

diversite as (
    select *, count(*) over (partition by annee, sexe) as lignes
    from {{ ref('mart_diversite_prenoms_par_annee') }}
)

select d.*, s.nombre_naissances as naissances_serie
from diversite as d
full outer join serie as s using (annee, sexe)
where d.lignes is distinct from 1
   or d.nombre_naissances is distinct from s.nombre_naissances
   or d.part_top_10 not between 0 and 1
   or d.nombre_prenoms_moitie_naissances not between 1 and d.nombre_prenoms
   or d.nombre_effectif_prenoms < 1 - 1e-9
   or d.nombre_effectif_prenoms > d.nombre_prenoms + 1e-9
