
# Statistiques 

# Packages
library(dplyr)

# 2. Connexion MySQL
con <- dbConnect(
  RMySQL::MySQL(),
  dbname = "resclaves",
  host = "localhost",
  user = "root",
  password = "********"
)

# H1 — Continuité spatiale
continuite_spatiale <- trajets %>%
  summarise(
    naissance_esclavage = mean(naissance == esclavage1),
    esclavage_libre     = mean(esclavage1 == libre1),
    libre_deces         = mean(libre1 == deces)
  )

print("H1 — Continuité spatiale")
print(continuite_spatiale)


# H2 — Mobilité forcée vs choisie
mobilite_comparee <- trajets %>%
  mutate(
    mobilite_esclavage = naissance != esclavage1,
    mobilite_libre     = esclavage1 != libre1
  ) %>%
  summarise(
    taux_mobilite_esclavage = mean(mobilite_esclavage),
    taux_mobilite_vie_libre = mean(mobilite_libre)
  )

print("H2 — Mobilité forcée vs vie libre")
print(mobilite_comparee)


# H3 — Lieux d’attraction / départ
flux <- trajets %>%
  count(naissance, esclavage1, name = "n")

entrees <- flux %>%
  group_by(esclavage1) %>%
  summarise(entrees = sum(n), .groups = "drop")

sorties <- flux %>%
  group_by(naissance) %>%
  summarise(sorties = sum(n), .groups = "drop")

bilan_lieux <- full_join(
  entrees,
  sorties,
  by = c("esclavage1" = "naissance")
) %>%
  replace_na(list(entrees = 0, sorties = 0)) %>%
  mutate(
    lieu = esclavage1,
    bilan = entrees - sorties
  ) %>%
  arrange(desc(bilan))

print("H3 — Bilan entrée / sortie par lieu")
print(head(bilan_lieux, 10))


# H4 — Lieux de vie libre privilégiés
lieux_vie_libre <- trajets %>%
  count(libre1, name = "n_libre")

lieux_esclavage <- trajets %>%
  count(esclavage1, name = "n_esclave")

attractivite_libre <- lieux_vie_libre %>%
  left_join(lieux_esclavage,
            by = c("libre1" = "esclavage1")) %>%
  replace_na(list(n_esclave = 0)) %>%
  mutate(ratio = n_libre / (n_esclave + 1)) %>%
  arrange(desc(ratio))

print("H4 — Lieux attractifs après esclavage")
print(head(attractivite_libre, 10))


# H5 — Dispersion spatiale post-esclavage
dispersion <- trajets %>%
  summarise(
    nb_lieux_naissance = n_distinct(naissance),
    nb_lieux_esclavage = n_distinct(esclavage1),
    nb_lieux_libre     = n_distinct(libre1),
    nb_lieux_deces     = n_distinct(deces)
  )

print("H6 — Dispersion spatiale")
print(dispersion)



