USE resclaves;


-- Table auteur
CREATE TABLE IF NOT EXISTS auteur (
    id_auteur INT PRIMARY KEY,
    nom VARCHAR(255),
    annee_naissance VARCHAR(50),
    lieu_naissance VARCHAR(255),
    annee_deces VARCHAR(50),
    lieu_deces VARCHAR(255),
    ap_1865 TINYINT(1) DEFAULT 0,
	moyen_lib VARCHAR(255),
	origine_parents VARCHAR(255),
	militant_abolitionniste VARCHAR(255),
	particularites VARCHAR(255),
	plrs_recits TINYINT(1) DEFAULT 0,
	op_source VARCHAR(255);
);

-- Table lieu
CREATE TABLE IF NOT EXISTS lieu (
    id_lieu INT AUTO_INCREMENT PRIMARY KEY,
    nom_lieu VARCHAR(255) UNIQUE,
    ville_lieu VARCHAR(255),
    comte_lieu VARCHAR(255),
    pays_lieu VARCHAR(255)
);

-- Table lieu_vie_libre
CREATE TABLE IF NOT EXISTS lieu_vie_libre (
    id_auteur INT,
    id_lieu INT,
    ordre INT,
    PRIMARY KEY (id_auteur, id_lieu, ordre),
    FOREIGN KEY (id_auteur) REFERENCES auteur(id_auteur),
    FOREIGN KEY (id_lieu) REFERENCES lieu(id_lieu)
);

-- Table lieu_esclavage
CREATE TABLE IF NOT EXISTS lieu_esclavage (
    id_auteur INT,
    id_lieu INT,
    ordre INT,
    PRIMARY KEY (id_auteur, id_lieu, ordre),
    FOREIGN KEY (id_auteur) REFERENCES auteur(id_auteur),
    FOREIGN KEY (id_lieu) REFERENCES lieu(id_lieu)
);

-- Table recit
CREATE TABLE IF NOT EXISTS recit (
    id_recit INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(500),
    annee_publi VARCHAR(50),
    lieu_publi VARCHAR(255),
    mode_publi VARCHAR(255),
    type_recit VARCHAR(50),
    historiographie VARCHAR(5000),
    preface_blanc VARCHAR(50),
    details_preface VARCHAR(255),
    scribe_editeur VARCHAR(255),
    lien_recit VARCHAR(500),
    debut_titre VARCHAR(500)
);

-- Table ecrit
CREATE TABLE IF NOT EXISTS ecrit (
    id_auteur INT,
    id_recit INT,
    PRIMARY KEY(id_auteur, id_recit),
    FOREIGN KEY(id_auteur) REFERENCES auteur(id_auteur),
    FOREIGN KEY(id_recit) REFERENCES recit(id_recit)
);



CREATE TABLE lieu_n_d(
   id_auteur INT,
   id_lieu INT,
   naissance_deces VARCHAR(50),
   PRIMARY KEY(id_auteur, id_lieu),
   FOREIGN KEY(id_auteur) REFERENCES auteur(id_auteur),
   FOREIGN KEY(id_lieu) REFERENCES lieu(id_lieu)
);
