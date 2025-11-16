import streamlit as st
from supabase import create_client
import pandas as pd

# Configuración
st.set_page_config(page_title="🧬 Genómica HGUA", layout="wide")

# Conexión Supabase
supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

# Título
st.title("🧬 Base de Datos Genómica - HGUA")

# Buscar muestra
sample_name = st.text_input("Buscar muestra:", placeholder="25B16796-A1")

if sample_name:
    # Obtener datos
    sample = supabase.table('sample').select('*').eq('sample_name', sample_name).execute()
    
    if sample.data:
        st.success(f"✅ Muestra encontrada: {sample_name}")
        
        # Mostrar info
        s = sample.data[0]
        col1, col2, col3 = st.columns(3)
        col1.metric("Fecha", s['analysis_date'])
        col2.metric("Celularidad", f"{s['tumor_cellularity']}%")
        col3.metric("Enfermedad", s['disease_type'])
        
        # Obtener mutaciones
        mutations = supabase.table('mutation').select('*').eq('sample_id', s['sample_id']).execute()
        
        st.subheader(f"🧬 Mutaciones ({len(mutations.data)})")
        if mutations.data:
            df = pd.DataFrame(mutations.data)
            st.dataframe(df[['gene', 'protein', 'af', 'dp', 'filter']], use_container_width=True)
        else:
            st.info("No hay mutaciones")
    else:
        st.error("❌ Muestra no encontrada")
