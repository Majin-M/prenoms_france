import duckdb
f="data/prenoms-2025.parquet"
print(duckdb.sql(f"DESCRIBE SELECT * FROM '{f}'"))
print(duckdb.sql(f"SELECT * FROM'{f}' LIMIT 10"))
print(duckdb.sql(f"""
    SELECT NIVEAU_GEOGRAPHIQUE, count(*) AS lignes
    FROM '{f}' GROUP BY 1  
                 """))
print(duckdb.sql(f"""
    SELECT PERIODE as annee,
        SEXE as sexe,
        valeur as nombre
        FROM '{f}' WHERE PRENOM ='STEVEN' 
        AND   NIVEAU_GEOGRAPHIQUE = 'FRANCE' 
          ORDER BY annee, sexe
                 """))

print(duckdb.sql(f"""
    SELECT PERIODE, SEXE, PRENOM, VALEUR
    FROM '{f}'
    WHERE NIVEAU_GEOGRAPHIQUE = 'FRANCE'
        AND PERIODE IN ('1950', '2020')
        AND RANG = 1
    ORDER BY PERIODE, SEXE
                 """))
duckdb.sql(f"SUMMARIZE SELECT * FROM '{f}'").show()

print(duckdb.sql(f"""
    SELECT PRENOM, count(*) AS lignes, sum(VALEUR) AS naissances
    FROM '{f}'
    WHERE starts_with(PRENOM, '_')
    GROUP BY PRENOM
                """))

print(duckdb.sql(f"""
    SELECT PERIODE, count(*)
    FROM '{f}'
    WHERE try_cast(PERIODE AS INTEGER) IS NULL
    GROUP BY PERIODE
                """))

print(duckdb.sql(f"""
    SELECT PRENOM, SEXE, PERIODE, NIVEAU_GEOGRAPHIQUE, GEOGRAPHIE, count(*) AS n
    FROM '{f}'
    GROUP BY ALL
    HAVING count(*) > 1
                """))

print(duckdb.sql(f"""
    SELECT PERIODE, count(*)
    FROM '{f}'
    WHERE try_cast(PERIODE AS INTEGER) IS NULL
    GROUP BY PERIODE
                """))
print(duckdb.sql(f"SELECT count(*) FROM '{f}' WHERE VALEUR % 5 <> 0 OR VALEUR <= 0"))


print(duckdb.sql(f"SELECT count(DISTINCT periode) FROM '{f}'"))

print(duckdb.sql(f"""
    SELECT sum(valeur) AS naissances_dans_le_fichier
    FROM '{f}'
    WHERE niveau_geographique = 'FRANCE'
    AND periode = '2020'
  """))
