"""
=============================================================================
Export : marts DuckDB → fichiers JSON pour le portfolio
=============================================================================
Objectif :
    Écrit dans exports/ les données dont le site a besoin, en n'exportant que
    les lignes publiées par l'INSEE (le site complète les années manquantes
    par 0) :
      - series/<INITIALE>.json : un fichier par initiale, sans accent et en
        majuscule (ÉLODIE va dans E.json). Format :
        {"STEVEN": {"M": [[1946, 5], [1949, 5], ...]}}.
      - diversite.json : indicateurs par année et par sexe, dont le total des
        naissances recensées, qui sert de dénominateur aux parts.
      - ecart_regions.json : écart annuel entre le total France et la somme
        des régions.
      - metadata.json : date de génération, empreinte de la source, nombres
        de lignes, années couvertes, règles de lecture pour le site, et résumé
        de la dernière exécution dbt (modèles, tests, durées).

    Les graphiques sont dessinés par le portfolio, qui lit ces fichiers :
    ce projet s'arrête à la préparation des données.

Utilisation :
    python export.py   (après dbt build)

Attention :
    Le dossier exports/ est entièrement réécrit à chaque exécution.
    Lecture seule sur la base DuckDB. Le résumé dbt vient de
    dbt/target/run_results.json : il décrit la dernière commande dbt lancée,
    d'où l'intérêt de passer par run.ps1 (dbt build juste avant l'export).
=============================================================================
"""

from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
import json
import logging
import shutil
import sys
import time
import unicodedata

import duckdb

RACINE = Path(__file__).resolve().parent
DB = RACINE / "data" / "prenoms.duckdb"
EXPORTS = RACINE / "exports"
LOGS = RACINE / "logs"
RUN_RESULTS = RACINE / "dbt" / "target" / "run_results.json"

log = logging.getLogger("export")


def configurer_logs() -> None:
    """Écrit les messages à la fois dans le terminal et dans logs/export.log."""
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGS / "export.log", encoding="utf-8"),
        ],
    )


def formater(nombre: int) -> str:
    """Formate un entier à la française : 724645 -> '724 645'."""
    return f"{nombre:,}".replace(",", " ")


@contextmanager
def etape(nom: str):
    """Annonce le début d'une étape, sa fin et sa durée, ou son échec."""
    log.info("[DÉBUT] %s", nom)
    debut = time.perf_counter()
    try:
        yield
    except Exception:
        log.exception("[ÉCHEC] %s après %.2f s", nom, time.perf_counter() - debut)
        raise
    log.info("[OK]    %s en %.2f s", nom, time.perf_counter() - debut)


def initiale(prenom: str) -> str:
    """Initiale sans accent, en majuscule : 'ÉLODIE' -> 'E'. Le site applique la même règle."""
    return unicodedata.normalize("NFD", prenom[0])[0].upper()


def ecrire_json(chemin: Path, donnees) -> int:
    """Écrit un JSON compact (sans espaces) et renvoie sa taille en octets."""
    chemin.parent.mkdir(parents=True, exist_ok=True)
    texte = json.dumps(donnees, ensure_ascii=False, separators=(",", ":"))
    chemin.write_text(texte, encoding="utf-8")
    return len(texte.encode("utf-8"))


def exporter_series(con, dossier: Path) -> tuple[int, int, int]:
    """Écrit un fichier par initiale ; renvoie (lignes exportées, fichiers, octets)."""
    lignes = con.execute("""
        SELECT prenom, sexe, annee, nombre_naissances
        FROM marts.mart_prenoms_serie_nationale
        WHERE est_publie
        ORDER BY prenom, sexe, annee
    """).fetchall()

    par_initiale: dict[str, dict] = defaultdict(dict)
    for prenom, sexe, annee, nombre in lignes:
        par_initiale[initiale(prenom)].setdefault(prenom, {}).setdefault(sexe, []).append([annee, nombre])

    octets = sum(ecrire_json(dossier / f"{i}.json", prenoms) for i, prenoms in par_initiale.items())
    return len(lignes), len(par_initiale), octets


def exporter_diversite(con, chemin: Path) -> int:
    colonnes = ["annee", "sexe", "nombre_prenoms", "nombre_naissances", "part_top_10",
                "nombre_prenoms_moitie_naissances", "nombre_effectif_prenoms"]
    lignes = con.execute(f"""
        SELECT {", ".join(colonnes)}
        FROM marts.mart_diversite_prenoms_par_annee
        ORDER BY annee, sexe
    """).fetchall()
    donnees = [
        {c: (round(v, 6) if isinstance(v, float) else v) for c, v in zip(colonnes, ligne)}
        for ligne in lignes
    ]
    return ecrire_json(chemin, donnees)


def exporter_ecart_regions(con, chemin: Path) -> int:
    lignes = con.execute("""
        SELECT annee, nombre_naissances_france, nombre_naissances_regions, part_ecart
        FROM marts.mart_ecart_regions_france
        ORDER BY annee
    """).fetchall()
    return ecrire_json(chemin, [
        {"annee": a, "nombre_naissances_france": f, "nombre_naissances_regions": r,
         "part_ecart": round(e, 6)}
        for a, f, r, e in lignes
    ])


def resumer_dbt() -> dict | None:
    """Résume dbt/target/run_results.json : modèles, tests par statut, durées."""
    if not RUN_RESULTS.is_file():
        log.warning("Pas de %s : résumé dbt absent de metadata.json", RUN_RESULTS.name)
        return None
    run = json.loads(RUN_RESULTS.read_text(encoding="utf-8"))
    commande = run["args"].get("which")
    if commande != "build":
        log.warning("La dernière commande dbt est « %s », pas « build » : résumé partiel", commande)

    modeles, tests = [], defaultdict(int)
    for r in run["results"]:
        type_noeud, _, nom = r["unique_id"].split(".", 2)
        if type_noeud == "model":
            modeles.append({"nom": nom.split(".")[-1], "statut": r["status"],
                            "duree_s": round(r["execution_time"], 2)})
        elif type_noeud == "test":
            tests[r["status"]] += 1
    return {
        "commande": commande,
        "version": run["metadata"]["dbt_version"],
        "execute_le": run["metadata"]["generated_at"],
        "duree_totale_s": round(run["elapsed_time"], 1),
        "modeles": modeles,
        "tests": {"total": sum(tests.values()), **dict(tests)},
    }


def exporter_metadata(con, chemin: Path, lignes_series: int) -> int:
    premiere_annee, derniere_annee, lignes_source, sha256, charge_le = con.execute("""
        SELECT min(annee), max(annee), count(*), any_value(_source_sha256), max(_loaded_at)
        FROM staging.stg_insee__prenoms
    """).fetchone()
    return ecrire_json(chemin, {
        "genere_le": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": {
            "producteur": "INSEE, fichier des prénoms",
            "sha256": sha256,
            "charge_le": charge_le.isoformat(),
        },
        "annees": {"premiere": premiere_annee, "derniere": derniere_annee},
        "lignes": {
            "source": lignes_source,
            "series_exportees": lignes_series,
        },
        "fichiers_series": "series/<INITIALE>.json : initiale sans accent, en majuscule",
        "annees_absentes": "une année absente d'une série vaut 0 : aucune naissance ou trop peu pour être publiées",
        "parts": "nombre_naissances / diversite.nombre_naissances (même année, même sexe) : "
                 "part parmi les naissances recensées dans le fichier des prénoms",
        "perimetre": "France hors Mayotte avant 2012, Mayotte incluse à partir de 2012",
        "dbt": resumer_dbt(),
    })


def main() -> int:
    configurer_logs()
    log.info("=" * 60)
    log.info("Export des marts vers exports/")
    log.info("=" * 60)
    debut = time.perf_counter()

    try:
        with duckdb.connect(str(DB), read_only=True) as con:
            with etape("Nettoyage de exports/"):
                shutil.rmtree(EXPORTS, ignore_errors=True)
            with etape("Séries par prénom"):
                lignes, fichiers, octets_series = exporter_series(con, EXPORTS / "series")
            with etape("Indicateurs de diversité"):
                octets_diversite = exporter_diversite(con, EXPORTS / "diversite.json")
            with etape("Écart régions / France"):
                exporter_ecart_regions(con, EXPORTS / "ecart_regions.json")
            with etape("Métadonnées"):
                exporter_metadata(con, EXPORTS / "metadata.json", lignes)
    except Exception:
        log.error("=" * 60)
        log.error("Export interrompu après %.2f s, voir le détail ci-dessus",
                  time.perf_counter() - debut)
        log.error("=" * 60)
        return 1

    log.info("=" * 60)
    log.info("Export terminé")
    log.info("   - Lignes de séries exportées : %s", formater(lignes))
    log.info("   - Fichiers series/ : %s (%.1f Mo au total)", fichiers, octets_series / 1e6)
    log.info("   - diversite.json : %.1f Ko", octets_diversite / 1e3)
    log.info("   - Durée totale : %.2f s", time.perf_counter() - debut)
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
