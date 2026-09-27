"""
=============================================================================
Ingestion : Fichier des prénoms INSEE → DuckDB (couche raw)
=============================================================================
Objectif :
    Télécharge le fichier Parquet de l'INSEE (édition juillet 2026,
    naissances 1900-2025), vérifie son schéma et le charge dans la table
    raw.prenoms, avec la date de chargement et l'empreinte sha256 du fichier.

Utilisation :
    python ingest.py

Attention :
    La table raw.prenoms est entièrement remplacée à chaque exécution.
    La base data/prenoms.duckdb ne doit pas être ouverte par un autre programme.
=============================================================================
"""

from contextlib import contextmanager
from pathlib import Path
import hashlib
import logging
import shutil
import sys
import time
import urllib.request

import duckdb

URL = "https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet"
RACINE = Path(__file__).resolve().parent
PARQUET = RACINE / "data" / "prenoms-2025.parquet"
DB = RACINE / "data" / "prenoms.duckdb"
LOGS = RACINE / "logs"
COLONNES_ATTENDUES = {"sexe", "prenom", "periode", "valeur", "rang",
                      "niveau_geographique", "geographie"}

log = logging.getLogger("ingest")


class SchemaError(ValueError):
    """Le fichier ne contient pas les colonnes attendues."""


def configurer_logs() -> None:
    """Écrit les messages à la fois dans le terminal et dans logs/ingest.log."""
    LOGS.mkdir(exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(LOGS / "ingest.log", encoding="utf-8"),
        ],
    )


def formater(nombre: int) -> str:
    """Formate un entier à la française : 6622949 -> '6 622 949'."""
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


def telecharger(url: str, dest: Path, forcer: bool = False) -> Path:
    """Télécharge le fichier source, sauf s'il est déjà présent et que forcer est faux."""
    if dest.is_file() and not forcer:
        log.info("Fichier déjà présent, pas de téléchargement")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")

    log.info("Téléchargement de %s", url)
    try:
        with urllib.request.urlopen(url, timeout=120) as reponse, tmp.open("wb") as sortie:
            shutil.copyfileobj(reponse, sortie)
    except Exception:
        tmp.unlink(missing_ok=True)  # sinon le prochain essai partirait d'un fichier tronqué
        raise

    tmp.replace(dest)  # renommage atomique : jamais de fichier incomplet sous le nom final
    return dest


def empreinte(fichier: Path) -> str:
    """Calcule l'empreinte sha256 du fichier, pour savoir quelle version a été chargée."""
    h = hashlib.sha256()
    with fichier.open("rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):  # par blocs de 1 Mo, pour ne pas tout charger en mémoire
            h.update(bloc)
    return h.hexdigest()


def verifier_schema(con, fichier: Path) -> None:
    """Lève SchemaError si une colonne attendue manque dans le fichier."""
    resultat = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{fichier.as_posix()}')"
    ).fetchall()
    colonnes = {row[0].lower() for row in resultat}  # SQL ignore la casse des noms : on compare en minuscules
    manquantes = COLONNES_ATTENDUES - colonnes
    if manquantes:
        raise SchemaError(f"Colonnes manquantes : {sorted(manquantes)}")


def charger(con, fichier: Path, sha256_source: str) -> int:
    """Crée raw.prenoms à partir du fichier et renvoie le nombre de lignes."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    log.info(">> Remplacement de la table raw.prenoms depuis %s", fichier.name)
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.prenoms AS
        SELECT *,
            CURRENT_TIMESTAMP AS _loaded_at,
            ? AS _source_sha256
        FROM read_parquet('{fichier.as_posix()}')
    """, (sha256_source,))
    return con.execute("SELECT count(*) FROM raw.prenoms").fetchone()[0]


def main() -> int:
    configurer_logs()
    log.info("=" * 60)
    log.info("Ingestion du fichier des prénoms INSEE")
    log.info("=" * 60)
    debut = time.perf_counter()

    try:
        with etape("Téléchargement"):
            telecharger(URL, PARQUET)
        with etape("Calcul de l'empreinte"):
            sha256_source = empreinte(PARQUET)
        with duckdb.connect(str(DB)) as con:
            with etape("Vérification du schéma"):
                verifier_schema(con, PARQUET)
            with etape("Chargement de raw.prenoms"):
                lignes = charger(con, PARQUET, sha256_source)
    except Exception:
        log.error("=" * 60)
        log.error("Ingestion interrompue après %.2f s, voir le détail ci-dessus",
                  time.perf_counter() - debut)
        log.error("=" * 60)
        return 1

    log.info("=" * 60)
    log.info("Ingestion terminée")
    log.info("   - Lignes chargées : %s", formater(lignes))
    log.info("   - Empreinte source : %s…", sha256_source[:12])
    log.info("   - Durée totale : %.2f s", time.perf_counter() - debut)
    log.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
