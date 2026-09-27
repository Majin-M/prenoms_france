
from pathlib import Path
import hashlib
import shutil
import urllib.request

import duckdb

URL = "https://www.insee.fr/fr/statistiques/fichier/8595130/prenoms-2025.parquet"
PARQUET = Path("data/prenoms-2025.parquet")
DB = Path("data/prenoms.duckdb")
COLONNES_ATTENDUES = {"sexe", "prenom", "periode", "valeur", "rang",
                      "niveau_geographique", "geographie"}

class SchemaError(ValueError):
    """Le fichier ne contient pas les colonnes attendues."""
    pass

def telecharger(url: str, dest: Path, forcer: bool = False) -> Path:
    if dest.is_file() and not forcer :                      # le fichier existe déjà et on ne force pas
        print("Fichier déjà présent, pas de téléchargement")
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(".part")

    print(f"Téléchargement de {url}")
    try:
        with urllib.request.urlopen(url, timeout=120) as reponse, tmp.open("wb") as sortie:
            shutil.copyfileobj(reponse, sortie)
    except Exception:
        tmp.unlink(missing_ok=True)   # on nettoie le fichier incomplet
        raise     

    tmp.replace(dest)                         # renommer tmp en dest
    return dest

def empreinte(fichier: Path) -> str:
    h = hashlib.sha256()
    with fichier.open("rb") as f:
        for bloc in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloc)
    return h.hexdigest()

def verifier_schema(con, fichier: Path) -> None:
    resultat = con.execute(
        f"DESCRIBE SELECT * FROM read_parquet('{fichier.as_posix()}')"
    ).fetchall()
    colonnes = {row[0].lower() for row in resultat}        # un set des noms de colonnes, en minuscules
    manquantes = COLONNES_ATTENDUES - colonnes       # les colonnes attendues absentes du fichier
    if manquantes:
        raise SchemaError(f"Colonnes manquantes : {sorted(manquantes)}")


def charger(con, fichier: Path, sha256_source: str) -> int:
    """Crée raw.prenoms à partir du fichier et renvoie le nombre de lignes."""
    con.execute("CREATE SCHEMA IF NOT EXISTS raw")
    con.execute(f"""
        CREATE OR REPLACE TABLE raw.prenoms AS
        SELECT *,
            CURRENT_TIMESTAMP AS _loaded_at,
            ? AS _source_sha256
        FROM read_parquet('{fichier.as_posix()}')
    """, (sha256_source,))
    return con.execute("SELECT count(*) FROM raw.prenoms").fetchone()[0]




def main() -> None:
    telecharger(URL, PARQUET)
    sha256_source = empreinte(PARQUET)

    with duckdb.connect(str(DB)) as con:
        verifier_schema(con, PARQUET)
        lignes = charger(con, PARQUET, sha256_source)

    print(f"{lignes:,} lignes chargées dans raw.prenoms (sha256 {sha256_source[:12]}…)")


if __name__ == "__main__":
    main()