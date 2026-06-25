from datetime import datetime, timedelta
import mysql.connector
import pandas as pd
import requests

# --- CONFIGURATION ---
NASA_API_KEY = "F2cPNmGsepIDaPpECnUg4VWXHPDqtGLFJmATq9kd"
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "nasa_db",
}


# --- 1. EXTRACTION ---
def extraire_donnees():
    aujourdhui = datetime.now().date()
    dans_sept_jours = aujourdhui + timedelta(days=7)

    url = f"https://api.nasa.gov/neo/rest/v1/feed?start_date={aujourdhui}&end_date={dans_sept_jours}&api_key={NASA_API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        return response.json()["near_earth_objects"]
    else:
        print(f"Erreur API : {response.status_code}")
        return None


# --- 2. TRANSFORMATION ---
def transformer_donnees(donnees_brutes):
    liste_asteroides = []

    # Le JSON est classé par date, on boucle sur chaque date
    for date, asteroides_du_jour in donnees_brutes.items():
        for asteroide in asteroides_du_jour:
            # Extraction et nettoyage des données qui nous intéressent
            infos = {
                "id": asteroide["id"],
                "nom": asteroide["name"],
                "date_approche": date,
                "diametre_min_metres": round(
                    asteroide["estimated_diameter"]["meters"][
                        "estimated_diameter_min"
                    ],
                    2,
                ),
                "diametre_max_metres": round(
                    asteroide["estimated_diameter"]["meters"][
                        "estimated_diameter_max"
                    ],
                    2,
                ),
                "vitesse_km_h": round(
                    float(
                        asteroide["close_approach_data"][0][
                            "relative_velocity"
                        ]["kilometers_per_hour"]
                    ),
                    2,
                ),
                "distance_terre_km": round(
                    float(
                        asteroide["close_approach_data"][0]["miss_distance"][
                            "kilometers"
                        ]
                    ),
                    2,
                ),
  "est_dangereux": 1 if asteroide["is_potentially_hazardous_asteroid"] else 0,
            }
            liste_asteroides.append(infos)

    # On transforme la liste en DataFrame Pandas (plus facile à manipuler)
    df = pd.DataFrame(liste_asteroides)
    return df


# --- 3. CHARGEMENT (LOAD) ---
def charger_dans_mysql(df):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()

        # Requête SQL pour insérer ou mettre à jour si l'astéroïde existe déjà
        sql_query = """
        INSERT INTO asteroides (id, nom, date_approche, diametre_min_metres, diametre_max_metres, vitesse_km_h, distance_terre_km, est_dangereux)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            vitesse_km_h = VALUES(vitesse_km_h),
            distance_terre_km = VALUES(distance_terre_km),
            est_dangereux = VALUES(est_dangereux);
        """

        # Conversion du DataFrame en liste de tuples pour le batch insert
        valeurs = [tuple(x) for x in df.to_numpy()]

        cursor.executemany(sql_query, valeurs)
        conn.commit()

        print(
            f"Pipeline ETL réussie ! {cursor.rowcount} lignes synchronisées dans MySQL."
        )

    except mysql.connector.Error as err:
        print(f"Erreur MySQL : {err}")
    finally:
        if "conn" in locals() and conn.is_connected():
            cursor.close()
            conn.close()


# --- ENCHAÎNEMENT DE LA PIPELINE ---
if __name__ == "__main__":
    print("=== DÉMARRAGE DU PIPELINE ETL ===")

    donnees_brutes = extraire_donnees()

    if donnees_brutes:
        df_nettoye = transformer_donnees(donnees_brutes)
        print(f"Données transformées : {len(df_nettoye)} astéroïdes prêts.")

        # Optionnel : affiche un aperçu du tableau dans la console
        print(df_nettoye[["nom", "vitesse_km_h", "est_dangereux"]].head(3))

        charger_dans_mysql(df_nettoye)