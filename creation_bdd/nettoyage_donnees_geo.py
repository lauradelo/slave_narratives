# -*- coding: utf-8 -*-
"""
Mise à jour des colonnes nom_ville, nom_etat, nom_comté, nom_pays
@author: laude
"""

import mysql.connector
import re
import spacy



TABLE = "lieu"
COLONNE_LIEU = "nom_lieu"

# Listes de référence
ETATS_US = {
    "alabama", "alaska", "arizona", "arkansas", "californie",
    "caroline du nord", "caroline du sud", "colorado", "connecticut",
    "dakota du nord", "dakota du sud", "delaware", "floride", "géorgie",
    "hawaï", "idaho", "illinois", "indiana", "iowa", "kansas", "kentucky",
    "louisiane", "maine", "maryland", "massachusetts", "michigan",
    "minnesota", "mississippi", "missouri", "montana", "nebraska",
    "nevada", "new hampshire", "new jersey", "new york",
    "nouveau-mexique", "ohio", "oklahoma", "oregon", "pennsylvanie",
    "rhode island", "tennessee", "texas", "utah", "vermont",
    "virginie du nord", "virginie du sud", "virginie de l'ouest", "virginie ouest",
    "virginie", "virginie occidentale", "washington", "wisconsin", "wyoming"
}

PAYS = {
    "canada", "brésil", "australie", "angleterre",
    "nigéria", "antigua & barbuda", "bermudes"
}

CONTINENTS = {
    "afrique", "europe", "asie", "amérique", "océanie"
}


# NLP
nlp = spacy.load("fr_core_news_sm")


# Fonctions d'extraction
def extraire_county_et_etat(texte):
    match = re.search(r"(.+?)\s+county\s+(.+)", texte, re.IGNORECASE)
    if match:
        return {
            "nom_comte": match.group(1).strip(),
            "nom_etat": match.group(2).strip(),
            "nom_ville": None,
            "nom_pays": None,
            "nom_lieu": texte
        }
    return None

def extraire_ville_et_etat(texte):
    texte_clean = texte.strip()
    texte_lower = texte_clean.lower()

    # --- État + (détails)
    for etat in sorted(ETATS_US, key=len, reverse=True):
        if texte_lower.startswith(etat + " ("):
            return {
                "nom_ville": None,
                "nom_etat": etat.title(),
                "nom_comte": None,
                "nom_pays": None,
                "nom_lieu": texte_clean
            }

    # --- Ville (État)
    match_parenthese = re.search(r"\(([^)]+)\)", texte_lower)
    if match_parenthese:
        contenu = match_parenthese.group(1).strip()
        for etat in ETATS_US:
            if contenu == etat:
                ville = texte_clean.split("(")[0].strip()
                return {
                    "nom_ville": ville,
                    "nom_etat": etat.title(),
                    "nom_comte": None,
                    "nom_pays": None,
                    "nom_lieu": texte_clean
                }

    # --- Ville État
    for etat in sorted(ETATS_US, key=len, reverse=True):
        pattern = rf"(?:^|\s|,|\()({re.escape(etat)})(?:$|[.,)])"
        match = re.search(pattern, texte_lower)
        if match:
            start = match.start(1)
            ville = texte_clean[:start].strip(" ,(")
            return {
                "nom_ville": ville if ville else None,
                "nom_etat": etat.title(),
                "nom_comte": None,
                "nom_pays": None,
                "nom_lieu": texte_clean
            }

    return None

def classifier_lieu(texte):
    t = texte.strip()
    t_lower = t.lower()

    # County
    res = extraire_county_et_etat(t)
    if res:
        return res

    # Ville + État
    res = extraire_ville_et_etat(t)
    if res:
        return res

    # Pays
    for p in PAYS:
        if p in t_lower:
            return {
                "nom_ville": None,
                "nom_etat": None,
                "nom_comte": None,
                "nom_pays": p.title(),
                "nom_lieu": t
            }

    # Continent
    for c in CONTINENTS:
        if c in t_lower:
            return {
                "nom_ville": None,
                "nom_etat": None,
                "nom_comte": None,
                "nom_pays": None,
                "continent": c.title(),
                "nom_lieu": t
            }

    # NLP fallback
    doc = nlp(t)
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC"):
            return {
                "nom_ville": t,
                "nom_etat": None,
                "nom_comte": None,
                "nom_pays": None,
                "nom_lieu": t
            }

    # fallback général
    return {
        "nom_ville": None,
        "nom_etat": None,
        "nom_comte": None,
        "nom_pays": None,
        "nom_lieu": t
    }


# Exectution et maj de bdd
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "********",
    "database": "resclaves"
}
conn = mysql.connector.connect(**DB_CONFIG)
cursor = conn.cursor(dictionary=True)

# Récupérer seulement les lieux avec id_lieu >= 169
cursor.execute(f"SELECT id_lieu, {COLONNE_LIEU} FROM {TABLE} WHERE id_lieu >= 169")
rows = cursor.fetchall()

for row in rows:
    lieu = row[COLONNE_LIEU]
    id_row = row["id_lieu"]
    resultat = classifier_lieu(lieu)

    update_sql = f"""
        UPDATE {TABLE}
        SET comte_lieu = %s,
            etat_lieu = %s,
            ville_lieu = %s,
            pays_lieu = %s
        WHERE id_lieu = %s
    """
    cursor.execute(update_sql, (
        resultat.get("nom_comte"),
        resultat.get("nom_etat"),
        resultat.get("nom_ville"),
        resultat.get("nom_pays"),
        id_row
    ))

conn.commit()
cursor.close()
conn.close()

print("✅ Mise à jour terminée pour les lieux à partir de id_lieu 169 !")

