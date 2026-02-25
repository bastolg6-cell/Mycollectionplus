import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text

# Configuration de la connexion XAMPP
USER = "root"
PASSWORD = "" 
HOST = "localhost"
DATABASE = "catalogue_basket"

engine = create_engine(f"mysql+mysqlconnector://{USER}:{PASSWORD}@{HOST}/{DATABASE}")

st.title("🏀 Import NBA Ultra-Complet")

fichier = st.file_uploader("Charger le fichier CSV (Édition NBA)", type="csv")

if fichier:
    df = pd.read_csv(fichier)
    
    # Tri par id_card pour une base de données ordonnée
    if 'id_card' in df.columns:
        df = df.sort_values(by='id_card')
    
    st.write(f"### Analyse du fichier : {len(df)} lignes détectées.")
    st.dataframe(df.head(10)) 

    if st.button("🚀 Synchroniser avec la Base de Données"):
        try:
            with st.spinner("Mise à jour des données en cours..."):
                with engine.connect() as conn:
                    with conn.begin():
                        for index, row in df.iterrows():
                            # Requête SQL UPSERT incluant tous les champs name_X et teams_X
                            sql = text("""
                                INSERT INTO basketball_basketballcard 
                                (id_card, date_sold, marque, licence, produit, saison, 
                                name, name_2, name_3, name_4, name_5, name_6, name_7, name_8, name_9, name_10, name_11, name_12,
                                teams, teams_2, teams_3, teams_4, teams_5, teams_6, teams_7, teams_8, teams_9, teams_10, teams_11, teams_12,
                                rc, categorie, type_card, parrallel, numero_card, numerotation_card, type_img, recto_img, verso_img) 
                                VALUES 
                                (:id_card, :date_sold, :marque, :licence, :produit, :saison, 
                                :name, :name_2, :name_3, :name_4, :name_5, :name_6, :name_7, :name_8, :name_9, :name_10, :name_11, :name_12,
                                :teams, :teams_2, :teams_3, :teams_4, :teams_5, :teams_6, :teams_7, :teams_8, :teams_9, :teams_10, :teams_11, :teams_12,
                                :rc, :categorie, :type_card, :parrallel, :numero_card, :numerotation_card, :type_img, :recto_img, :verso_img)
                                ON DUPLICATE KEY UPDATE 
                                date_sold=VALUES(date_sold), marque=VALUES(marque), licence=VALUES(licence), produit=VALUES(produit), saison=VALUES(saison),
                                name=VALUES(name), name_2=VALUES(name_2), name_3=VALUES(name_3), name_4=VALUES(name_4), name_5=VALUES(name_5), name_6=VALUES(name_6),
                                name_7=VALUES(name_7), name_8=VALUES(name_8), name_9=VALUES(name_9), name_10=VALUES(name_10), name_11=VALUES(name_11), name_12=VALUES(name_12),
                                teams=VALUES(teams), teams_2=VALUES(teams_2), teams_3=VALUES(teams_3), teams_4=VALUES(teams_4), teams_5=VALUES(teams_5), teams_6=VALUES(teams_6),
                                teams_7=VALUES(teams_7), teams_8=VALUES(teams_8), teams_9=VALUES(teams_9), teams_10=VALUES(teams_10), teams_11=VALUES(teams_11), teams_12=VALUES(teams_12),
                                RC=VALUES(RC), categorie=VALUES(categorie), type_card=VALUES(type_card), parrallel=VALUES(parrallel),
                                numero_card=VALUES(numero_card), numerotation_card=VALUES(numerotation_card), type_img=VALUES(type_img), recto_img=VALUES(recto_img), verso_img=VALUES(verso_img)
                            """)
                            
                            # Nettoyage des NaN de Pandas pour MySQL
                            params = {k: (None if pd.isna(v) else v) for k, v in row.items()}
                            
                            conn.execute(sql, params)
                            
            st.success("Toutes les cartes ont été ajoutées ou mises à jour !")
            st.balloons()
        except Exception as e:
            st.error(f"Erreur technique : {e}")

# Aperçu de la table
if st.checkbox("Vérifier le contenu de la table SQL"):
    try:
        df_sql = pd.read_sql("SELECT * FROM basketball_basketballcard ORDER BY id_card DESC LIMIT 100", engine)
        st.write("Dernières entrées :")
        st.dataframe(df_sql)
    except Exception as e:
        st.info("Impossible d'afficher les données.")