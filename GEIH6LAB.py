import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os
import io

# Rutas de red para cargar los 6 archivos CSV
network_paths = [
    r"\\ruta_red\carpeta\Matriz para GEIH_1.csv",
    r"\\ruta_red\carpeta\Matriz para GEIH_2.csv",
    r"\\ruta_red\carpeta\Matriz para GEIH_3.csv",
    r"\\ruta_red\carpeta\Matriz para GEIH_4.csv",
    r"\\ruta_red\carpeta\Matriz para GEIH_5.csv",
    r"\\ruta_red\carpeta\Matriz para GEIH_6.csv"
]

# Verifica si la imagen existe antes de mostrarla y permite tamaño ajustable
img_path = 'img/EncabezadoG.png'
if os.path.exists(img_path):
    st.image(img_path, use_container_width=False, width=420)
else:
    st.warning(f"No se encontró la imagen: {img_path}")

st.markdown("<h1 style='text-align: center; font-weight: bold;font-size: 36px;'>Integración y Análisis de Información Grupos de Exhumaciones e Identificación Humana</h1>", unsafe_allow_html=True)

def load_csv_skip_first_row(file_or_path, is_uploaded=False):
    try:
        if is_uploaded:
            df = pd.read_csv(file_or_path, header=1)
            file_name = file_or_path.name
        else:
            df = pd.read_csv(file_or_path, header=1)
            file_name = os.path.basename(file_or_path)
        # Eliminar columnas Unnamed si existen
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
        # Asignar tipo fecha a columnas 10, 11 y 12 (año, mes, día)
        if len(df.columns) > 12:
            col_year = df.columns[10]
            col_month = df.columns[11]
            col_day = df.columns[12]
            # Crear columna de fecha combinando año, mes y día
            df["FECHA_COMPLETA"] = pd.to_datetime(
                df[[col_year, col_month, col_day]].astype(str).agg('-'.join, axis=1),
                errors='coerce',
                format='%Y-%m-%d'
            )
        # Agregar columna de ciudad usando el nombre del archivo
        df["ciudad_archivo"] = os.path.splitext(file_name)[0]
        return df.reset_index(drop=True)
    except Exception as e:
        st.error(f"No se pudo cargar el archivo: {file_or_path}\nError: {e}")
        return pd.DataFrame()

# Cargar archivos de red
st.markdown(
    "<h2 style='font-size:20px; color:darkblue;'>Cargar archivos desde carpetas compartidas de Red</h2>",
    unsafe_allow_html=True
)
# dfs_red = []
# for path in network_paths:
#     df = load_csv_skip_first_row(path, is_uploaded=False)
#     if not df.empty:
#         st.write(f"Archivo: {path.split('\\')[-1]}")
#         st.write(f"Filas: {df.shape[0]}, Columnas: {df.shape[1]}")
#         st.dataframe(df.head(3))
#         dfs_red.append(df)

# if len(dfs_red) == 0:
#     st.warning("No se cargaron archivos desde las carpetas de red.")

# Permitir al usuario subir o seleccionar dos archivos CSV adicionales
st.markdown(
    "<h2 style='font-size:20px; color:darkblue;'>Seleccionar archivos desde carpeta Manualmente</h2>",
    unsafe_allow_html=True
)
uploaded_files = st.file_uploader("Sube 6 archivos de seccionales", accept_multiple_files=True, type=["csv"], key="user_files")
dfs_user = []
for uploaded_file in uploaded_files:
    df_user = load_csv_skip_first_row(uploaded_file, is_uploaded=True)
    if not df_user.empty:
        st.write(f"Archivo: {uploaded_file.name}")
        st.write(f"Filas: {df_user.shape[0]}, Columnas: {df_user.shape[1]}")
        st.dataframe(df_user.head(3))
        dfs_user.append(df_user)

# Consolidar todos los dataframes en uno solo
st.markdown("<h1 style='text-align: center; font-weight: bold;font-size: 26px;'>Datos Consolidados GEIH CTI a nivel nacional</h1>", unsafe_allow_html=True)
all_dfs = dfs_red + dfs_user

if all_dfs:
    df_combined = pd.concat(all_dfs, ignore_index=True)

    # Mostrar un resumen básico
    st.write(f"DataFrame combinado: {df_combined.shape[0]} filas y {df_combined.shape[1]} columnas.")
    st.dataframe(df_combined.head())

    # Dashboard
    st.header("Cuadros de mando e insights")

    # Línea de tiempo - Las fechas están en las columnas J, K y L (índices 9, 10, 11)
    st.subheader("Línea de tiempo (columnas Año de hallazgo o  Año de exhumación)")
    date_cols = []
    for idx in [6, 7]:  # Índices 6, 7, 8 corresponden a las columnas J, K, L
        if idx < len(df_combined.columns):
            date_cols.append(df_combined.columns[idx])
    if date_cols:
        for col in date_cols:
            df_combined[col] = pd.to_datetime(df_combined[col], errors='coerce')
        # Unir todas las fechas en una sola columna para el gráfico
        fechas = pd.concat([df_combined[col].dropna() for col in date_cols])
        timeline = fechas.value_counts().sort_index().reset_index()
        timeline.columns = ['Fecha', 'Conteo']

        if not timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(timeline['Fecha'], timeline['Conteo'], marker='o')
            ax.set_title("Línea de Tiempo - Conteo por Fecha (J, K, L)")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Conteo")
            plt.xticks(rotation=45)
            st.pyplot(fig)
        else:
            st.info("No hay datos de fecha válidos en las columnas J, K o L.")
    else:
        st.info("No se encontraron las columnas J, K y L para la línea de tiempo.")

    # Tarjetas con insights (Ejemplo simple con estadísticas rápidas)
    st.subheader("Insights destacados")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Filas totales", df_combined.shape[0])
    col2.metric("Columnas totales", df_combined.shape[1])
    col3.metric("Datos nulos (%)", round(df_combined.isnull().mean().mean() * 100, 2))
    col4.metric("Valores únicos cols.", sum(df_combined.nunique() > 1))

    # Top 10 value counts: elegir una columna categórica para mostrar
    st.subheader("Top 10 valores más frecuentes")
    categorical_cols = df_combined.select_dtypes(include=["object", "category"]).columns.tolist()
    if categorical_cols:
        col = st.selectbox("Selecciona columna para top 10 value counts", categorical_cols)
        top10 = df_combined[col].value_counts().nlargest(10)
        st.bar_chart(top10)
    else:
        st.info("No hay columnas categóricas para mostrar value counts.")

    # Descarga del archivo consolidado en formato Excel
    st.header("Descargar archivo consolidado")
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_combined.to_excel(writer, index=False, sheet_name='Consolidado')
    output.seek(0)
    st.download_button(
        label="Descargar XLSX combinado",
        data=output,
        file_name='archivo_consolidado.xlsx',
        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
else:
    st.info("Carga archivos para mostrar el análisis.")

