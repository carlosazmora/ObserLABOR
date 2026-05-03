import streamlit as st
import plotly.express as px
from Streamlit.adzuna import get_analisis_completo

def mostrar_tendencias_e_insights():
    data = get_analisis_completo()
    df = data['df']
    
    tab1, tab2, tab3 = st.tabs(["Habilidades / Perfiles Emergentes", 
                               "Brechas Oferta-Demanda", 
                               "Comparación por País"])
    
    with tab1:
        st.subheader("Top 10 Perfiles Más Demandados")
        fig1 = px.bar(data['top_perfiles'], 
                      x='perfil', y='vacantes_total',
                      title="Perfiles con mayor demanda internacional",
                      color='vacantes_total')
        st.plotly_chart(fig1, use_container_width=True)
        
        st.subheader("Perfiles con menor demanda")
        fig2 = px.bar(data['bottom_perfiles'], 
                      x='perfil', y='vacantes_total',
                      title="Perfiles con menor demanda")
        st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Vacantes en EE.UU.", f"{data['vacantes_us']:,.0f}")
        with col2:
            st.metric("Vacantes en Brasil", f"{data['vacantes_br']:,.0f}")
        
        st.info(f"**Brecha observada:** EE.UU. tiene aproximadamente "
                f"{(data['vacantes_us']/data['vacantes_br']):.1f}x más vacantes que Brasil en los perfiles analizados.")
    
    with tab3:
        fig_pais = px.bar(data['df_pais'], x='pais_nombre', y='vacantes_total',
                         title="Vacantes Totales por País")
        st.plotly_chart(fig_pais, use_container_width=True)