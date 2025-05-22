
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Gestor de Trabajos Académicos", layout="wide")
st.title("📚 Panel de Control - Ventas Académicas")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    st.sidebar.subheader("Selecciona grupo(s)")
    selected_sheets = st.sidebar.multiselect("Hojas disponibles:", sheet_names, default=sheet_names)

    dfs = []
    for sheet in selected_sheets:
        df = excel_file.parse(sheet)
        df.columns = df.iloc[0]  # Usar primera fila como encabezado
        df = df[1:]
        df['Grupo'] = sheet
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

    # Validar existencia de columnas esperadas
    expected_cols = [
        'N¬ .', 'Fecha de Pedido', 'Fecha de Entrega', 'Número',
        'Tipo de Tarea', 'Descripcion/detalles', 'Costo', 'Adelanto',
        'Atención', 'Desarrollo', 'Estado', 'Observación', 'Grupo'
    ]
    df = df[[col for col in expected_cols if col in df.columns]]

    # Renombrar columnas si existen
    rename_map = {
        'N¬ .': 'Codigo',
        'Fecha de Pedido': 'Fecha_Pedido',
        'Fecha de Entrega': 'Fecha_Entrega',
        'Número': 'Cliente',
        'Tipo de Tarea': 'Tipo_Tarea',
        'Descripcion/detalles': 'Descripcion',
        'Atención': 'Atencion',
        'Observación': 'Observacion'
    }
    df.rename(columns=rename_map, inplace=True)

    # Asegurar columnas numéricas y fechas
    df['Fecha_Pedido'] = pd.to_datetime(df['Fecha_Pedido'], errors='coerce', dayfirst=True)
    df['Fecha_Entrega'] = pd.to_datetime(df['Fecha_Entrega'], errors='coerce', dayfirst=True)
    df['Costo'] = pd.to_numeric(df.get('Costo', 0), errors='coerce')
    df['Adelanto'] = pd.to_numeric(df.get('Adelanto', 0), errors='coerce')

    # Panel Resumen
    total_trabajos = len(df)
    total_costo = df['Costo'].sum()
    total_adelanto = df['Adelanto'].sum()

    col1, col2, col3 = st.columns(3)
    col1.metric("📦 Total de Trabajos", total_trabajos)
    col2.metric("💰 Ingresos Proyectados", f"S/. {total_costo:,.2f}")
    col3.metric("💸 Adelantos Recibidos", f"S/. {total_adelanto:,.2f}")

    # Gráfico por estado
    if 'Estado' in df.columns:
        fig_estado = px.histogram(df, x='Estado', color='Estado', title="Distribución por Estado")
        st.plotly_chart(fig_estado, use_container_width=True)

    # Ranking de desarrolladores
    if 'Desarrollo' in df.columns:
        dev_count = df['Desarrollo'].value_counts().reset_index()
        dev_count.columns = ['Desarrollador', 'Cantidad']
        fig_dev = px.bar(dev_count, x='Desarrollador', y='Cantidad', title="Ranking de Desarrolladores")
        st.plotly_chart(fig_dev, use_container_width=True)

    # Tareas pendientes
    if 'Estado' in df.columns:
        st.subheader("📌 Tareas Pendientes")
        pendientes = df[df['Estado'].str.lower().str.contains("pendiente", na=False)]
        if not pendientes.empty:
            st.dataframe(pendientes[['Fecha_Entrega', 'Tipo_Tarea', 'Descripcion', 'Desarrollo', 'Grupo']].sort_values("Fecha_Entrega"))

    # Observaciones
    if 'Observacion' in df.columns:
        st.subheader("📝 Observaciones Registradas")
        observaciones = df[df['Observacion'].notna() & (df['Observacion'].str.strip() != "")]
        if not observaciones.empty:
            st.dataframe(observaciones[['Fecha_Entrega', 'Tipo_Tarea', 'Observacion', 'Grupo']].sort_values("Fecha_Entrega"))
else:
    st.info("Sube un archivo Excel para comenzar.")
