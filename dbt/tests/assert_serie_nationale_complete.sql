-- Chaque couple (prénom, sexe) doit avoir exactement une ligne par année,
-- de 1900 à la dernière année publiée : ni trou, ni doublon.
select prenom, sexe, count(*) as lignes, count(distinct annee) as annees
from {{ ref('mart_prenoms_serie_nationale') }}
group by prenom, sexe
having count(*) <> {{ var('derniere_annee') }} - 1900 + 1
    or count(distinct annee) <> count(*)
    or min(annee) <> 1900
    or max(annee) <> {{ var('derniere_annee') }}
