import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="Gestor de Trabajos Académicos", layout="wide")
st.title("📚 Vista de Javier - Calendario de Tareas por Grupo")

# URLs de las hojas de cálculo públicas
sheet_urls = {
    "GENIOS EN LA EDUCACIÓN": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnZa_3M1gfrT1h5Uji3FhLyhUZg6UkMVMVWdM6zA2Za_NJX-LzT1mgD4MaP_Mkhw/pub?gid=464200169&single=true&output=csv",
    "TU ALIADO ACADÉMICO": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnZa_3M1gfrT1h5Uji3FhLyhUZg6UkMVMVWdM6zA2Za_NJX-LzT1mgD4MaP_Mkhw/pub?gid=420707983&single=true&output=csv",
    "ALIADOS DEL CONOCIMIENTO": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnZa_3M1gfrT1h5Uji3FhLyhUZg6UkMVMVWdM6zA2Za_NJX-LzT1mgD4MaP_Mkhw/pub?gid=435353295&single=true&output=csv",
    "TURBOTAREAS": "https://docs.google.com/spreadsheets/d/e/2PACX-1vSnZa_3M1gfrT1h5Uji3FhLyhUZg6UkMVMVWdM6zA2Za_NJX-LzT1mgD4MaP_Mkhw/pub?gid=1250127946&single=true&output=csv",
}

# Extraer hora en formato AM/PM desde descripción
def extraer_hora(texto):
    if pd.isna(texto):
        return None
    texto = str(texto).strip().lower()
    match = re.search(r'(\d{1,2}:\d{2}\s?(am|pm))', texto)
    if match:
        try:
            return pd.to_datetime(match.group(1), format='%I:%M %p').time()
        except:
            return None
    return None

# Cargar datos
dfs = []
for grupo, url in sheet_urls.items():
    try:
        df = pd.read_csv(url)
        df.columns = df.iloc[0]
        df = df[1:]
        df['Grupo'] = grupo
        dfs.append(df)
    except Exception as e:
        st.warning(f"No se pudo cargar la hoja {grupo}: {e}")

if dfs:
    df = pd.concat(dfs, ignore_index=True)

    # Renombrar columnas
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

    # Procesamiento de columnas
    df['Fecha_Pedido'] = pd.to_datetime(df['Fecha_Pedido'], errors='coerce', dayfirst=True)
    df['Fecha_Entrega'] = pd.to_datetime(df['Fecha_Entrega'], errors='coerce', dayfirst=True)
    df['Costo'] = pd.to_numeric(df.get('Costo', 0), errors='coerce')
    df['Adelanto'] = pd.to_numeric(df.get('Adelanto', 0), errors='coerce')

    # Filtro por Javier y pendientes
    df = df[(df['Desarrollo'].str.lower().str.strip() == 'javier') &
            (df['Estado'].str.lower().str.contains("pendiente", na=False))]
    df = df.dropna(subset=['Fecha_Entrega'])
    df['Fecha_Entrega'] = pd.to_datetime(df['Fecha_Entrega']).dt.date
    df['Hora_Entrega'] = df['Descripcion'].apply(extraer_hora)

    # Selección de fecha
    dias = sorted(df['Fecha_Entrega'].unique())
    dia_seleccionado = st.selectbox("Selecciona una fecha", dias, format_func=lambda d: d.strftime('%d/%m/%Y'))

    st.markdown(f"### 📆 Calendario para {dia_seleccionado.strftime('%d/%m/%Y')}")
    tareas_dia = df[df['Fecha_Entrega'] == dia_seleccionado].sort_values(by='Hora_Entrega')

    grupos = list(sheet_urls.keys())
    horas = sorted(tareas_dia['Hora_Entrega'].dropna().unique())

    if 'completadas' not in st.session_state:
        st.session_state['completadas'] = set()

    mostrar_solo_pendientes = st.checkbox("Mostrar solo tareas no completadas", value=False)

    table_data = []
    for hora in horas:
        fila = [hora.strftime('%I:%M %p') if hora else ""]
        for grupo in grupos:
            tareas = tareas_dia[(tareas_dia['Grupo'] == grupo) & (tareas_dia['Hora_Entrega'] == hora)]
            celdas = []
            for idx, row in tareas.iterrows():
                key = f"{row['Codigo']}_{row['Fecha_Entrega']}"
                completado = key in st.session_state['completadas']
                if mostrar_solo_pendientes and completado:
                    continue
                texto = f"✅ {row['Tipo_Tarea']} (S/. {row['Costo']})" if completado else f"⏳ {row['Tipo_Tarea']} (S/. {row['Costo']})"
                checkbox = st.checkbox("", key=key, value=completado)
                if checkbox:
                    st.session_state['completadas'].add(key)
                else:
                    st.session_state['completadas'].discard(key)
                celdas.append(f"{texto}<br><small>{row['Descripcion']}</small>")
            fila.append("<br><br>".join(celdas) if celdas else "")
        table_data.append(fila)

    columns = ['Hora'] + grupos
    df_display = pd.DataFrame(table_data, columns=columns)
    st.markdown(df_display.to_html(escape=False, index=False), unsafe_allow_html=True)

else:
    st.warning("No se pudo cargar ningún dato desde Google Sheets.")
