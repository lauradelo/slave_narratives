# -*- coding: utf-8 -*-
"""
Transfert des lieux de naissance et décès vers lieu et lieu_n_d
@author: laude
"""

import mysql.connector
import re


DEBUG = False  # True = affiche les lignes, False = écrit en base


# Connexion à la bdd
MYSQL_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "********",
    "database": "resclaves"
}
conn = mysql.connector.connect(**MYSQL_CONFIG)
cursor = conn.cursor(dictionary=True)


# Cache des lieux (évite doublons)
lieux_cache = {}

# On initialise le compteur à 168 pour les nouveaux lieux
nouveau_id_lieu = 169

def get_or_create_lieu(nom_lieu):
    """Retourne l'id_lieu si existant, sinon l'insère et retourne l'id"""
    global nouveau_id_lieu
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
        id_lieu = nouveau_id_lieu
        nouveau_id_lieu += 1
    else:
        cursor.execute("INSERT INTO lieu (id_lieu, nom_lieu) VALUES (%s, %s)", (nouveau_id_lieu, nom_lieu))
        conn.commit()
        id_lieu = nouveau_id_lieu
        nouveau_id_lieu += 1

    lieux_cache[nom_lieu] = id_lieu
    return id_lieu


def clean_text(val):
    """Nettoie la valeur texte"""
    if val is None:
        return None
    val = str(val).strip()
    if val.lower() in ["non spécifié", "", "n/a"]:
        return None
    return val

def clean_id_auteur(val):
    """Extrait l'ID numérique si la valeur contient autre chose"""
    if not val:
        return None
    match = re.search(r'\d+', str(val))
    if match:
        return int(match.group())
    return None


# Récupération des auteurs
cursor.execute("SELECT * FROM auteur")
tab_auteurs = cursor.fetchall()


# Insertion lieux de naissance/décès
for row in tab_auteurs:
    id_auteur = clean_id_auteur(row.get("id_auteur"))

    # --- Lieu de naissance ---
    lieu_naissance = clean_text(row.get("lieu_naissance"))
    if lieu_naissance:
        id_lieu = get_or_create_lieu(lieu_naissance)
        if id_lieu:
            if DEBUG:
                print(f"[DEBUG] Naissance: Auteur={id_auteur}, Lieu={lieu_naissance}, id_lieu={id_lieu}")
            else:
                cursor.execute(
                    "INSERT IGNORE INTO lieu_n_d (id_auteur, id_lieu, naissance_deces) VALUES (%s, %s, 'naissance')",
                    (id_auteur, id_lieu)
                )

    # --- Lieu de décès ---
    lieu_deces = clean_text(row.get("lieu_deces"))
    if lieu_deces:
        id_lieu = get_or_create_lieu(lieu_deces)
        if id_lieu:
            if DEBUG:
                print(f"[DEBUG] Décès: Auteur={id_auteur}, Lieu={lieu_deces}, id_lieu={id_lieu}")
            else:
                cursor.execute(
                    "INSERT IGNORE INTO lieu_n_d (id_auteur, id_lieu, naissance_deces) VALUES (%s, %s, 'deces')",
                    (id_auteur, id_lieu)
                )


# Commit et déconnexion de la bdd
if not DEBUG:
    conn.commit()
cursor.close()
conn.close()

if DEBUG:
    print("\n[DEBUG] Mode test terminé. Les données ne sont pas encore écrites en base.")
else:
    print("\n[INFO] Import terminé et base mise à jour.")
