import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

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

    st.subheader("📌 Vista de Javier - Pendientes por Fecha")

    hoy = datetime.today().date()
    manana = hoy + timedelta(days=1)

    javier_df = df[(df['Desarrollo'].str.lower().str.strip() == 'javier') &
                   (df['Estado'].str.lower().str.contains("pendiente", na=False))]

    pendientes_hoy = javier_df[javier_df['Fecha_Entrega'].dt.date == hoy]
    pendientes_manana = javier_df[javier_df['Fecha_Entrega'].dt.date == manana]
    futuros = javier_df[javier_df['Fecha_Entrega'].dt.date > manana]

    tab1, tab2, tab3 = st.tabs(["Hoy", "Mañana", "Próximos Días"])

    with tab1:
        st.write(f"### 📅 Pendientes para hoy ({hoy})")
        st.dataframe(pendientes_hoy[['Codigo', 'Fecha_Entrega', 'Tipo_Tarea', 'Descripcion', 'Costo', 'Grupo']])

    with tab2:
        st.write(f"### 📅 Pendientes para mañana ({manana})")
        st.dataframe(pendientes_manana[['Codigo', 'Fecha_Entrega', 'Tipo_Tarea', 'Descripcion', 'Costo', 'Grupo']])

    with tab3:
        st.write("### 📅 Pendientes futuros")
        st.dataframe(futuros[['Codigo', 'Fecha_Entrega', 'Tipo_Tarea', 'Descripcion', 'Costo', 'Grupo']])

else:
    st.info("Sube un archivo Excel para comenzar.")
