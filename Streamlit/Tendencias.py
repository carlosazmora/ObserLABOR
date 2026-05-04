import streamlit as st
from DatosInternacionales import get_contexto_para_ia
from ia_analisis import generar_insight_claude

def mostrar_tendencias_e_insights():
    contexto = get_contexto_para_ia()

    # Avisar al usuario si no hay datos aún
    if "Sin datos" in contexto:
        st.info("⚠️ Los datos de Adzuna aún no han sido cargados. Ve al **Panel Ejecutivo** y presiona 🔄 Actualizar datos para habilitarlo.")

    if st.button("🤖 Generar Análisis con Claude", disabled=("Sin datos" in contexto)):
        respuesta = generar_insight_claude(
            panel_nombre="Tendencias e Insights Estratégicos",
            contexto_datos=contexto
        )
        if respuesta:
            st.markdown(respuesta)