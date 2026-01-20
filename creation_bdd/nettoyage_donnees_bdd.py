# -*- coding: utf-8 -*-
"""
Transfert depuis tables existantes vers tables finales
@author: laude
"""

import mysql.connector
import re

# Connexion à la bdd
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "********",
    "database": "resclaves"
}
DEBUG = False  # True = affiche les lignes au lieu d'écrire en base

conn = mysql.connector.connect(**MYSQL_CONFIG)
cursor = conn.cursor(dictionary=True)  # retourne les lignes comme dict pour plus facile à mapper


# Caches des lieux (évite doublons)
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
        lieux_cache[nom_lieu] = res["id_lieu"]
        return res["id_lieu"]

    if DEBUG:
        print(f"[DEBUG] Nouveau lieu détecté : {nom_lieu}")
        id_lieu = len(lieux_cache) + 1  # valeur fictive pour test
    else:
        cursor.execute("INSERT INTO lieu (nom_lieu) VALUES (%s)", (nom_lieu,))
        conn.commit()
        id_lieu = cursor.lastrowid

    lieux_cache[nom_lieu] = id_lieu
    return id_lieu


# Fonctions
def split_lieux(val):
    if not val:
        return []
    separators = [" à ", " - ", " vers ", ",", " puis ", " et "]
    for sep in separators:
        if sep in val:
            return [v.strip() for v in val.split(sep)]
    return [val.strip()]

def clean_text(val):
    if val is None:
        return None
    val = str(val).strip()
    if val.lower() in ["non spécifié", "", "n/a"]:
        return None
    return val


def clean_id_auteur(val):
    if not val:
        return None
    # cherche tous les chiffres dans la chaîne
    match = re.search(r'\d+', str(val))
    if match:
        return int(match.group())  # renvoie 15 pour "A15"
    return None



# Insertion des auteurs
cursor.execute("SELECT * FROM tab_auteurs")
tab_auteurs = cursor.fetchall()

for row in tab_auteurs:
    raw_id = row.get("id_auteur")
    id_auteur = clean_id_auteur(raw_id)
    nom = row.get("nom")
    date_naissance = row.get("naissance")
    lieu_naissance = row.get("lieu_naissance")
    date_deces = row.get("deces")
    lieu_deces = row.get("lieu_deces")
    moyen_lib = row.get("moyen_lib")
    origine_parents = row.get("origine_parents")
    militant_abolitionniste = row.get("militant_abolitionniste")
    particularites = row.get("particularites")
    plrs_recits_raw = row.get("plrs_recits")  # récupère la valeur
    
    if plrs_recits_raw is None:
        plrs_recits = None
    else:
        plrs_recits_raw = str(plrs_recits_raw).strip().lower()  # normalise
        if plrs_recits_raw == "oui":
            plrs_recits = 1
        elif plrs_recits_raw == "non":
            plrs_recits = 0
        else:
            plrs_recits = None  # pour les valeurs inattendues
            
    op_source = row.get("op_source")

    if DEBUG:
        print(f"[DEBUG] Auteur: ID={id_auteur}, Nom={nom}, Naissance={date_naissance}, Lieu={lieu_naissance}, Deces={date_deces}, Lieu deces={lieu_deces}")
    else:
        cursor.execute(
            """
            INSERT INTO auteur (id_auteur, nom, annee_naissance, lieu_naissance, annee_deces, lieu_deces, ap_1865, moyen_lib, origine_parents, militant_abolitionniste, particularites, plrs_recits, op_source)
            VALUES (%s, %s, %s, %s, %s, %s, 0, %s, %s, %s, %s, %s, %s)
            """,
            (id_auteur, nom, date_naissance, lieu_naissance, date_deces, lieu_deces, moyen_lib, origine_parents, militant_abolitionniste, particularites, plrs_recits, op_source)
        )


# Insertion lieux de vie libre
for row in tab_auteurs:
    raw_id = row.get("id_auteur")
    id_auteur = clean_id_auteur(raw_id)
    lieux_vie = clean_text(row.get("lieuvie_ap_lib"))
    for ordre, lieu in enumerate(split_lieux(lieux_vie), start=1):
        id_lieu = get_or_create_lieu(lieu)
        if DEBUG:
            print(f"[DEBUG] Lieu de vie libre: Auteur={id_auteur}, Ordre={ordre}, Lieu={lieu}, id_lieu={id_lieu}")
        else:
            cursor.execute(
                "INSERT INTO lieu_vie_libre (id_auteur, id_lieu, ordre) VALUES (%s, %s, %s)",
                (id_auteur, id_lieu, ordre)
            )


# Insertion lieux d'esclavages
for row in tab_auteurs:
    raw_id = row.get("id_auteur")
    id_auteur = clean_id_auteur(raw_id)
    lieux_esclavage = clean_text(row.get("lieu_esclavage"))
    for ordre, lieu in enumerate(split_lieux(lieux_esclavage), start=1):
        id_lieu = get_or_create_lieu(lieu)
        if DEBUG:
            print(f"[DEBUG] Lieu esclavage: Auteur={id_auteur}, Ordre={ordre}, Lieu={lieu}, id_lieu={id_lieu}")
        else:
            cursor.execute(
                "INSERT INTO lieu_esclavage (id_auteur, id_lieu, ordre) VALUES (%s, %s, %s)",
                (id_auteur, id_lieu, ordre)
            )


# Insertion récits
cursor.execute("SELECT * FROM tab_recits_v3")
tab_recits = cursor.fetchall()

for row in tab_recits:
    raw_id = row.get("id_auteur")
    id_auteur = clean_id_auteur(raw_id)
    annee_publi = row.get("date_publi")
    lieu_publi = row.get("lieu_publi")
    id_recit = int(row.get("id_recit"))
    titre= row.get("titre")
    mode_publi = row.get("mode_publi")
    type_recit = row.get("type_recit")
    historiographie = row.get("historiographie")
    preface_blanc = row.get("preface_blanc")
    details_preface = row.get("details_preface")
    scribe_auteur = row.get("scribe_auteur")
    lien_recit = row.get("lien_recit")
    debut_titre = row.get("debut_titre")

    
    if not annee_publi and not lieu_publi:
        continue

    if DEBUG:
        print(f"[DEBUG] Recit: Auteur={id_auteur}, id_recit={id_recit}, Annee={annee_publi}, Lieu={lieu_publi}")
    else:
        cursor.execute(
            """
            INSERT INTO recit 
                        (id_recit, annee_publi, lieu_publi, titre, mode_publi, type_recit, historiographie, preface_blanc, details_preface, scribe_editeur, lien_recit, debut_titre) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (id_recit, annee_publi, lieu_publi, titre, mode_publi, type_recit, historiographie, preface_blanc, details_preface, scribe_auteur, lien_recit, debut_titre)
        )
        conn.commit()

        # Lien auteur -> recit
        cursor.execute(
            "INSERT INTO ecrit (id_auteur, id_recit) VALUES (%s, %s)",
            (id_auteur, id_recit)
        )


# Commit et déconnexion de la bdd
if not DEBUG:
    conn.commit()
cursor.close()
conn.close()

if DEBUG:
    print("\n[DEBUG] Mode test terminé. Les données ne sont pas encore écrites en base.")
else:
    print("\n[INFO] Import terminé.")
