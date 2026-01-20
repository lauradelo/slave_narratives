
# Viz trajets récits d'esclaves

# ---- 1. Packages ----
library(DBI)
library(dplyr)
library(tidyr)
library(stringi)
library(ggalluvial)
library(ggplot2)

# ---- 2. Connexion MySQL ----
con <- dbConnect(
  RMySQL::MySQL(),
  dbname = "resclaves",
  host = "localhost",
  user = "root",
  password = "********"
)

# ---- 3. Chargement des tables ----
auteurs <- dbReadTable(con, "auteur") %>%
  filter(ap_1865 == 0)  
# si 0 garde uniquement ceux avant 1865, si 1 inversement

lieux <- dbReadTable(con, "lieu") %>%
  mutate(
    lieu_utilisable = coalesce(
      stri_trans_general(tolower(comte_lieu), "Latin-ASCII"),
      stri_trans_general(tolower(ville_lieu), "Latin-ASCII"),
      stri_trans_general(tolower(nom_lieu), "Latin-ASCII"),
      stri_trans_general(tolower(pays_lieu), "Latin-ASCII"),
      "Inconnu"
    ) %>% stri_trim_both()
  )


# ---- 4.Construire les trajectoires filtrées ----
# Naissance et décès
trajets <- dbReadTable(con, "lieu_n_d") %>%
  filter(id_auteur %in% auteurs$id_auteur) %>%  # filtrer avant
  inner_join(lieux, by = "id_lieu") %>%
  select(id_auteur, naissance_deces, lieu_utilisable) %>%
  pivot_wider(names_from = naissance_deces, values_from = lieu_utilisable)

# Premier lieu d'esclavage
esclavage <- dbReadTable(con, "lieu_esclavage") %>%
  filter(id_auteur %in% auteurs$id_auteur) %>%
  inner_join(lieux, by = "id_lieu") %>%
  group_by(id_auteur) %>%
  summarise(esclavage1 = first(lieu_utilisable), .groups = "drop")

trajets <- trajets %>% left_join(esclavage, by = "id_auteur")

# Premier lieu de vie libre
vie_libre <- dbReadTable(con, "lieu_vie_libre") %>%
  filter(id_auteur %in% auteurs$id_auteur) %>%
  inner_join(lieux, by = "id_lieu") %>%
  group_by(id_auteur) %>%
  summarise(libre1 = first(lieu_utilisable), .groups = "drop")

trajets <- trajets %>%
  left_join(vie_libre, by = "id_auteur") %>%
  mutate(across(everything(), ~ifelse(is.na(.x), "Inconnu", .x)))


# ---- 5.Fonction pour réduire les catégories (compact) ----
# utile si l'on regroupe certains lieux (non fait avec les diagrammes alluvials du rapport)
reducer_categories <- function(vec, top_n = 10) {
  freq <- sort(table(vec), decreasing = TRUE)
  top_lieux <- names(freq)[1:min(top_n, length(freq))]
  vec2 <- ifelse(vec %in% top_lieux, vec, "Autres")
  return(vec2)
}

top_n <- 50  # nombre de lieux principaux à garder (50 = prends tous les lieux)

trajets <- trajets %>%
  mutate(
    naissance = reducer_categories(naissance, top_n),
    esclavage1 = reducer_categories(esclavage1, top_n),
    libre1 = reducer_categories(libre1, top_n),
    deces = reducer_categories(deces, top_n)
  )


# ---- 6.Compter les trajectoires ---- 
trajectoires_counts <- trajets %>%
  group_by(naissance, esclavage1, libre1, deces) %>%
  summarise(nb_auteurs = n(), .groups = "drop") %>%
  arrange(desc(nb_auteurs))


# ---- 7.Diagramme Alluvial ----
ggplot(trajectoires_counts,
       aes(axis1 = naissance, axis2 = esclavage1, axis3 = libre1, axis4 = deces,
           y = nb_auteurs)) +
  geom_alluvium(aes(fill = naissance), width = 0.06) +  # bandes fines
  geom_stratum(width = 0.06) +
  geom_text(stat = "stratum", aes(label = after_stat(stratum)), size = 2) +
  theme_minimal() +
  labs(title = "Trajectoires synthétiques des auteurs (avant 1865, compact)",
       y = "Nombre d'auteurs")

# ---- 12. Déconnexion ----
dbDisconnect(con)
