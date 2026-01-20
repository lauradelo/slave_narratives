# -*- coding: utf-8 -*-
"""
Import auteurs + lieux (vie libre et esclavage) depuis CSV vers MySQL
@author: laude
"""

import pandas as pd
import mysql.connector


# Fonctions
def clean_text(val):
    if pd.isna(val):
        return None
    val = str(val).strip()
    if "Non spécifié" in val or val == "":
        return None
    return val

def split_lieux(val):
    if not val:
        return []
    separators = [" à ", " - ", " vers "]
    for sep in separators:
        if sep in val:
            return [v.strip() for v in val.split(sep)]
    return [val.strip()]


# Lecture csv
CSV_FILE = "ap_1865.csv"
df = pd.read_csv(CSV_FILE, sep=";")
df = df.applymap(clean_text)


# Connexion à la bdd
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "********",
    "database": "resclaves"
}
DEBUG = False
conn = mysql.connector.connect(**MYSQL_CONFIG)
cursor = conn.cursor()


# Cache les lieux (évite doublons)
lieux_cache = {}

def get_or_create_lieu(nom_lieu):
    if not nom_lieu:
        return None
    nom_lieu = nom_lieu.strip()
    if nom_lieu in lieux_cache:
        return lieux_cache[nom_lieu]

    cursor.execute("SELECT id_lieu FROM lieu WHERE nom_lieu = %s", (nom_lieu,))
    res = cursor.fetchone()
    if res:
        lieux_cache[nom_lieu] = res[0]
        return res[0]

    if DEBUG:
        print(f"[DEBUG] Nouveau lieu détecté : {nom_lieu}")
        id_lieu = len(lieux_cache) + 1  # valeur fictive pour test
    else:
        cursor.execute("INSERT INTO lieu (nom_lieu) VALUES (%s)", (nom_lieu,))
        conn.commit()
        id_lieu = cursor.lastrowid

    lieux_cache[nom_lieu] = id_lieu
    return id_lieu


# Fonction d'insertions des lieux
def insert_lieux(df, col_lieu_csv, table_sql):
    for _, row in df.iterrows():
        id_auteur = int(row["id_auteur"])
        lieux = split_lieux(row[col_lieu_csv])
        for ordre, nom_lieu in enumerate(lieux, start=1):
            id_lieu = get_or_create_lieu(nom_lieu)
            if id_lieu:
                if DEBUG:
                    print(f"[DEBUG] Auteur={id_auteur}, Table={table_sql}, Ordre={ordre}, Lieu='{nom_lieu}', id_lieu={id_lieu}")
                else:
                    cursor.execute(
                        f"INSERT INTO {table_sql} (id_auteur, id_lieu, ordre) VALUES (%s, %s, %s)",
                        (id_auteur, id_lieu, ordre)
                    )
                    
                    
# Fonction d'insertion des récits
def insert_recits(df, debug=True):
    for _, row in df.iterrows():
        id_auteur = int(row["id_auteur"])
        annee_publi = row.get("date_publication")
        lieu_publi = row.get("lieu_publication")

        # Si pas de date et pas de lieu, on ignore
        if not annee_publi and not lieu_publi:
            continue

        if debug:
            # Mode test : on simule un id_recit
            id_recit = _ + 1
            print(f"[DEBUG] Recit auteur={id_auteur}, id_recit={id_auteur}, annee_publi={annee_publi}, lieu_publi={lieu_publi}")
        else:
            # Insertion dans recit
            cursor.execute(
                """
                INSERT INTO recit (id_recit, annee_publi, lieu_publi)
                VALUES (%s, %s, %s)
                """,
                (id_auteur, annee_publi, lieu_publi)
            )
            conn.commit()

            # Lien avec l'auteur
            cursor.execute(
                "INSERT INTO ecrit (id_auteur, id_recit) VALUES (%s, %s)",
                (id_auteur, id_auteur)
            )



# Insertions des auteurs
for _, row in df.iterrows():
    id_auteur = int(row["id_auteur"])
    nom = row["nom"]
    date_naissance = row["date_naissance"]
    lieu_naissance = row["lieu_naissance"]
    date_deces = row["date_mort"]
    lieu_deces = row["lieu_deces"]

    if DEBUG:
        print(f"[DEBUG] Auteur: ID={id_auteur}, Nom='{nom}', Naissance={date_naissance}, Mort={date_deces}, lieu_naissance ={lieu_naissance}, lieu_mort ={lieu_deces}")
    else:
        cursor.execute(
            """
            INSERT INTO auteur (id_auteur, nom, annee_naissance, lieu_naissance, annee_deces, lieu_deces, ap_1865)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
            """,
            (id_auteur, nom, date_naissance, lieu_naissance, date_deces, lieu_deces)
        )


# Insertion des lieux de vie libre
insert_lieux(df, "lieu_vie_libre", "lieu_vie_libre")


# Insertions des lieux d'esclavage
insert_lieux(df, "lieu_esclavagisme", "lieu_esclavage")

# Mode test : affiche seulement
insert_recits(df, debug=False)



# Commit et déconnexion de la bdd
if not DEBUG:
    conn.commit()
cursor.close()
conn.close()

if DEBUG:
    print("\n[DEBUG] Mode test terminé. Les données ne sont pas encore écrites en base.")
else:
    print("\n[INFO] Import terminé.")







