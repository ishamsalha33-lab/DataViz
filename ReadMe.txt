======================================================================
         DOCUMENTATION TECHNIQUE : PROJET "OBJECTIF NASA"
             Pipeline ETL & Dashboard de Datavisualisation
======================================================================

Ce projet met en place une architecture complète de traitement de 
données (Pipeline ETL) couplée à une interface web interactive. Il 
extrait les données en temps réel de l'API de la NASA concernant les 
astéroïdes approchant la Terre, les transforme, les stocke dans une 
base de données MySQL, puis les restitue sous forme de graphiques.

----------------------------------------------------------------------
🎯 PROBLÉMATIQUE DU PROJET
----------------------------------------------------------------------
« Quels sont les astéroïdes qui frôlent la Terre cette semaine, et 
comment est calculé leur niveau de dangerosité ? »

----------------------------------------------------------------------
🛠️ 1. ARCHITECTURE & STACK TECHNIQUE
----------------------------------------------------------------------
L'application repose sur une architecture en 3 couches distinctes :

* Extraction & Transformation (ETL) : Python 3 (requests, pandas)
* Stockage (Persistance des données)  : MySQL
* Restitution & Datavisualisation   : Streamlit et Plotly

Schéma des flux :
  [ API NASA ] 
       │  (Extraction JSON via Requests)
       ▼
 [ Script Python ETL ] ──(Transformation & Nettoyage Pandas)
       │
       ▼
  [ Base MySQL ] 
       │  (Requêtes SQL de lecture)
       ▼
 [ Dashboard Streamlit ] ──(Visualisation interactive Plotly)

----------------------------------------------------------------------
📦 2. PRÉREQUIS ET INSTALLATION
----------------------------------------------------------------------
1. Dépendances Python :
   Exécuter la commande suivante dans le terminal :
   pip install requests pandas mysql-connector-python streamlit plotly

2. Configuration de la Base de Données (SQL) :
   Créer la base et la table avec le script suivant :

   CREATE DATABASE IF NOT EXISTS nasa_db;
   USE nasa_db;

   CREATE TABLE IF NOT EXISTS asteroides (
       id VARCHAR(50) PRIMARY KEY,
       nom VARCHAR(100),
       date_approche DATE,
       diametre_min_metres FLOAT,
       diametre_max_metres FLOAT,
       vitesse_km_h FLOAT,
       distance_terre_km FLOAT,
       est_dangereux BOOLEAN
   );

----------------------------------------------------------------------
📂 3. STRUCTURE DU PROJET
----------------------------------------------------------------------
Le projet est structuré de manière modulaire autour de deux fichiers :
* etl_nasa.py : Gère l'ingestion, le nettoyage et le chargement (MySQL).
* app.py      : Gère l'interface graphique utilisateur et les graphes.

----------------------------------------------------------------------
⚙️ 4. FONCTIONNEMENT DES COMPOSANTS
----------------------------------------------------------------------
A. Le Pipeline ETL (etl_nasa.py)
   * EXTRACT : Requête HTTP GET sur l'API NeoWS de la NASA pour 
     récupérer les objets géocroiseurs sur une fenêtre de 7 jours.
   * TRANSFORM : Extraction des variables clés du JSON imbriqué, 
     arrondi et conversion des unités (vitesses en km/h, distances 
     en km, diamètres en mètres) via un DataFrame Pandas.
   * LOAD : Insertion des données dans MySQL en mode "Upsert" 
     (ON DUPLICATE KEY UPDATE) pour éviter les doublons.

B. Le Dashboard Web (app.py)
   L'interface se connecte à MySQL et structure les analyses :
   * KPIs : Volume total, objets en alerte, et record de vitesse.
   * TOP 5 PROXIMITÉ : Graphique à barres isolant les objets les plus 
     proches pour illustrer la notion de "frôlement".
   * MATRICE DES MENACES : Graphe de dispersion (Distance vs Vitesse). 
     La taille des bulles (diamètre) et la couleur (Vert=Sûr, Rouge=
     Dangereux) expliquent visuellement les critères de la NASA.
   * DISTRIBUTION & RARETÉ : Un anneau et un histogramme prouvent que 
     les objets géants et dangereux sont très minoritaires.

----------------------------------------------------------------------
🚀 5. DÉPLOIEMENT ET UTILISATION
----------------------------------------------------------------------
Étape 1 : Initialisation ou mise à jour manuelle des données
          python etl_nasa.py
          (Note: Un bouton de synchronisation est aussi disponible 
          directement sur l'interface web).

Étape 2 : Lancement de l'application Web
          streamlit run app.py

L'application s'ouvre automatiquement à l'adresse : http://localhost:8501
======================================================================