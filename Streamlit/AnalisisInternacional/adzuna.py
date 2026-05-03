# Streamlit/AnalisisInternacional/adzuna.py
import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime

# ==================== CONFIG ====================
APP_ID = "aa4dc3a4"
APP_KEY = "ec8882a52bf119f4e787ef6d92256f86"
BASE_URL = "https://api.adzuna.com/v1/api/jobs"

PAISES = ["us", "ca", "br", "mx", "gb"]
NOMBRES = {"us": "EE.UU.", "ca": "Canadá", "br": "Brasil", "mx": "México", "gb": "Reino Unido"}

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