# Streamlit/AnalisisInternacional/adzuna.py
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ==================== CONFIG ====================
APP_ID = "e391fe5b"
APP_KEY = "610ad3405c3b0ce0d33412647efa58bb"
BASE_URL = "https://api.adzuna.com/v1/api/jobs"

PAISES = [
    "gb",  # Reino Unido
    "us",  # EE.UU.
    "au",  # Australia
    "ca",  # Canadá
    "nz",  # Nueva Zelanda
    "de",  # Alemania
    "fr",  # Francia
    "nl",  # Países Bajos
    "be",  # Bélgica
    "at",  # Austria
    "ch",  # Suiza
    "it",  # Italia
    "es",  # España
    "pl",  # Polonia
    "br",  # Brasil
    "in",  # India
    "mx",  # México
    "sg",  # Singapur
    "za",  # Sudáfrica
]

NOMBRES = {
    "gb": "Reino Unido",
    "us": "EE.UU.",
    "au": "Australia",
    "ca": "Canadá",
    "nz": "Nueva Zelanda",
    "de": "Alemania",
    "fr": "Francia",
    "nl": "Países Bajos",
    "be": "Bélgica",
    "at": "Austria",
    "ch": "Suiza",
    "it": "Italia",
    "es": "España",
    "pl": "Polonia",
    "br": "Brasil",
    "in": "India",
    "mx": "México",
    "sg": "Singapur",
    "za": "Sudáfrica",
}

PROFESIONES = [
    "data scientist", "software engineer", "data analyst",
    "machine learning engineer", "devops engineer",
    "cybersecurity analyst", "cloud engineer",
    "business analyst", "project manager", "product manager",
    "financial analyst", "marketing specialist", "ux designer",
    "industrial engineer", "supply chain analyst", "nurse", "teacher", "consultant"
]

@st.cache_data(ttl=7200)
def cargar_datos_adzuna():
    """Consulta vacantes usando solo Adzuna (internacional)"""
    registros = []
    progress_bar = st.progress(0)
    total = len(PAISES) * len(PROFESIONES)
    count = 0
    
    for pais in PAISES:
        for perfil in PROFESIONES:
            data = adzuna_request(pais, "search/1", {
                "results_per_page": 1,
                "what": perfil
            })
            if data:
                registros.append({
                    "pais": pais,
                    "pais_nombre": NOMBRES[pais],
                    "perfil": perfil.title(),
                    "vacantes": data.get("count", 0),
                    "fecha": datetime.now().date()
                })
            count += 1
            progress_bar.progress(count / total)
            time.sleep(0.25)
    
    progress_bar.empty()
    return pd.DataFrame(registros)


def adzuna_request(pais: str, endpoint: str, params: dict = None):
    url = f"{BASE_URL}/{pais}/{endpoint}"
    p = {"app_id": APP_ID, "app_key": APP_KEY, **(params or {})}
    try:
        r = requests.get(url, params=p, timeout=12)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ==================== FUNCIONES DE INSIGHTS DATA-DRIVEN ====================
@st.cache_data(ttl=7200)
def get_analisis_completo():
    df = cargar_datos_adzuna()
    
    # Agregaciones útiles
    df_perfil = df.groupby('perfil').agg(
        vacantes_total=('vacantes', 'sum'),
        paises_presentes=('pais_nombre', 'nunique')
    ).reset_index()
    
    df_pais = df.groupby('pais_nombre').agg(
        vacantes_total=('vacantes', 'sum')
    ).reset_index()
    
    # Top y bottom
    top_perfiles = df_perfil.nlargest(10, 'vacantes_total')
    bottom_perfiles = df_perfil.nsmallest(5, 'vacantes_total')
    
    # Crecimiento aproximado (comparación entre países)
    vacantes_us = df[df['pais_nombre'] == 'EE.UU.']['vacantes'].sum()
    vacantes_br = df[df['pais_nombre'] == 'Brasil']['vacantes'].sum()
    
    return {
        'df': df,
        'df_perfil': df_perfil,
        'df_pais': df_pais,
        'top_perfiles': top_perfiles,
        'bottom_perfiles': bottom_perfiles,
        'vacantes_us': vacantes_us,
        'vacantes_br': vacantes_br,
        'total_registros': len(df)
    }
