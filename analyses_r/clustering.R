
# Clustering récits d'esclaves

# ---- 1. Packages ----
library(DBI)
library(RMySQL)
library(dplyr)
library(tidyr)
library(factoextra)
library(cluster)
library(sf)
library(FactoMineR)
library(ggplot2)
library(leaflet)
library(RColorBrewer)

# ---- 2. Connexion MySQL ----
con <- dbConnect(
  RMySQL::MySQL(),
  dbname = "resclaves",
  host = "localhost",
  user = "root",
  password = "********"
)

# ---- 3. Chargement des tables ----
tab_recits_v3 <- dbReadTable(con, "tab_recits_v3")
tab_auteurs   <- dbReadTable(con, "tab_auteurs")
points        <- dbReadTable(con, "points")
recit_poly        <- dbReadTable(con, "recit_poly")

# ---- 4. Fusion des données ----
data <- tab_recits_v3 %>%
  left_join(tab_auteurs, by = "id_auteur") %>%
  left_join(points %>% select(id_recit, ville, WKT), by = "id_recit")

# ---- 5. Nettoyage / sélection des variables ----
data_clean <- data %>%
  select(id_recit, type_recit, mode_publi, preface_blanc, militant_abolitionniste,
         plrs_recits, ville, WKT) %>%
  mutate(across(where(is.character), ~replace_na(., "Inconnu")))

# ---- 6. Encodage catégoriel ----
data_facto <- data_clean %>%
  select(type_recit, mode_publi, preface_blanc, militant_abolitionniste, plrs_recits) %>%
  mutate(across(everything(), as.factor))
data_num <- model.matrix(~ . - 1, data = data_facto)

# ---- 7. Clustering socio-historique ----
set.seed(123)
k_soc <- kmeans(data_num, centers = 4, nstart = 20)
data_clean$cluster_soc <- k_soc$cluster

# ---- 8. Clustering géographique ----
points_sf <- data_clean %>%
  filter(!is.na(WKT)) %>%
  st_as_sf(wkt = "WKT", crs = 4326, remove = FALSE)

coords <- st_coordinates(points_sf)
km_geo <- kmeans(coords, centers = 5)
points_sf$cluster_geo <- km_geo$cluster

# ---- 9. Fusion des deux clusters ----
data_final <- points_sf %>%
  mutate(cluster_mix = paste0("S", cluster_soc, "_G", cluster_geo))

# ---- 10. Visualisation des clusters ----
fviz_cluster(k_soc, data = data_num, geom = "point", main = "Clustering socio-historique des récits")

fviz_cluster(km_geo, data = data_num, geom = "point", main = "Clustering géographique des récits")


tab_recits_v3 %>%
  mutate(decennie = floor(as.numeric(date_publi) / 10) * 10) %>%
  count(decennie) %>%
  ggplot(aes(x = decennie, y = n)) +
  geom_col(fill = "steelblue") +
  labs(title = "Nombre de récits publiés par décennie", x = "Décennie", y = "Nombre de récits")


tab_recits_v3 %>%
  count(preface_blanc, type_recit) %>%
  ggplot(aes(x = type_recit, y = n, fill = preface_blanc)) +
  geom_col(position = "dodge") +
  labs(title = "Préfaces blanches selon le type de récit", x = "Type de récit", y = "Nombre")



# ---- 12. Déconnexion ----
dbDisconnect(con)

