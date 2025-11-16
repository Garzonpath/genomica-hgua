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
    btn_quality = st.button("📊 Parámetros de Calidad", use_container_width=True)

with col_btn2:
    btn_molecular = st.button("🧬 Análisis Molecular", use_container_width=True)

# =====================================================
# PARÁMETROS DE CALIDAD
# =====================================================
if btn_quality:
    if not st.session_state.selected_samples:
        st.warning("⚠️ Selecciona al menos una muestra")
    else:
        st.markdown("### 📊 Parámetros de Calidad")
        st.caption("Formato listo para copiar a Google Sheets (separado por TAB)")
        
        # Encabezados
        col_name, col_reads, col_aligned, col_mapd, col_fusion, col_copy = st.columns([3, 2, 2, 1, 1, 1])
        with col_name:
            st.markdown("**Sample_name**")
        with col_reads:
            st.markdown("**mean_reads**")
        with col_aligned:
            st.markdown("**percent_aligned**")
        with col_mapd:
            st.markdown("**mapd**")
        with col_fusion:
            st.markdown("**fusion_qc**")
        with col_copy:
            st.markdown("**Copiar**")
        
        st.markdown("---")
        
        # Obtener datos de QC
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
            percent_aligned = qc_adn.data[0]['percent_aligned_reads'] if qc_adn.data and qc_adn.data[0].get('percent_aligned_reads') else 'N/A'
            mapd = f"{qc_adn.data[0]['mapd']:.2f}" if qc_adn.data and qc_adn.data[0].get('mapd') else 'N/A'
            
            # Extraer solo PASS/FAIL de fusion_qc
            fusion_qc_raw = qc_arn.data[0]['fusion_qc'] if qc_arn.data and qc_arn.data[0].get('fusion_qc') else 'N/A'
            if fusion_qc_raw != 'N/A':
                fusion_qc = fusion_qc_raw.split(',')[0].strip().upper()
            else:
                fusion_qc = 'N/A'
            
            # Crear línea para copiar (separada por TAB para Google Sheets)
            line_data = f"{sample_name}\t{mean_reads}\t{percent_aligned}\t{mapd}\t{fusion_qc}"
            
            # Mostrar fila
            col_name, col_reads, col_aligned, col_mapd, col_fusion, col_copy = st.columns([3, 2, 2, 1, 1, 1])
            
            with col_name:
                st.text(sample_name)
            with col_reads:
                st.text(str(mean_reads))
            with col_aligned:
                st.text(str(percent_aligned))
            with col_mapd:
                st.text(str(mapd))
            with col_fusion:
                st.text(fusion_qc)
            with col_copy:
                # Botón que muestra el texto copiable
                if st.button("📋", key=f"copy_{sample_id}", help="Click para ver texto copiable"):
                    st.session_state[f"show_copy_{sample_id}"] = True
            
            # Mostrar texto copiable si se presionó el botón
            if st.session_state.get(f"show_copy_{sample_id}", False):
                st.text_input("Copiar esta línea:", value=line_data, key=f"copytext_{sample_id}")

# =====================================================
# ANÁLISIS MOLECULAR
# =====================================================
if btn_molecular:
    if not st.session_state.selected_samples:
        st.warning("⚠️ Selecciona al menos una muestra")
    else:
        st.markdown("### 🧬 Análisis Molecular")
        
        # Dropdown clasificaciones
        clasificaciones = [
            "Sin clasificar",
            "Benigna",
            "Probablemente benigna",
            "VUS",
            "Probablemente patogénica",
            "Patogénica"
        ]
        
        # Para cada muestra seleccionada
        for sample_id in st.session_state.selected_samples:
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
                        # Fila principal con info
                        col_info, col_class, col_btn1, col_btn2, col_save = st.columns([6, 2, 1, 1, 1])
                        
                        with col_info:
                            gene = mut['gene'] or 'N/A'
                            protein = mut['protein'] or 'N/A'
                            coding = mut['coding'] or 'N/A'
                            af = mut['af'] if mut['af'] else 0
                            dp = mut['dp'] if mut['dp'] else 0
                            
                            st.markdown(f"**{gene}** | {protein} | {coding}")
                            st.caption(f"AF: {af:.3f} | DP: {dp} | Type: {mut['type'] or 'N/A'}")
                            st.caption(f"Function: {mut['function'] or 'N/A'} | Location: {mut['location'] or 'N/A'}")
                            st.caption(f"Oncomine: {mut['oncomine_variant_class'] or 'N/A'}")
                        
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
                            # Copiar para búsqueda: transcript:coding
                            transcript = mut['transcript'] or ''
                            search_text = f"{transcript}:{coding}"
                            if st.button("🔍", key=f"search_mut_{mut['mutation_id']}", help="Copiar para búsqueda"):
                                st.session_state[f"show_search_mut_{mut['mutation_id']}"] = True
                        
                        with col_btn2:
                            # Copiar para informe
                            if st.button("📄", key=f"report_mut_{mut['mutation_id']}", help="Copiar para informe"):
                                st.session_state[f"show_report_mut_{mut['mutation_id']}"] = True
                        
                        with col_save:
                            if st.button("💾", key=f"save_mut_{mut['mutation_id']}", help="Guardar clasificación"):
                                supabase.table('mutation').update({
                                    'clasificacion_hgua': new_class
                                }).eq('mutation_id', mut['mutation_id']).execute()
                                st.success("✅")
                        
                        # Mostrar textos copiables
                        if st.session_state.get(f"show_search_mut_{mut['mutation_id']}", False):
                            st.text_input("Copiar búsqueda:", value=search_text, key=f"copy_search_mut_{mut['mutation_id']}")
                        
                        if st.session_state.get(f"show_report_mut_{mut['mutation_id']}", False):
                            # GEN (chrom:pos; transcript) exon; coding; protein; VAF: XX.XX%; dp; type; clasificacion
                            chrom = mut['chrom'] or ''
                            pos = mut['pos'] or ''
                            exon = mut['exon'] or ''
                            vaf = af * 100
                            mut_type = mut['type'] or ''
                            report_text = f"{gene} ({chrom}:{pos}; {transcript}) {exon}; {coding}; {protein}; VAF: {vaf:.2f}%; {dp}; {mut_type}; {new_class}"
                            st.text_input("Copiar informe:", value=report_text, key=f"copy_report_mut_{mut['mutation_id']}")
                        
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
                            
                            st.markdown(f"**{arn_id}** | Type: {svtype}")
                            st.caption(f"Mol count: {mol_count} | Read count: {read_count}")
                            st.caption(f"Imbalance score: {imbalance_score:.3f} | P-value: {imbalance_pval:.4f}")
                        
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
                                st.success("✅")
                        
                        st.markdown("---")
            
            # Separador entre muestras
            if sample_id != st.session_state.selected_samples[-1]:
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
                            
                            st.markdown(f"**{gene_name}** | CN: {cn:.2f}")
                            st.caption(f"CI: {ci} | Oncomine: {cnv['oncomine_variant_class'] or 'N/A'}")
                        
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
                        
                        with col_save:
                            if st.button("💾", key=f"save_cnv_{cnv['cnv_id']}", help="Guardar clasificación"):
                                supabase.table('cnv').update({
                                    'clasificacion_hgua': new_class
                                }).eq('cnv_id', cnv['cnv_id']).execute()
                                st.success("✅")
                        
                        # Texto para informe
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
                            st.text_input("Copiar informe:", value=report_text, key=f"copy_report_cnv_{cnv['cnv_id']}")
                        
                        st.markdown("
