-- Par année et par sexe, les parts doivent être comprises entre 0 et 1 et leur somme valoir 1.
-- La tolérance absorbe les erreurs d'arrondi des nombres à virgule.
select annee, sexe, sum(part_naissances) as somme_parts, min(part_naissances) as part_min, max(part_naissances) as part_max
from {{ ref('mart_prenoms_serie_nationale') }}
group by annee, sexe
having abs(sum(part_naissances) - 1) > 1e-9
    or min(part_naissances) < 0
    or max(part_naissances) > 1
