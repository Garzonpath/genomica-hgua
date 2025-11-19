import streamlit as st
from supabase import create_client
import pandas as pd

# =====================================================
# CONFIGURACIÓN
# =====================================================
st.set_page_config(
    page_title="🧬 Genómica HGUA",
    page_icon="🧬",
    layout="wide"
)

# Conexión Supabase
@st.cache_resource
def init_supabase():
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"]
    )

supabase = init_supabase()

# =====================================================
# TÍTULO
# =====================================================
st.title("🧬 Base de Datos Genómica-HGUA")
st.markdown("---")

# =====================================================
# BARRA DE BÚSQUEDA
# =====================================================
search = st.text_input(
    "🔍 Buscar muestra:",
    placeholder="Ej: 25B, 24P, 23C...",
    help="Formato: [Año][Tipo][Número]. Ejemplo: 25B16796"
)

# =====================================================
# OBTENER MUESTRAS
# =====================================================
def get_samples(search_term=None):
    """Obtiene muestras filtradas o las últimas 20"""
    query = supabase.table('sample').select('sample_id, sample_name, analysis_date, workflow_name')
    
    if search_term:
        query = query.ilike('sample_name', f'{search_term}%')
    
    response = query.order('analysis_date', desc=True).limit(20).execute()
    return response.data

# Obtener muestras
samples = get_samples(search if search else None)

# =====================================================
# TABLA CON CHECKBOXES
# =====================================================
st.markdown("### Muestras disponibles")
st.caption(f"Mostrando {len(samples)} muestra(s)")

if samples:
    # Inicializar selección en session_state
    if 'selected_samples' not in st.session_state:
        st.session_state.selected_samples = []
    
    # Crear tabla
    col1, col2, col3, col4 = st.columns([1, 4, 3, 3])
    
    with col1:
        st.markdown("**☑**")
    with col2:
        st.markdown("**Sample Name**")
    with col3:
        st.markdown("**Analysis Date**")
    with col4:
        st.markdown("**Workflow**")
    
    st.markdown("---")
    
    # Filas con checkboxes
    for idx, sample in enumerate(samples):
        col1, col2, col3, col4 = st.columns([1, 4, 3, 3])
        
        with col1:
            checked = st.checkbox(
                "☑",
                key=f"check_{sample['sample_id']}",
                label_visibility="collapsed"
            )
            if checked and sample['sample_id'] not in st.session_state.selected_samples:
                st.session_state.selected_samples.append(sample['sample_id'])
            elif not checked and sample['sample_id'] in st.session_state.selected_samples:
                st.session_state.selected_samples.remove(sample['sample_id'])
        
        with col2:
            st.text(sample['sample_name'])
        with col3:
            st.text(sample['analysis_date'] or 'N/A')
        with col4:
            st.text(sample['workflow_name'] or 'N/A')
else:
    st.info("No se encontraron muestras")

# =====================================================
# BOTONES DE ACCIÓN
# =====================================================
st.markdown("---")
col_btn1, col_btn2, col_spacer = st.columns([2, 2, 6])

with col_btn1:
    if st.button("📊 Parámetros de Calidad", use_container_width=True):
        if not st.session_state.selected_samples:
            st.warning("⚠️ Selecciona al menos una muestra")
        else:
            st.session_state['show_quality'] = not st.session_state.get('show_quality', False)

with col_btn2:
    if st.button("🧬 Análisis Molecular", use_container_width=True):
        if not st.session_state.selected_samples:
            st.warning("⚠️ Selecciona al menos una muestra")
        else:
            st.session_state['analyzing_samples'] = st.session_state.selected_samples.copy()

# Botón para cerrar análisis molecular
if st.session_state.get('analyzing_samples'):
    if st.button("❌ Cerrar Análisis Molecular", type="secondary"):
        st.session_state['analyzing_samples'] = None
        st.rerun()

# =====================================================
# PARÁMETROS DE CALIDAD
# =====================================================
if st.session_state.get('show_quality', False):
    st.markdown("### 📊 Parámetros de Calidad")
    st.caption("Formato listo para copiar a Google Sheets (separado por TAB)")
    
    # Recopilar TODOS los datos primero
    all_lines = []
    quality_data_display = []
    
    for sample_id in st.session_state.selected_samples:
        # Info de muestra
        sample_info = supabase.table('sample').select('sample_name').eq('sample_id', sample_id).execute()
        sample_name = sample_info.data[0]['sample_name'] if sample_info.data else 'N/A'
        
        # QC ADN
        qc_adn = supabase.table('sample_adn_qc').select('*').eq('sample_id', sample_id).execute()
        
        # QC ARN
        qc_arn = supabase.table('sample_arn_qc').select('*').eq('sample_id', sample_id).execute()
        
        # Procesar datos
        mean_reads = int(qc_adn.data[0]['median_reads_per_amplicon']) if qc_adn.data and qc_adn.data[0].get('median_reads_per_amplicon') else 'N/A'
        uniformity_coverage = f"{qc_adn.data[0]['uniformity_of_base_coverage']:.2f}" if qc_adn.data and qc_adn.data[0].get('uniformity_of_base_coverage') else 'N/A'
        mapd = f"{qc_adn.data[0]['mapd']:.2f}" if qc_adn.data and qc_adn.data[0].get('mapd') else 'N/A'
        
        # Extraer solo PASS/FAIL de fusion_qc
        fusion_qc_raw = qc_arn.data[0]['fusion_qc'] if qc_arn.data and qc_arn.data[0].get('fusion_qc') else 'N/A'
        if fusion_qc_raw != 'N/A':
            fusion_qc = fusion_qc_raw.split(',')[0].strip().upper()
        else:
            fusion_qc = 'N/A'
        
        # Crear línea para copiar (separada por TAB para Google Sheets)
        line_data = f"{sample_name}\t{mean_reads}\t{uniformity_coverage}\t{mapd}\t{fusion_qc}"
        all_lines.append(line_data)
        
        # Guardar para mostrar en tabla
        quality_data_display.append({
            'sample_name': sample_name,
            'mean_reads': str(mean_reads),
            'uniformity_coverage': str(uniformity_coverage),
            'mapd': str(mapd),
            'fusion_qc': fusion_qc
        })
    
    # Mostrar tabla visual
    col_name, col_reads, col_aligned, col_mapd, col_fusion = st.columns([3, 2, 2, 1, 1])
    with col_name:
        st.markdown("**Sample_name**")
    with col_reads:
        st.markdown("**mean_reads**")
    with col_aligned:
        st.markdown("**uniformity_coverage**")
    with col_mapd:
        st.markdown("**mapd**")
    with col_fusion:
        st.markdown("**fusion_qc**")
    
    st.markdown("---")
    
    # Mostrar cada fila
    for data in quality_data_display:
        col_name, col_reads, col_aligned, col_mapd, col_fusion = st.columns([3, 2, 2, 1, 1])
        
        with col_name:
            st.text(data['sample_name'])
        with col_reads:
            st.text(data['mean_reads'])
        with col_aligned:
            st.text(data['uniformity_coverage'])
        with col_mapd:
            st.text(data['mapd'])
        with col_fusion:
            st.text(data['fusion_qc'])
    
    st.markdown("---")
    
    # Campo de texto grande con TODAS las filas para copiar de una vez
    all_data_text = "\n".join(all_lines)
    st.text_area(
        "📋 **Copiar TODAS las filas** (Ctrl+A → Ctrl+C → Pegar en Google Sheets)",
        value=all_data_text,
        height=150,
        key="copy_all_quality",
        help="Los datos están separados por TAB. Al pegar en Google Sheets se distribuirán automáticamente en columnas."
    )
    
    # Botón para cerrar
    if st.button("❌ Cerrar Parámetros de Calidad", type="secondary"):
        st.session_state['show_quality'] = False
        st.rerun()

# =====================================================
# ANÁLISIS MOLECULAR
# =====================================================
if st.session_state.get('analyzing_samples'):
    st.markdown("### 🧬 Análisis Molecular")
    
    # Dropdown clasificaciones
    clasificaciones = [
        "Sin clasificar",
        "Benigna",
        "Probablemente benigna",
        "VUS",
        "Probablemente patogénica",
        "Patogénica",
        "No informar por QC"
    ]
    
    # Para cada muestra que se está analizando
    for sample_id in st.session_state['analyzing_samples']:
            # Info de muestra
            sample_info = supabase.table('sample').select('sample_name').eq('sample_id', sample_id).execute()
            sample_name = sample_info.data[0]['sample_name'] if sample_info.data else 'N/A'
            
            st.markdown(f"#### 📋 {sample_name}")
            st.markdown("---")
            
            # ============== MUTATIONS ==============
            mutations = supabase.table('mutation').select('*').eq('sample_id', sample_id).execute()
            
            if mutations.data:
                st.markdown(f"**🧬 Mutaciones ({len(mutations.data)})**")
                
                for mut in mutations.data:
                    with st.container():
                        # Fila principal con info - TEXTO MÁS GRANDE
                        col_info, col_class, col_btn1, col_btn2, col_save = st.columns([6, 2, 1, 1, 1])
                        
                        with col_info:
                            gene = mut['gene'] or 'N/A'
                            protein = mut['protein'] or 'N/A'
                            coding = mut['coding'] or 'N/A'
                            af = mut['af'] if mut['af'] else 0
                            dp = mut['dp'] if mut['dp'] else 0
                            
                            # Texto más grande
                            st.markdown(f"### {gene} | {protein}")
                            st.markdown(f"**Coding:** {coding}")
                            st.markdown(f"**AF:** {af:.3f} | **DP:** {dp} | **Type:** {mut['type'] or 'N/A'}")
                            st.markdown(f"**Function:** {mut['function'] or 'N/A'} | **Location:** {mut['location'] or 'N/A'}")
                            st.markdown(f"**Oncomine:** {mut['oncomine_variant_class'] or 'N/A'}")
                        
                        with col_class:
                            current_class = mut['clasificacion_hgua'] or 'Sin clasificar'
                            new_class = st.selectbox(
                                "Clasificación",
                                clasificaciones,
                                index=clasificaciones.index(current_class) if current_class in clasificaciones else 0,
                                key=f"class_mut_{mut['mutation_id']}",
                                label_visibility="collapsed"
                            )
                        
                        with col_btn1:
                            # Botón copiar para búsqueda
                            if st.button("🔍", key=f"search_mut_{mut['mutation_id']}", help="Copiar para búsqueda"):
                                st.session_state[f"show_search_mut_{mut['mutation_id']}"] = True
                            else:
                                st.session_state[f"show_search_mut_{mut['mutation_id']}"] = False
                        
                        with col_btn2:
                            # Botón copiar para informe
                            if st.button("📄", key=f"report_mut_{mut['mutation_id']}", help="Copiar para informe"):
                                st.session_state[f"show_report_mut_{mut['mutation_id']}"] = True
                            else:
                                st.session_state[f"show_report_mut_{mut['mutation_id']}"] = False
                        
                        with col_save:
                            if st.button("💾", key=f"save_mut_{mut['mutation_id']}", help="Guardar clasificación"):
                                supabase.table('mutation').update({
                                    'clasificacion_hgua': new_class
                                }).eq('mutation_id', mut['mutation_id']).execute()
                                st.success("✅", icon="✅")
                        
                        # Campo para búsqueda - ANCHO COMPLETO DEBAJO
                        if st.session_state.get(f"show_search_mut_{mut['mutation_id']}", False):
                            transcript = mut['transcript'] or ''
                            search_text = f"{transcript}:{coding}"
                            st.text_area(
                                "📋 Copiar búsqueda (Ctrl+A → Ctrl+C):",
                                value=search_text,
                                height=80,
                                key=f"copy_search_mut_{mut['mutation_id']}"
                            )
                        
                        # Campo para informe - ANCHO COMPLETO DEBAJO
                        if st.session_state.get(f"show_report_mut_{mut['mutation_id']}", False):
                            chrom = mut['chrom'] or ''
                            pos = mut['pos'] or ''
                            exon = mut['exon'] or ''
                            exon_formatted = f"exón {exon}" if exon else ""
                            vaf = af * 100
                            mut_type = mut['type'] or ''
                            transcript = mut['transcript'] or ''
                            report_text = f"{gene} ({chrom}:{pos}; {transcript}) {exon_formatted}; {coding}; {protein}; VAF: {vaf:.2f}%; {dp}; {mut_type}; {new_class}"
                            st.text_area(
                                "📋 Copiar informe (Ctrl+A → Ctrl+C):",
                                value=report_text,
                                height=120,
                                key=f"copy_report_mut_{mut['mutation_id']}"
                            )
                        
                        st.markdown("---")
            
            # Separador entre muestras
            if sample_id != st.session_state["analyzing_samples"][-1]:
                st.markdown("---")
                st.markdown("")
            
            # ============== CNVs ==============
            cnvs = supabase.table('cnv').select('*').eq('sample_id', sample_id).execute()
            
            if cnvs.data:
                st.markdown(f"**📊 CNVs ({len(cnvs.data)})**")
                
                for cnv in cnvs.data:
                    with st.container():
                        col_info, col_class, col_btn, col_save = st.columns([7, 2, 1, 1])
                        
                        with col_info:
                            gene_name = cnv['gene_name'] or 'N/A'
                            cn = cnv['cn'] if cnv['cn'] else 0
                            ci = cnv['ci'] or ''
                            chrom = cnv['chrom'] or ''
                            pos = cnv['pos'] or ''
                            end_pos = cnv['end_pos'] or ''
                            
                            # Texto más grande
                            st.markdown(f"### {gene_name}")
                            st.markdown(f"**CN:** {cn:.2f} | **CI:** {ci}")
                            st.markdown(f"**Oncomine:** {cnv['oncomine_variant_class'] or 'N/A'}")
                        
                        with col_class:
                            current_class = cnv['clasificacion_hgua'] or 'Sin clasificar'
                            new_class = st.selectbox(
                                "Clasificación",
                                clasificaciones,
                                index=clasificaciones.index(current_class) if current_class in clasificaciones else 0,
                                key=f"class_cnv_{cnv['cnv_id']}",
                                label_visibility="collapsed"
                            )
                        
                        with col_btn:
                            if st.button("📄", key=f"report_cnv_{cnv['cnv_id']}", help="Copiar para informe"):
                                st.session_state[f"show_report_cnv_{cnv['cnv_id']}"] = True
                            else:
                                st.session_state[f"show_report_cnv_{cnv['cnv_id']}"] = False
                        
                        with col_save:
                            if st.button("💾", key=f"save_cnv_{cnv['cnv_id']}", help="Guardar clasificación"):
                                supabase.table('cnv').update({
                                    'clasificacion_hgua': new_class
                                }).eq('cnv_id', cnv['cnv_id']).execute()
                                st.success("✅", icon="✅")
                        
                        # Campo para informe - ANCHO COMPLETO DEBAJO
                        if st.session_state.get(f"show_report_cnv_{cnv['cnv_id']}", False):
                            # Determinar amplificación o deleción
                            condicion = "Amplificación" if cn > 2 else "Deleción"
                            
                            # Formatear CI con %
                            ci_formatted = ci
                            if ci and '-' in ci:
                                parts = ci.split('-')
                                if len(parts) == 2:
                                    ci_formatted = f"{parts[0]}%-{parts[1]}%"
                            
                            report_text = f"{condicion} {gene_name} ({chrom}; {pos}:{end_pos}) {ci_formatted}"
                            st.text_area(
                                "📋 Copiar informe (Ctrl+A → Ctrl+C):",
                                value=report_text,
                                height=100,
                                key=f"copy_report_cnv_{cnv['cnv_id']}"
                            )
                        
                        st.markdown("---")
            
            # ============== ARN ALTERATIONS ==============
            arns = supabase.table('arn_alteration').select('*').eq('sample_id', sample_id).execute()
            
            if arns.data:
                st.markdown(f"**🔬 Alteraciones de ARN ({len(arns.data)})**")
                
                for arn in arns.data:
                    with st.container():
                        col_info, col_class, col_btn, col_save = st.columns([7, 2, 1, 1])
                        
                        with col_info:
                            svtype = arn['svtype'] or 'N/A'
                            arn_id = arn['id'] or 'N/A'
                            mol_count = arn['mol_count'] if arn['mol_count'] else 0
                            read_count = arn['read_count'] if arn['read_count'] else 0
                            imbalance_score = arn['imbalance_score'] if arn['imbalance_score'] else 0
                            imbalance_pval = arn['imbalance_pval'] if arn['imbalance_pval'] else 0
                            
                            # Texto más grande
                            st.markdown(f"### {arn_id}")
                            st.markdown(f"**Type:** {svtype}")
                            st.markdown(f"**Mol count:** {mol_count} | **Read count:** {read_count}")
                            st.markdown(f"**Imbalance score:** {imbalance_score:.3f} | **P-value:** {imbalance_pval:.4f}")
                        
                        with col_class:
                            current_class = arn['clasificacion_hgua'] or 'Sin clasificar'
                            new_class = st.selectbox(
                                "Clasificación",
                                clasificaciones,
                                index=clasificaciones.index(current_class) if current_class in clasificaciones else 0,
                                key=f"class_arn_{arn['arn_alteration_id']}",
                                label_visibility="collapsed"
                            )
                        
                        with col_btn:
                            if st.button("📄", key=f"report_arn_{arn['arn_alteration_id']}", help="Copiar para informe (pendiente)", disabled=True):
                                st.info("Formato pendiente de definir")
                        
                        with col_save:
                            if st.button("💾", key=f"save_arn_{arn['arn_alteration_id']}", help="Guardar clasificación"):
                                supabase.table('arn_alteration').update({
                                    'clasificacion_hgua': new_class
                                }).eq('arn_alteration_id', arn['arn_alteration_id']).execute()
                                st.success("✅", icon="✅")
                        
                        st.markdown("---")
            
            # Separador entre muestras
            if sample_id != st.session_state["analyzing_samples"][-1]:
                st.markdown("---")
                st.markdown("")
