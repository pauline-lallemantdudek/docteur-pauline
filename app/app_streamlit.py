import streamlit as st
import pandas as pd
import datetime
import calendar as py_calendar  # Le module Python pour les dates
from streamlit_calendar import calendar as st_calendar  # Le composant de visualisation
import os

st.set_page_config(page_title="Planning du Service", layout="wide")

DATA_FILE = "presences_medecins.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        dtypes = {"Matin": bool, "Après-midi": bool}
        return pd.read_csv(DATA_FILE, dtype=dtypes)
    else:
        return pd.DataFrame(columns=["Nom", "Prénom", "Date", "Matin", "Après-midi"])

def save_data(df):
    df.to_csv(DATA_FILE, index=False)

JOURS_FR = ["Lundi", "Mardi", "Mercredi", "Jeudi", "Vendredi", "Samedi", "Dimanche"]
MOIS_FR = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre"]

st.sidebar.title("Navigation")
page = st.sidebar.radio("Aller vers :", ["📝 Saisie des présences", "📊 Tableau de bord"])

# ----------------- PAGE 1 : SAISIE MENSUELLE -----------------
if page == "📝 Saisie des présences":
    st.title("Saisie de vos disponibilités")
    st.write("Saisissez votre nom pour afficher la grille des jours ouvrés du mois (du lundi au vendredi).")
    
    col1, col2 = st.columns(2)
    with col1:
        prenom = st.text_input("Prénom")
    with col2:
        nom = st.text_input("Nom")
        
    today = datetime.date.today()
    col_m, col_y = st.columns(2)
    with col_m:
        mois_index = st.selectbox("Mois", range(1, 13), format_func=lambda x: MOIS_FR[x-1], index=today.month - 1)
    with col_y:
        annee = st.selectbox("Année", [today.year, today.year + 1])

    if prenom and nom:
        nom_clean = nom.strip().capitalize()
        prenom_clean = prenom.strip().capitalize()
        
        st.write(f"### Planning de {prenom_clean} {nom_clean} — {MOIS_FR[mois_index-1]} {annee}")
        
        # 1. Générer toutes les dates du mois
        num_days = py_calendar.monthrange(annee, mois_index)[1]
        all_dates = [datetime.date(annee, mois_index, day) for day in range(1, num_days + 1)]
        
        # 2. Ne conserver QUE les jours ouvrés (lundi à vendredi, index 0 à 4)
        work_dates = [d for d in all_dates if d.weekday() < 5]
        
        df_all = load_data()
        
        data_editor = []
        for d in work_dates:
            d_str = d.strftime("%Y-%m-%d")
            
            mask = (df_all["Nom"] == nom_clean) & (df_all["Prénom"] == prenom_clean) & (df_all["Date"] == d_str)
            
            if mask.any():
                matin = bool(df_all.loc[mask, "Matin"].values[0])
                aprem = bool(df_all.loc[mask, "Après-midi"].values[0])
            else:
                matin = False
                aprem = False
                
            data_editor.append({
                "Date": d_str,
                "Jour": JOURS_FR[d.weekday()],
                "Matin": matin,
                "Après-midi": aprem
            })
            
        df_month = pd.DataFrame(data_editor)
        
        # 3. Grille interactives de saisie
        edited_df = st.data_editor(
            df_month,
            disabled=["Date", "Jour"],
            hide_index=True,
            use_container_width=True
        )
        
        # 4. Enregistrement
        if st.button("Enregistrer mes présences", type="primary"):
            df_all["Date_obj"] = pd.to_datetime(df_all["Date"]).dt.date
            mask_doc = (df_all["Nom"] == nom_clean) & (df_all["Prénom"] == prenom_clean)
            mask_month = df_all["Date_obj"].apply(lambda x: x.month == mois_index and x.year == annee)
            
            df_all = df_all[~(mask_doc & mask_month)].copy()
            df_all = df_all.drop(columns=["Date_obj"], errors="ignore")
            
            to_add = edited_df[(edited_df["Matin"] == True) | (edited_df["Après-midi"] == True)].copy()
            
            if not to_add.empty:
                to_add["Nom"] = nom_clean
                to_add["Prénom"] = prenom_clean
                to_add = to_add[["Nom", "Prénom", "Date", "Matin", "Après-midi"]]
                df_all = pd.concat([df_all, to_add], ignore_index=True)
                
            save_data(df_all)
            st.success("✅ Vos présences ont été enregistrées avec succès !")
            
    else:
        st.info("Veuillez saisir votre nom et votre prénom pour afficher la grille de saisie.")

# ----------------- PALETTE DE 15 COULEURS DISTINCTES -----------------
COLOR_PALETTE = [
    "#3182CE",  # Bleu
    "#D69E2E",  # Jaune / Ambre
    "#38A169",  # Vert
    "#DD6B20",  # Orange
    "#805AD5",  # Violet
    "#E53E3E",  # Rouge
    "#319795",  # Teal / Cyan
    "#D53F8C",  # Rose
    "#4C51BF",  # Indigo
    "#2B6CB0",  # Bleu foncé
    "#2F855A",  # Vert foncé
    "#C53030",  # Rouge foncé
    "#9B2C2C",  # Bordeau
    "#2C5282",  # Bleu nuit
    "#742A2A"   # Marron
]

# ----------------- PAGE 2 : DASHBOARD (MODE CALENDRIER) -----------------
if page == "📊 Tableau de bord":
    st.title("Tableau de bord des présences")
    st.write("Vue d'ensemble des médecins présents dans le service.")
    
    with st.spinner("Chargement du planning..."):
        df = load_data()
    
    if df.empty:
        st.info("Aucune présence n'a encore été enregistrée dans le système.")
    else:
        df["Nom Complet"] = df["Prénom"] + " " + df["Nom"]
        
        # 1. Associer à CHAQUE médecin unique UNE couleur dédiée dans l'ordre
        medecins_uniques = sorted(df["Nom Complet"].unique())
        doctor_color_map = {}
        for i, doc in enumerate(medecins_uniques):
            # On prend la couleur correspondant à l'index du médecin (avec % si plus de 15 médecins)
            doctor_color_map[doc] = COLOR_PALETTE[i % len(COLOR_PALETTE)]
        
        # 2. Affichage de la légende pour les médecins
        st.write("**Légende des médecins :**")
        cols = st.columns(min(len(medecins_uniques), 5))
        for i, doc in enumerate(medecins_uniques):
            color = doctor_color_map[doc]
            cols[i % 5].markdown(
                f'<div style="background-color:{color}; padding: 4px 8px; border-radius: 4px; color: white; font-weight: bold; text-align: center; margin-bottom: 5px;">{doc}</div>', 
                unsafe_allow_html=True
            )
        st.write("---")

        # 3. Construction des événements pour le calendrier
        events = []
        for _, row in df.iterrows():
            date_str = str(row["Date"])
            nom = row["Nom Complet"]
            doc_color = doctor_color_map[nom]  # Utilisation de la couleur unique assignée
            
            # Événement pour le matin
            if row["Matin"]:
                events.append({
                    "title": f"☀️ {nom}",
                    "start": f"{date_str}T08:00:00",
                    "end": f"{date_str}T12:30:00",
                    "color": doc_color
                })
                
            # Événement pour l'après-midi
            if row["Après-midi"]:
                events.append({
                    "title": f"🌙 {nom}",
                    "start": f"{date_str}T13:30:00",
                    "end": f"{date_str}T18:00:00",
                    "color": doc_color
                })

        # Configuration du calendrier
        calendar_options = {
            "editable": False,
            "selectable": True,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,timeGridWeek"
            },
            "initialView": "dayGridMonth",
            "hiddenDays": [0, 6],  # Exclut le week-end
            "locale": "fr"
        }

        # Affichage du calendrier Streamlit
        st_calendar(
            events=events,
            options=calendar_options,
            key="calendar"
        )