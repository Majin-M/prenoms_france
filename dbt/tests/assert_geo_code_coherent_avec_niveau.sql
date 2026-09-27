-- Constat : un geo_code n'a de sens qu'avec son niveau_geo (11 = Île-de-France en REG, Aude en DEP).
-- On vérifie que chaque code a la forme attendue pour son niveau :
--   FRANCE : F
--   REG    : 2 chiffres
--   DEP    : 2 chiffres, 2A / 2B (Corse) ou 971 à 976 (outre-mer)
select niveau_geo, geo_code, count(*) as lignes
from {{ ref('stg_insee__prenoms') }}
where not (
       (niveau_geo = 'FRANCE' and geo_code = 'F')
    or (niveau_geo = 'REG'    and regexp_full_match(geo_code, '[0-9]{2}'))
    or (niveau_geo = 'DEP'    and regexp_full_match(geo_code, '[0-9]{2}|2[AB]|97[1-6]'))
)
group by all
