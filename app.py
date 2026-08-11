import streamlit as st
import pandas as pd
import plotly.express as px
import os
import io
from datetime import datetime

# 1. Configuración de la página
st.set_page_config(page_title="Sistema de Egresos 2026", layout="wide", initial_sidebar_state="expanded")
DB_PATH = "base_datos_historica.csv"

# --- MÓDULO DE SEGURIDAD (LOGIN) ---
if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

if not st.session_state["autenticado"]:
    st.title("🔒 Acceso Restringido")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        pwd = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            # Compara lo escrito con la contraseña oculta en secrets.toml
            if pwd == st.secrets["credenciales"]["password"]: 
                st.session_state["autenticado"] = True
                st.rerun()
            else:
                st.error("Contraseña incorrecta")
    st.stop()

# --- ORDEN CRONOLÓGICO GLOBAL ---
orden_meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]

# --- FUNCIONES DE BASE DE DATOS ---
def cargar_datos():
    if os.path.exists(DB_PATH):
        return pd.read_csv(DB_PATH)
    return pd.DataFrame()

def guardar_datos(nuevo_df):
    df_existente = cargar_datos()
    if not df_existente.empty:
        df_final = pd.concat([df_existente, nuevo_df], ignore_index=True)
    else:
        df_final = nuevo_df
    df_final.to_csv(DB_PATH, index=False)
    return df_final

def limpiar_datos(df):
    columnas_numericas = ["TOTAL EGRESOS", "PAGOS"]
    for col in columnas_numericas:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace('S/', '', regex=False).str.replace('$', '', regex=False).str.replace(',', '', regex=False).str.strip()
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    columnas_texto = ["PROOVEDOR", "INVERSIONES", "EGRESOS", "UNIDAD DE NEGOCIO", "AREA", "LOCALIDAD", "CONCEPTO", "SUB-CONCEPTO", "MES", "AÑO", "DESCRIPCIÓN"]
    for col in columnas_texto:
        if col in df.columns:
            df[col] = df[col].astype(str).str.upper().str.strip()
            
    if "FECHA DE OPERACIÓN" in df.columns:
        df["FECHA DE OPERACIÓN"] = pd.to_datetime(df["FECHA DE OPERACIÓN"], errors='coerce', dayfirst=True).dt.strftime('%d/%m/%Y')
        df["FECHA DE OPERACIÓN"] = df["FECHA DE OPERACIÓN"].fillna("Sin fecha")
        
    return df

df = cargar_datos()

# --- RECUPERACIÓN DE MEMORIA: FORZAR ORDEN CRONOLÓGICO ---
if not df.empty and "MES" in df.columns:
    df["MES"] = pd.Categorical(df["MES"], categories=orden_meses, ordered=True)

# --- COLORES CORPORATIVOS ---
color_rojo_corp = "#8A1538"
color_amarillo_corp = "#D4AF37"
color_costo = "#4A0B1E" 
color_gasto = "#E5C158" 

# --- FORMATO DE MATRICES ---
def formato_dinero(val):
    if pd.isna(val) or val == 0:
        return ""
    return f"S/ {val:,.2f}"

# --- MENÚ DE NAVEGACIÓN LATERAL ---
st.sidebar.title("Navegación")
menu = st.sidebar.radio("Ir a:", [
    "🏠 INICIO", 
    "🏢 INTELIGENCIA DE PROVEEDORES", 
    "📥 GESTIÓN DE DATOS"
])

st.sidebar.divider()

# --- FILTROS GLOBALES ---
if not df.empty and menu != "📥 GESTIÓN DE DATOS":
    st.sidebar.subheader("Filtros Globales")
    
    if "AÑO" in df.columns:
        años = ["Todos"] + df["AÑO"].dropna().astype(str).unique().tolist()
        año_sel = st.sidebar.selectbox("Año", años)
        if año_sel != "Todos":
            df = df[df["AÑO"] == año_sel]
            
    if "MES" in df.columns:
        meses = ["Todos"] + list(df["MES"].dropna().unique())
        mes_sel = st.sidebar.selectbox("Mes", meses)
        if mes_sel != "Todos":
            df = df[df["MES"] == mes_sel]
            
    if "UNIDAD DE NEGOCIO" in df.columns:
        unidades = ["Todas"] + df["UNIDAD DE NEGOCIO"].dropna().unique().tolist()
        un_sel = st.sidebar.selectbox("Unidad de Negocio", unidades)
        if un_sel != "Todas":
            df = df[df["UNIDAD DE NEGOCIO"] == un_sel]
            
    if "AREA" in df.columns:
        areas = ["Todas"] + df["AREA"].dropna().unique().tolist()
        area_sel = st.sidebar.selectbox("Área", areas)
        if area_sel != "Todas":
            df = df[df["AREA"] == area_sel]

# ==========================================
# RUTA 1: INICIO (Dashboard General)
# ==========================================
if menu == "🏠 INICIO":
    st.title("Reporte Actualizable 2026 - Inicio")
    
    if df.empty:
        st.warning("La base de datos está vacía. Ve a 'Gestión de Datos'.")
    else:
        # 1. MÉTRICAS
        total_egresos = df["TOTAL EGRESOS"].sum() if "TOTAL EGRESOS" in df.columns else 0
        costos = df[df["EGRESOS"] == "COSTO"]["TOTAL EGRESOS"].sum() if "EGRESOS" in df.columns else 0
        gastos = df[df["EGRESOS"] == "GASTO"]["TOTAL EGRESOS"].sum() if "EGRESOS" in df.columns else 0
        lima = df[df["LOCALIDAD"] == "LIMA"]["TOTAL EGRESOS"].sum() if "LOCALIDAD" in df.columns else 0
        cusco = df[df["LOCALIDAD"] == "CUSCO"]["TOTAL EGRESOS"].sum() if "LOCALIDAD" in df.columns else 0

        st.subheader("Métricas Generales")
        c1, c2 = st.columns(2)
        c1.metric("💰 Egresos Totales", f"S/ {total_egresos:,.2f}")
        c2.metric("📉 Costos Totales", f"S/ {costos:,.2f}")
        
        st.write("") 
        c3, c4 = st.columns(2)
        c3.metric("📊 Gastos Totales", f"S/ {gastos:,.2f}")
        c4.metric("🏙️ Egresos Lima", f"S/ {lima:,.2f}")
        
        st.write("") 
        c5, c6 = st.columns(2)
        c5.metric("⛰️ Egresos Cusco", f"S/ {cusco:,.2f}")
        
        st.markdown("---")
        
        # 2. GRÁFICOS PRINCIPALES Y PIRÁMIDE COSTO VS GASTO
        col_graf1, col_graf2 = st.columns(2)
        with col_graf1:
            if "MES" in df.columns:
                st.subheader("Evolución de Egresos")
                df_mes = df.groupby("MES", observed=False)["TOTAL EGRESOS"].sum().reset_index()
                df_mes["TOTAL EGRESOS"] = df_mes["TOTAL EGRESOS"].fillna(0)
                df_mes = df_mes.sort_values("MES")
                
                fig_line = px.line(df_mes, x="MES", y="TOTAL EGRESOS", markers=True, color_discrete_sequence=[color_amarillo_corp])
                fig_line.update_traces(line_shape='spline', line=dict(width=3))
                fig_line.update_xaxes(title="", categoryorder='array', categoryarray=orden_meses)
                st.plotly_chart(fig_line, use_container_width=True)

        with col_graf2:
            if "MES" in df.columns and "EGRESOS" in df.columns:
                st.subheader("Costos vs Gastos (Pirámide)")
                df_cg = df.groupby(["MES", "EGRESOS"], observed=False)["TOTAL EGRESOS"].sum().reset_index()
                df_cg["TOTAL EGRESOS"] = df_cg["TOTAL EGRESOS"].fillna(0)
                
                # Transformación para efecto pirámide: Costos hacia la izquierda (negativo)
                df_cg["VALOR_GRAFICO"] = df_cg.apply(lambda x: -x["TOTAL EGRESOS"] if x["EGRESOS"] == "COSTO" else x["TOTAL EGRESOS"], axis=1)
                
                fig_cg = px.bar(df_cg, y="MES", x="VALOR_GRAFICO", color="EGRESOS", orientation='h',
                                color_discrete_map={"COSTO": color_costo, "GASTO": color_gasto},
                                custom_data=["TOTAL EGRESOS"])
                
                fig_cg.update_layout(barmode='relative', xaxis_title="", yaxis_title="")
                fig_cg.update_traces(hovertemplate="%{y} | %{color}<br>S/ %{customdata[0]:,.2f}")
                # Ordenar meses de Enero (arriba) a Diciembre (abajo)
                fig_cg.update_yaxes(categoryorder='array', categoryarray=orden_meses[::-1])
                # Ocultamos la escala X numérica para no mostrar números negativos
                fig_cg.update_layout(xaxis=dict(showticklabels=False))
                
                st.plotly_chart(fig_cg, use_container_width=True)

        st.markdown("---")

        # 3. RANKINGS DETALLADOS (Tablas unificadas en Inicio)
        st.subheader("Rankings Detallados (Desglose)")
        total_global = df["TOTAL EGRESOS"].sum()
        
        c_rk1, c_rk2 = st.columns(2)
        with c_rk1:
            if "UNIDAD DE NEGOCIO" in df.columns:
                st.markdown("**Por Unidad de Negocio**")
                top_un = df.groupby("UNIDAD DE NEGOCIO")["TOTAL EGRESOS"].sum().reset_index()
                top_un["% TOTAL"] = top_un["TOTAL EGRESOS"] / total_global
                top_un = top_un.sort_values(by="TOTAL EGRESOS", ascending=False)
                
                st.dataframe(
                    top_un.style
                    .format({"TOTAL EGRESOS": "S/ {:,.2f}", "% TOTAL": "{:.2%}"})
                    .background_gradient(cmap="RdYlGn", subset=["TOTAL EGRESOS"]),
                    use_container_width=True, hide_index=True
                )
                
        with c_rk2:
            if "PROOVEDOR" in df.columns:
                st.markdown("**Listado Completo de Proveedores**")
                top_prov = df.groupby("PROOVEDOR")["TOTAL EGRESOS"].sum().reset_index()
                top_prov["% TOTAL"] = top_prov["TOTAL EGRESOS"] / total_global
                top_prov = top_prov.sort_values(by="TOTAL EGRESOS", ascending=False)
                
                st.dataframe(
                    top_prov.style
                    .format({"TOTAL EGRESOS": "S/ {:,.2f}", "% TOTAL": "{:.2%}"})
                    .background_gradient(cmap="RdYlGn", subset=["TOTAL EGRESOS"]),
                    use_container_width=True, hide_index=True
                )
        
        st.markdown("---")
        
        # 5. MATRICES ESTRUCTURALES
        st.subheader("Estructura Financiera (Matrices)")
        tab1, tab2 = st.tabs(["📊 Matriz OPEX", "🏗️ Matriz CAPEX"])
        
        with tab1:
            if "INVERSIONES" in df.columns and "CONCEPTO" in df.columns:
                df_opex = df[df["INVERSIONES"] == "OPEX"]
                if not df_opex.empty:
                    matriz_opex = pd.pivot_table(df_opex, values="TOTAL EGRESOS", index="CONCEPTO", columns="MES", aggfunc="sum", margins=True, margins_name="Total", observed=False)
                    st.dataframe(matriz_opex.style.format(formato_dinero), use_container_width=True)
                else:
                    st.info("No hay datos de OPEX registrados.")
                    
        with tab2:
            if "INVERSIONES" in df.columns and "CONCEPTO" in df.columns:
                df_capex = df[df["INVERSIONES"] == "CAPEX"]
                if not df_capex.empty:
                    matriz_capex = pd.pivot_table(df_capex, values="TOTAL EGRESOS", index="CONCEPTO", columns="MES", aggfunc="sum", margins=True, margins_name="Total", observed=False)
                    st.dataframe(matriz_capex.style.format(formato_dinero), use_container_width=True)
                else:
                    st.info("No hay datos de CAPEX registrados.")

# ==========================================
# RUTA 2: INTELIGENCIA DE PROVEEDORES
# ==========================================
elif menu == "🏢 INTELIGENCIA DE PROVEEDORES":
    st.title("Inteligencia de Proveedores")

    if df.empty or "PROOVEDOR" not in df.columns:
        st.warning("La base de datos está vacía o no tiene columna de proveedores. Ve a 'Gestión de Datos'.")
    else:
        tab_resumen, tab_detalle = st.tabs(["📊 Resumen General", "🔎 Análisis Individual"])

        # --- TAB 1: RESUMEN GENERAL (enfoque en gráficos, no en tabla) ---
        with tab_resumen:
            st.subheader("Resumen General de Proveedores")
            st.caption("Vista rápida para identificar a qué proveedor conviene estudiar a detalle.")

            total_global = df["TOTAL EGRESOS"].sum() if "TOTAL EGRESOS" in df.columns else 0

            # Agregados base
            resumen = df.groupby("PROOVEDOR").agg(
                MONTO_TOTAL=("TOTAL EGRESOS", "sum"),
                N_FACTURAS=("TOTAL EGRESOS", "count"),
            ).reset_index()
            resumen["% TOTAL"] = resumen["MONTO_TOTAL"] / total_global if total_global else 0

            # CAPEX / OPEX por proveedor
            if "INVERSIONES" in df.columns:
                capex = df[df["INVERSIONES"] == "CAPEX"].groupby("PROOVEDOR")["TOTAL EGRESOS"].sum()
                opex = df[df["INVERSIONES"] == "OPEX"].groupby("PROOVEDOR")["TOTAL EGRESOS"].sum()
                resumen["CAPEX"] = resumen["PROOVEDOR"].map(capex).fillna(0)
                resumen["OPEX"] = resumen["PROOVEDOR"].map(opex).fillna(0)

            # Última compra y recencia (requiere parsear FECHA DE OPERACIÓN, guardada como texto dd/mm/yyyy)
            if "FECHA DE OPERACIÓN" in df.columns:
                fechas_parseadas = pd.to_datetime(df["FECHA DE OPERACIÓN"], format="%d/%m/%Y", errors="coerce")
                ultima_compra = fechas_parseadas.groupby(df["PROOVEDOR"]).max()
                resumen["ÚLTIMA COMPRA"] = resumen["PROOVEDOR"].map(ultima_compra)
                hoy = pd.Timestamp(datetime.now().date())
                resumen["DÍAS SIN COMPRAR"] = (hoy - resumen["ÚLTIMA COMPRA"]).dt.days

            resumen = resumen.sort_values(by="MONTO_TOTAL", ascending=False)

            # --- KPIs ---
            top5_share = resumen.head(5)["MONTO_TOTAL"].sum() / total_global if total_global else 0
            c1, c2, c3 = st.columns(3)
            c1.metric("🏢 Proveedores Activos", f"{resumen['PROOVEDOR'].nunique()}")
            if "DÍAS SIN COMPRAR" in resumen.columns:
                inactivos_90 = (resumen["DÍAS SIN COMPRAR"] > 90).sum()
                c2.metric("⏸️ Sin comprar +90 días", f"{inactivos_90}")
            c3.metric("🎯 Concentración Top 5", f"{top5_share:.1%}", help="% del gasto total que representan los 5 proveedores más grandes")

            st.markdown("---")

            # --- FILA DE GRÁFICOS 1: Top 10 y Concentración ---
            g1, g2 = st.columns(2)
            top10 = resumen.head(10)

            with g1:
                st.markdown("**Top 10 Proveedores por Monto**")
                fig_top10 = px.bar(top10, x="MONTO_TOTAL", y="PROOVEDOR", orientation="h", text_auto=".2s", color_discrete_sequence=[color_rojo_corp])
                fig_top10.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="", yaxis_title="")
                st.plotly_chart(fig_top10, use_container_width=True)

            with g2:
                st.markdown("**Concentración de Gasto**")
                resto = resumen["MONTO_TOTAL"].sum() - resumen.head(5)["MONTO_TOTAL"].sum()
                df_conc = pd.concat([
                    resumen.head(5)[["PROOVEDOR", "MONTO_TOTAL"]],
                    pd.DataFrame([{"PROOVEDOR": "RESTO DE PROVEEDORES", "MONTO_TOTAL": resto}])
                ])
                fig_conc = px.pie(df_conc, values="MONTO_TOTAL", names="PROOVEDOR", hole=0.5,
                                   color_discrete_sequence=px.colors.sequential.Reds_r)
                fig_conc.update_traces(textinfo="percent+label", showlegend=False)
                st.plotly_chart(fig_conc, use_container_width=True)

            # --- FILA DE GRÁFICOS 2: CAPEX/OPEX y Recencia vs Monto ---
            g3, g4 = st.columns(2)

            with g3:
                if "CAPEX" in resumen.columns:
                    st.markdown("**CAPEX vs. OPEX (Top 10)**")
                    df_co = top10.melt(id_vars="PROOVEDOR", value_vars=["CAPEX", "OPEX"], var_name="TIPO", value_name="MONTO")
                    fig_co = px.bar(df_co, x="MONTO", y="PROOVEDOR", color="TIPO", orientation="h",
                                     color_discrete_map={"CAPEX": color_costo, "OPEX": color_gasto})
                    fig_co.update_layout(yaxis={'categoryorder': 'total ascending'}, xaxis_title="", yaxis_title="")
                    st.plotly_chart(fig_co, use_container_width=True)

            with g4:
                if "DÍAS SIN COMPRAR" in resumen.columns:
                    st.markdown("**A quién estudiar: Monto vs. Días sin Comprar**")
                    st.caption("Arriba a la derecha = proveedores grandes que dejaron de comprar. Vale la pena revisarlos.")
                    fig_bub = px.scatter(resumen, x="DÍAS SIN COMPRAR", y="MONTO_TOTAL", size="MONTO_TOTAL",
                                          hover_name="PROOVEDOR", color_discrete_sequence=[color_rojo_corp])
                    fig_bub.update_layout(xaxis_title="Días sin comprar", yaxis_title="Monto total (S/)")
                    st.plotly_chart(fig_bub, use_container_width=True)

            st.markdown("---")

            # --- TABLA SIMPLE: solo Top 10 visible, resto en expander ---
            st.markdown("**Top 10 — Detalle**")
            cols_tabla = ["PROOVEDOR", "MONTO_TOTAL", "% TOTAL", "N_FACTURAS"]
            if "DÍAS SIN COMPRAR" in resumen.columns:
                cols_tabla.append("DÍAS SIN COMPRAR")
            st.dataframe(
                top10[cols_tabla].style.format({"MONTO_TOTAL": "S/ {:,.2f}", "% TOTAL": "{:.2%}"}),
                use_container_width=True, hide_index=True
            )

            with st.expander("Ver listado completo de proveedores"):
                st.dataframe(
                    resumen[cols_tabla].style.format({"MONTO_TOTAL": "S/ {:,.2f}", "% TOTAL": "{:.2%}"}),
                    use_container_width=True, hide_index=True
                )

        # --- TAB 2: ANÁLISIS INDIVIDUAL (drill-down por proveedor) ---
        with tab_detalle:
            lista_proveedores = df["PROOVEDOR"].dropna().unique().tolist()
            lista_proveedores.sort()
            prov_sel = st.selectbox("Busca y selecciona un Proveedor:", options=lista_proveedores)

            st.subheader(f"Detalle: {prov_sel}")
            df_prov = df[df["PROOVEDOR"] == prov_sel]

            total_prov = df_prov['TOTAL EGRESOS'].sum()
            capex_prov = df_prov[df_prov["INVERSIONES"] == "CAPEX"]["TOTAL EGRESOS"].sum() if "INVERSIONES" in df_prov.columns else 0
            opex_prov = df_prov[df_prov["INVERSIONES"] == "OPEX"]["TOTAL EGRESOS"].sum() if "INVERSIONES" in df_prov.columns else 0

            c1, c2 = st.columns(2)
            c1.metric("Monto Total Facturado", f"S/ {total_prov:,.2f}")
            c2.metric("Inversión (CAPEX)", f"S/ {capex_prov:,.2f}")

            st.write("")
            c3, c4 = st.columns(2)
            c3.metric("Operación (OPEX)", f"S/ {opex_prov:,.2f}")
            c4.metric("Cantidad de Registros", f"{len(df_prov)}")

            st.markdown("---")

            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                if "MES" in df_prov.columns:
                    st.subheader("Tendencia de Gastos (Evolución)")
                    df_prov_mes = df_prov.groupby("MES", observed=False)["TOTAL EGRESOS"].sum().reset_index()
                    df_prov_mes["TOTAL EGRESOS"] = df_prov_mes["TOTAL EGRESOS"].fillna(0)
                    df_prov_mes = df_prov_mes.sort_values("MES")

                    fig_prov_line = px.line(df_prov_mes, x="MES", y="TOTAL EGRESOS", markers=True, color_discrete_sequence=[color_rojo_corp])
                    fig_prov_line.update_traces(line_shape='spline', line=dict(width=3))
                    fig_prov_line.update_xaxes(title="", categoryorder='array', categoryarray=orden_meses)
                    st.plotly_chart(fig_prov_line, use_container_width=True)

            with col_graf2:
                st.subheader("Resumen de Actividad")
                if "CONCEPTO" in df_prov.columns:
                    top_concepto = df_prov.groupby("CONCEPTO")["TOTAL EGRESOS"].sum().reset_index().sort_values(by="TOTAL EGRESOS", ascending=False).head(3)
                    st.markdown("**Conceptos más usados:**")
                    st.dataframe(top_concepto.style.format({"TOTAL EGRESOS": "S/ {:,.2f}"}), use_container_width=True, hide_index=True)

                if "AREA" in df_prov.columns:
                    top_area = df_prov.groupby("AREA")["TOTAL EGRESOS"].sum().reset_index().sort_values(by="TOTAL EGRESOS", ascending=False).head(3)
                    st.markdown("**Áreas de mayor impacto:**")
                    st.dataframe(top_area.style.format({"TOTAL EGRESOS": "S/ {:,.2f}"}), use_container_width=True, hide_index=True)

            st.markdown("---")
            st.subheader("Desglose de Facturas del Proveedor")
            # Columnas exactas solicitadas para la auditoría
            columnas_mostrar = ["FECHA DE OPERACIÓN", "DESCRIPCIÓN", "INVERSIONES", "CONCEPTO", "SUB-CONCEPTO", "TOTAL EGRESOS"]
            columnas_disp = [col for col in columnas_mostrar if col in df_prov.columns]
            st.dataframe(df_prov[columnas_disp], use_container_width=True, hide_index=True)

# ==========================================
# RUTA 3: GESTIÓN DE DATOS
# ==========================================
elif menu == "📥 GESTIÓN DE DATOS":
    st.title("📥 Mantenimiento de Base de Datos")
    
    st.subheader("Vista Previa de la Base de Datos Histórica")
    if not df.empty:
        st.dataframe(df, use_container_width=True, height=250)
    else:
        st.info("La base de datos se encuentra vacía.")
        
    st.markdown("---")
    
    st.subheader("Agregar Nueva Data")
    opcion = st.radio("Método:", ["Pegar Texto (Celdas)", "Subir Archivo Excel"])
    nuevo_df = None
    if opcion == "Subir Archivo Excel":
        archivo = st.file_uploader("Sube el Excel", type=["xlsx", "xls"])
        if st.button("Procesar Archivo") and archivo:
            nuevo_df = pd.read_excel(archivo)
    elif opcion == "Pegar Texto (Celdas)":
        texto = st.text_area("Pega filas desde Excel:")
        if st.button("Procesar Texto") and texto:
            nuevo_df = pd.read_csv(io.StringIO(texto), sep='\t')

    if nuevo_df is not None:
        nuevo_df = limpiar_datos(nuevo_df)
        guardar_datos(nuevo_df)
        st.success("✅ Datos inyectados correctamente.")
        st.rerun()

    st.markdown("---")
    with st.expander("⚠️ Borrar Base de Datos"):
        if st.button("🗑️ Eliminar TODO"):
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                st.rerun()
