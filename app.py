import mysql.connector
import pandas as pd
import plotly.express as px
import streamlit as st

import etl_nasa

# CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Objectif NASA - Analyse Avancée", page_icon="assets/logo.webp", layout="wide"
)

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "nasa_db",
}


def charger_donnees():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        query = "SELECT * FROM asteroides"
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            df["date_approche"] = pd.to_datetime(df["date_approche"]).dt.date
            df["Statut"] = df["est_dangereux"].map(
                {1: "⚠️ Potentiellement Dangereux", 0: "✅ Sûr"}
            )
        return df
    except Exception as e:
        st.error(f"Erreur MySQL : {e}")
        return pd.DataFrame()


# SIDEBAR
st.sidebar.title("Commandes")
if st.sidebar.button("Synchroniser la BDD avec la NASA", use_container_width=True):
    with st.spinner("Mise à jour MySQL..."):
        donnees_brutes = etl_nasa.extraire_donnees()
        if donnees_brutes:
            df_nettoye = etl_nasa.transformer_donnees(donnees_brutes)
            etl_nasa.charger_dans_mysql(df_nettoye)
            st.sidebar.success("BDD Synchronisée !")
            st.cache_data.clear()

df = charger_donnees()
if not df.empty:
    choix_danger = st.sidebar.radio(
        "Filtrer par dangerosité :", ("Tous", "Uniquement Dangereux", "Sûrs")
    )
    if choix_danger == "Uniquement Dangereux":
        df_filtre = df[df["est_dangereux"] == 1]
    elif choix_danger == "Sûrs":
        df_filtre = df[df["est_dangereux"] == 0]
    else:
        df_filtre = df.copy()
else:
    df_filtre = pd.DataFrame()

# CONTENU PRINCIPAL
st.title("Objectif NASA : Rapport d'Analyse des Menaces Spatiales")
st.markdown(
    "**Problématique d'étude :** *Quels sont les astéroïdes qui frôlent la Terre cette semaine, et comment est calculé leur niveau de dangerosité ?*"
)
st.markdown("---")

if not df_filtre.empty:
    # KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Astéroïdes dans la base MySQL", len(df_filtre))
    col2.metric("Objets Classés Dangereux", df_filtre["est_dangereux"].sum())
    col3.metric("Vitesse Record (km/h)", f"{df_filtre['vitesse_km_h'].max():,.2f}")

    st.markdown("---")

    # BLOC 1 : QUI NOUS FRÔLE LE PLUS PRÈS ? (Nouveau Graphe)
    st.subheader("1. Menace immédiate : Les objets les plus proches")

    col_txt1, col_graph1 = st.columns([1, 2])

    with col_txt1:
        st.markdown("### Comment ce graphe répond à la problématique ?")
        st.info(
            """
            **Ce graphique identifie directement les objets qui 'frôlent' le plus notre planète.**
            
            En triant la base MySQL par distance croissante, on isole le **Top 5 des menaces prioritaires** de la semaine. 
            Plus la barre est courte, plus l'objet passe près de la Terre. C'est le premier indicateur brut de la problématique.
            """
        )

    with col_graph1:
        # Top 5 des plus proches
        df_proches = df_filtre.nsmallest(5, "distance_terre_km")
        fig_proches = px.bar(
            df_proches,
            x="distance_terre_km",
            y="nom",
            orientation="h",
            text_auto=True,
            title="Top 5 des astéroïdes les plus proches de nous (en km)",
            template="plotly_dark",
            color_discrete_sequence=["#ff7f0e"],
        )
        fig_proches.update_layout(yaxis={"categoryorder": "total descending"})
        st.plotly_chart(fig_proches, use_container_width=True)

    st.markdown("---")

    # BLOC 2 : LE CALCUL DE LA DANGEROSITÉ
    st.subheader("2. Comprendre le calcul : Distance vs Vitesse vs Taille")

    col_graph2, col_txt2 = st.columns([2, 1])

    with col_graph2:
        fig_scatter = px.scatter(
            df_filtre,
            x="distance_terre_km",
            y="vitesse_km_h",
            size="diametre_max_metres",
            color="Statut",
            hover_name="nom",
            labels={
                "distance_terre_km": "Distance (km)",
                "vitesse_km_h": "Vitesse (km/h)",
            },
            color_discrete_map={
                "✅ Sûr": "#00CC96",
                "⚠️ Potentiellement Dangereux": "#EF553B",
            },
            template="plotly_dark",
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col_txt2:
        st.markdown("###  Comment ce graphe répond à la problématique ?")
        st.warning(
            """
            **C'est la réponse visuelle à la deuxième partie de ta problématique : "Comment est calculée la dangerosité ?".**
            
            En observant la couleur des bulles, on comprend la logique de la NASA :
            * Un astéroïde devient **rouge (Dangereux)** s'il combine une **distance très faible** (proche de l'axe vertical 0) ET un **diamètre important** (taille de la bulle).
            * Un petit astéroïde (petite bulle), même très proche ou très rapide, restera souvent **vert (Sûr)** car il brûlerait dans l'atmosphère.
            """
        )

    st.markdown("---")
    # BLOC 3 : PROPORTION ET DISTRIBUTION
    st.subheader("3. Profil global et distribution des tailles")

    col_txt3, col_graph3a, col_graph3b = st.columns([1, 1, 1])

    with col_txt3:
        st.markdown("### Comment ces graphes complètent l'analyse ?")
        st.success(
            """
            **Ils permettent de contextualiser la rareté de la menace.**
            
            * **L'anneau (à gauche)** prouve que l'immense majorité des objets qui croisent la Terre sont totalement inoffensifs. 
            * **L'histogramme (à droite)** montre la distribution des tailles. La physique spatiale se vérifie ici : l'espace est saturé de petits débris (premières barres), tandis que les monstres de plus de 500 mètres sont extrêmement rares.
            """
        )

    with col_graph3a:
        # Proportion de danger
        fig_pie = px.pie(
            df_filtre,
            names="Statut",
            hole=0.4,
            color="Statut",
            color_discrete_map={
                "✅ Sûr": "#00CC96",
                "⚠️ Potentiellement Dangereux": "#EF553B",
            },
            template="plotly_dark",
            title="Proportion des types d'objets",
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_graph3b:
        # Nouveau Graphe : Distribution des tailles (Histogramme)
        fig_hist = px.histogram(
            df_filtre,
            x="diametre_max_metres",
            nbins=15,
            title="Nombre d'objets par tranche de diamètre (mètres)",
            template="plotly_dark",
            color_discrete_sequence=["#a370f7"],
        )
        fig_hist.update_layout(
            xaxis_title="Diamètre maximum (mètres)", yaxis_title="Nombre d'astéroïdes"
        )
        st.plotly_chart(fig_hist, use_container_width=True)

    # TABLEAU FINAL
    st.markdown("---")
    st.subheader("Base de données brute complète")
    st.dataframe(df_filtre.drop(columns=["Statut"]), use_container_width=True)

else:
    st.info(
        "Base de données vide. Activez la synchronisation dans le menu latéral."
    )