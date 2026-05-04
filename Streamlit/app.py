import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from DatosInternacionales import mostrar_boton_actualizacion, get_analisis_completo
from VariacionesSalariales import mostrar_variaciones_salariales
from Tendencias import mostrar_tendencias_e_insights

st.set_page_config(page_title="Observatorio Laboral Unisabana", layout="wide", page_icon="📊")

# ==================== DATOS DE EJEMPLO ====================
@st.cache_data
def cargar_datos():
    df_programas = pd.DataFrame({
        'Programa': ['Ingeniería de Sistemas', 'Administración', 'Economía', 'Derecho', 'Marketing', 'Diseño Industrial'],
        'Empleabilidad_%': [94, 87, 85, 76, 89, 82],
        'Salario_inicial': [5200, 3900, 4300, 3100, 3700, 3600],
        'Crecimiento_%': [18, 9, 12, -4, 22, 11],
        'Sector': ['Tecnología', 'Finanzas', 'Finanzas', 'Legal', 'Marketing', 'Manufactura'],
        'Region': ['Nacional', 'Nacional', 'Nacional', 'Nacional', 'Nacional', 'Nacional']
    })

    df_competencias = pd.DataFrame({
        'Competencia': ['Python', 'Power BI / Tableau', 'Inglés Avanzado', 'IA Generativa', 'Liderazgo', 'Comunicación', 'Machine Learning'],
        'Demanda_%': [96, 89, 91, 94, 82, 87, 78],
        'Tipo': ['Técnica', 'Técnica', 'Transversal', 'Técnica', 'Transversal', 'Transversal', 'Técnica'],
        'Tendencia': ['Fuerte Crecimiento', 'Crecimiento', 'Estable', 'Fuerte Crecimiento', 'Estable', 'Estable', 'Crecimiento']
    })
    return df_programas, df_competencias

df_programas, df_competencias = cargar_datos()

# ==================== SIDEBAR ====================
st.sidebar.title("📊 Observatorio Laboral")

seccion = st.sidebar.radio("Navegación", [
    "🏠 Panel Ejecutivo",
    "🔎 Análisis por Programa",
    "🌍 Datos Internacionales",
    "📈 Tendencias e Insights",
    "🚨 Alertas",
    "💰 Variaciones Salariales",
    "🌍 Cobertura Geográfica",
    "📚 Fuentes",
    "🔧 Mantenimiento"
])

st.sidebar.caption(f"{datetime.now().strftime('%d %b %Y')}")

# ==================== PANEL EJECUTIVO ====================
if seccion == "🏠 Panel Ejecutivo":
    st.title("🏠 Panel Ejecutivo")
    st.markdown("**Monitoreo del Mercado Laboral - Universidad de La Sabana**")

    # --- Orquestación de datos Adzuna ---
    with st.expander("🔄 Gestión de datos internacionales (Adzuna)", expanded=True):
        mostrar_boton_actualizacion()

    st.divider()

# ==================== ANÁLISIS POR PROGRAMA ====================
elif seccion == "🔎 Análisis por Programa":
    st.title("🔎 Análisis por Programa Académico")
    programa = st.selectbox("Selecciona un programa", df_programas['Programa'])
    info = df_programas[df_programas['Programa'] == programa].iloc[0]

    col1, col2, col3 = st.columns(3)
    col1.metric("Empleabilidad", f"{info['Empleabilidad_%']}%")
    col2.metric("Salario Inicial", f"${info['Salario_inicial']:,} COP")
    col3.metric("Crecimiento", f"{info['Crecimiento_%']}%", delta=f"{info['Crecimiento_%']}%")

    st.info(f"**Pertinencia frente al sector productivo:** Alta en el sector **{info['Sector']}**")

# ==================== TENDENCIAS E INSIGHTS ====================
elif seccion == "📈 Tendencias e Insights":
    st.title("📈 Tendencias e Insights Estratégicos")
    mostrar_tendencias_e_insights()

# ==================== ALERTAS ====================
elif seccion == "🚨 Alertas":
    st.title("🚨 Alertas Estratégicas")
    st.error("**Alto Riesgo:** Derecho (-4% crecimiento)")
    st.warning("**Moderado:** Administración necesita más analítica y IA")
    st.success("**Oportunidad:** Marketing Digital (+22% crecimiento)")

# ==================== VARIACIONES SALARIALES ====================
elif seccion == "💰 Variaciones Salariales":
    st.title("💰 Variaciones Salariales")
    mostrar_variaciones_salariales()

# ==================== COBERTURA GEOGRÁFICA ====================
elif seccion == "🌍 Cobertura Geográfica":
    st.title("🌍 Cobertura Geográfica")
    st.info("**Local (Bogotá / Cundinamarca) | Nacional | Internacional**")

# ==================== FUENTES ====================
elif seccion == "📚 Fuentes":
    st.title("📚 Fuentes de Información")
    st.write("**Principales fuentes:**")
    fuentes = ["Servicio Público de Empleo", "Ministerio del Trabajo", "Banco de la República",
               "Ocupacol", "LinkedIn", "World Economic Forum", "McKinsey"]
    for f in fuentes:
        st.success(f"✅ {f}")

# ==================== MANTENIMIENTO ====================
elif seccion == "🔧 Mantenimiento":
    st.title("🔧 Mantenimiento y Sostenibilidad")
    st.subheader("Frecuencia de Actualización")
    st.write("- Datos: Mensual / Trimestral según fuente")
    st.write("- Dashboard: Automático cada vez que se actualicen los datos")
    st.write("- Auditoría: Mensual por responsable de Alumni")

# ==================== DATOS INTERNACIONALES ====================
elif seccion == "🌍 Datos Internacionales":
    st.title("🌍 Análisis Internacional - Adzuna")

    data = get_analisis_completo()

    if data is None:
        st.warning("⚠️ Sin datos cargados. Ve al **Panel Ejecutivo** y presiona 🔄 Actualizar datos.")
    else:
        df_adzuna = data['df']
        st.success(f"✅ Datos cargados: **{len(df_adzuna):,} registros**")

        col1, col2 = st.columns(2)
        with col1:
            pais_sel = st.selectbox("País", sorted(df_adzuna["pais_nombre"].unique()))
        with col2:
            todas = sorted(df_adzuna["perfil"].unique())
            perfil_sel = st.multiselect("Profesiones", options=todas, default=todas)

        df_filtrado = df_adzuna[
            (df_adzuna["pais_nombre"] == pais_sel) &
            (df_adzuna["perfil"].isin(perfil_sel))
        ].sort_values("vacantes", ascending=False)

        fig = px.bar(df_filtrado, x="perfil", y="vacantes",
                     title=f"Vacantes en {pais_sel}", color="perfil")
        st.plotly_chart(fig, use_container_width=True)

        columnas_mostrar = ["pais_nombre", "perfil", "vacantes"]
        st.dataframe(df_filtrado[columnas_mostrar], use_container_width=True, hide_index=True)

st.caption("Observatorio del Mercado Laboral - Alumni Sabana")