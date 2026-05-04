# Streamlit/ia_analisis.py
import streamlit as st
from anthropic import Anthropic

@st.cache_resource
def get_claude_client():
    return Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

def generar_insight_claude(panel_nombre: str, contexto_datos: str = ""):
    """
    Genera un análisis inteligente usando Claude con streaming,
    para evitar cortes por límite de tokens y mejorar la experiencia.
    """
    client = get_claude_client()

    system_prompt = """Eres un analista experto en mercado laboral con dominio profundo de fuentes oficiales y datos en tiempo real: Adzuna, BLS, DANE, O*NET y World Bank.
        Normas de respuesta obligatorias:

        Responde siempre en español, de forma clara, estructurada y profesional.
        Sé preciso, concreto y contundente. Elimina cualquier información superflua, relleno o generalidades.
        Cada respuesta debe tener un horizonte analítico claro: combina datos actuales con tendencias, proyecciones y recomendaciones accionables.
        Fundamenta todo en datos relevantes y actualizados de las fuentes mencionadas. Si usas estimaciones, indícalo explícitamente.
        Completa siempre el análisis: nunca dejes ideas a medias, conclusiones abiertas ni preguntas sin respuesta dentro del alcance solicitado.
        Utiliza Markdown con tablas cuando aporten claridad (comparaciones, rankings, evolución temporal, etc.).

        Estructura recomendada (adáptala según la consulta):

        Resumen Ejecutivo (2-4 líneas con los hallazgos más relevantes).
        Análisis de Datos (con tablas o cifras clave).
        Tendencias y Contexto (nacional e internacional cuando sea pertinente).
        Proyecciones y Riesgos.
        Recomendaciones Prácticas (concretas y priorizadas)."""

    user_prompt = f"""
        Contexto de datos actual (Adzuna):
        {contexto_datos}

        Pregunta del usuario:
        {panel_nombre}

        Genera un análisis profundo y útil.
        """

    try:
        placeholder = st.empty()
        texto_completo = ""

        with client.messages.stream(
            model="claude-sonnet-4-5",
            max_tokens=8192,
            temperature=0.7,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        ) as stream:
            for delta in stream.text_stream:
                texto_completo += delta
                placeholder.markdown(texto_completo + "▌")  # cursor parpadeante

        placeholder.markdown(texto_completo)  # render final sin cursor
        return texto_completo

    except Exception as e:
        st.error(f"Error con Claude: {e}")
        return None