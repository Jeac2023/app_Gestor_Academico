import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import re

st.set_page_config(page_title="Gestor de Trabajos Académicos", layout="wide")
st.title("📚 Vista de Javier - Calendario de Tareas Pendientes")

uploaded_file = st.file_uploader("Sube tu archivo Excel", type=["xlsx"])

if uploaded_file:
    excel_file = pd.ExcelFile(uploaded_file)
    sheet_names = excel_file.sheet_names
    selected_sheets = sheet_names

    dfs = []
    for sheet in selected_sheets:
        df = excel_file.parse(sheet)
        df.columns = df.iloc[0]
        df = df[1:]
        df['Grupo'] = sheet
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)

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

    df['Fecha_Pedido'] = pd.to_datetime(df['Fecha_Pedido'], errors='coerce', dayfirst=True)
    df['Fecha_Entrega'] = pd.to_datetime(df['Fecha_Entrega'], errors='coerce', dayfirst=True)
    df['Costo'] = pd.to_numeric(df.get('Costo', 0), errors='coerce')
    df['Adelanto'] = pd.to_numeric(df.get('Adelanto', 0), errors='coerce')

    # Filtrar por Javier y pendientes
    hoy = datetime.today().date()
    javier_df = df[(df['Desarrollo'].str.lower().str.strip() == 'javier') &
                   (df['Estado'].str.lower().str.contains("pendiente", na=False))]
    javier_df = javier_df.dropna(subset=['Fecha_Entrega'])
    javier_df['Fecha_Entrega'] = pd.to_datetime(javier_df['Fecha_Entrega']).dt.date

    # Extraer hora desde descripción con regex
    def extraer_hora(texto):
        if pd.isna(texto): return None
        match = re.search(r'(\\d{1,2}[:.h]\\d{2})', texto)
        return match.group(1) if match else None

    javier_df['Hora_Entrega'] = javier_df['Descripcion'].apply(extraer_hora)
    javier_df['Hora_Entrega'] = pd.to_datetime(javier_df['Hora_Entrega'], format='%H:%M', errors='coerce').dt.time

    # Filtro por día
    dias = sorted(javier_df['Fecha_Entrega'].unique())
    dia_seleccionado = st.selectbox("Selecciona una fecha para ver tus tareas", dias, format_func=lambda d: d.strftime('%d/%m/%Y'))

    # Agrupar por grupo
    st.subheader(f"📆 Tareas para el {dia_seleccionado.strftime('%d/%m/%Y')}")
    tareas_dia = javier_df[javier_df['Fecha_Entrega'] == dia_seleccionado]
    tareas_dia = tareas_dia.sort_values(by='Hora_Entrega')

    grupos = tareas_dia['Grupo'].unique()
    if 'completadas' not in st.session_state:
        st.session_state['completadas'] = set()

    for grupo in grupos:
        st.markdown(f"### 🏷️ Grupo: {grupo}")
        tareas_grupo = tareas_dia[tareas_dia['Grupo'] == grupo]

        for idx, row in tareas_grupo.iterrows():
            key = f"tarea_{row['Codigo']}_{row['Fecha_Entrega']}"
            completado = key in st.session_state['completadas']

            col1, col2 = st.columns([0.05, 0.95])
            with col1:
                check = st.checkbox("", value=completado, key=key)
                if check:
                    st.session_state['completadas'].add(key)
                else:
                    st.session_state['completadas'].discard(key)

            with col2:
                hora = row['Hora_Entrega'].strftime('%H:%M') if pd.notna(row['Hora_Entrega']) else "(sin hora)"
                estado = "✅ Completado" if check else "⏳ Pendiente"
                st.markdown(f"**{hora}** — {row['Tipo_Tarea']} — `S/. {row['Costo']}` — **{estado}**")
                st.caption(f"Código: {row['Codigo']} | {row['Descripcion']}")
else:
    st.info("Sube un archivo Excel para comenzar.")
