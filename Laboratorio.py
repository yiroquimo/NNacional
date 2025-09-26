import streamlit as st
import pandas as pd
import difflib

st.title("Comparar, Analizar y Unir Archivos CSV")

# Subida de archivos
file_lunes = st.file_uploader("Sube prueba_todos_lunes.csv", type=['csv'])
file_martes = st.file_uploader("Sube EXHUMACIONES_martes.csv", type=['csv'])

# Inicialización de variables para evitar errores si falta algún archivo
df_lunes = None
df_martes = None

if file_lunes:
    try:
        df_lunes = pd.read_csv(file_lunes, encoding="utf-8")
    except UnicodeDecodeError:
        try:
            df_lunes = pd.read_csv(file_lunes, encoding="latin1")
        except Exception as e:
            st.error(f"Error al leer prueba_todos_lunes.csv: {e}")
    except Exception as e:
        st.error(f"Error al leer prueba_todos_lunes.csv: {e}")
if file_martes:
    try:
        df_martes = pd.read_csv(file_martes, encoding="utf-8", on_bad_lines='skip')
    except UnicodeDecodeError:
        try:
            df_martes = pd.read_csv(file_martes, encoding="latin1", on_bad_lines='skip')
        except Exception as e:
            st.error(f"Error al leer EXHUMACIONES_martes.csv: {e}")
    except Exception as e:
        st.error(f"Error al leer EXHUMACIONES_martes.csv: {e}")

# Solo continuar si ambos archivos fueron cargados correctamente
if df_lunes is not None and df_martes is not None:
    st.subheader("Resumen de prueba_todos_lunes.csv")
    st.write(f"Filas: {df_lunes.shape[0]}, Columnas: {df_lunes.shape[1]}")
    st.write(df_lunes.head())

    st.subheader("Resumen de EXHUMACIONES_martes.csv")
    st.write(f"Filas: {df_martes.shape[0]}, Columnas: {df_martes.shape[1]}")
    st.write(df_martes.head())

    # Selección de columnas a comparar
    columnas_lunes = st.multiselect(
        "Selecciona la(s) columna(s) de prueba_todos_lunes.csv para comparar:",
        options=df_lunes.columns.tolist(),
        default=['NOMBRE OCCISO'] if 'NOMBRE OCCISO' in df_lunes.columns else []
    )
    columnas_martes = st.multiselect(
        "Selecciona la(s) columna(s) de EXHUMACIONES_martes.csv para comparar:",
        options=df_martes.columns.tolist(),
        default=['NOMBRE OCCISO'] if 'NOMBRE OCCISO' in df_martes.columns else []
    )

    # Solo continuar si el usuario seleccionó columnas en ambos archivos
    if columnas_lunes and columnas_martes:
        # Selección de sensibilidad (umbral de similitud)
        sensibilidad = st.slider(
            "Grado de sensibilidad para coincidencias aproximadas (0.0 = menos estricto, 1.0 = más estricto):",
            min_value=0.0, max_value=1.0, value=0.8, step=0.01
        )

        # Mostrar cuadro de evolución de búsqueda y tiempo estimado
        total_comparaciones = len(df_lunes) * len(df_martes)
        tiempo_estimado = total_comparaciones / 10000
        st.info(f"Se realizarán aproximadamente {total_comparaciones:,} comparaciones. "
                f"Tiempo estimado: {tiempo_estimado:.1f} segundos.")

        # --- Comparación aproximada de registros por nombre ---
        aproximados = []
        usados_martes = set()
        progress_bar = st.progress(0, text="Comparando registros...")

        for idx_lunes, row_lunes in df_lunes.iterrows():
            valor_lunes = " ".join([str(row_lunes[col]) for col in columnas_lunes])
            valores_martes_disponibles = df_martes.loc[~df_martes.index.isin(usados_martes), columnas_martes].astype(str).agg(" ".join, axis=1)
            valores_martes_disponibles = valores_martes_disponibles.tolist()
            mejores = difflib.get_close_matches(
                valor_lunes,
                valores_martes_disponibles,
                n=1,
                cutoff=sensibilidad
            )
            if mejores:
                valor_martes = mejores[0]
                mask_disponibles = ~df_martes.index.isin(usados_martes)
                indices_disponibles = df_martes.index[mask_disponibles]
                idx_martes = None
                for i, v in zip(indices_disponibles, valores_martes_disponibles):
                    if v == valor_martes:
                        idx_martes = i
                        break
                if idx_martes is not None:
                    usados_martes.add(idx_martes)
                    similitud = difflib.SequenceMatcher(None, valor_lunes, valor_martes).ratio()
                    aproximados.append({
                        'index_lunes': idx_lunes,
                        'index_martes': idx_martes,
                        'similitud': round(similitud, 2),
                        'valor_lunes': valor_lunes,
                        'valor_martes': valor_martes,
                        'registro_lunes': row_lunes.to_dict(),
                        'registro_martes': df_martes.loc[idx_martes].to_dict()
                    })
            # Actualizar barra de progreso
            progress_bar.progress((idx_lunes + 1) / len(df_lunes), text="Comparando registros...")

        progress_bar.empty()

        # Mostrar resultados de la comparación aproximada en listas seleccionables
        st.subheader("Resultados de la comparación aproximada")
        if aproximados:
            indices = [
                f"Lunes idx {m['index_lunes']} ({m['valor_lunes']}) | "
                f"Martes idx {m['index_martes']} ({m['valor_martes']}) | "
                f"Similitud: {m['similitud']}"
                for m in aproximados
            ]
            seleccionados = st.multiselect(
                "Selecciona las coincidencias que deseas unir:",
                options=indices
            )
            if seleccionados:
                st.success("Coincidencias seleccionadas. Presiona el botón para generar el archivo unido.")

                # Mostrar lista de coincidencias seleccionadas con detalle de archivo y columna
                st.markdown("### Lista de coincidencias seleccionadas")
                lista_coincidencias = []
                for idx, label in enumerate(indices):
                    if label in seleccionados:
                        reg_lunes = aproximados[idx]['registro_lunes']
                        reg_martes = aproximados[idx]['registro_martes']
                        # Mostrar columnas seleccionadas y sus valores
                        detalle = {
                            "Archivo": "prueba_todos_lunes.csv",
                            "Índice": aproximados[idx]['index_lunes'],
                        }
                        for col in columnas_lunes:
                            detalle[f"Columna: {col}"] = reg_lunes.get(col, "")
                        lista_coincidencias.append(detalle)

                        detalle2 = {
                            "Archivo": "EXHUMACIONES_martes.csv",
                            "Índice": aproximados[idx]['index_martes'],
                        }
                        for col in columnas_martes:
                            detalle2[f"Columna: {col}"] = reg_martes.get(col, "")
                        lista_coincidencias.append(detalle2)

                st.dataframe(pd.DataFrame(lista_coincidencias))

                if st.button("Generar archivo unido"):
                    # Extraer los registros seleccionados
                    registros_unidos = []
                    for idx, label in enumerate(indices):
                        if label in seleccionados:
                            reg_lunes = aproximados[idx]['registro_lunes']
                            reg_martes = aproximados[idx]['registro_martes']
                            registro_unido = {**reg_lunes, **reg_martes}
                            registros_unidos.append(registro_unido)
                    df_unido = pd.DataFrame(registros_unidos)
                    st.success(f"Archivo generado con {len(df_unido)} registros unidos.")
                    st.dataframe(df_unido)
                    # Botón para descargar
                    csv = df_unido.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="Descargar archivo unido CSV",
                        data=csv,
                        file_name="registros_unidos.csv",
                        mime='text/csv'
                    )
            else:
                st.info("Selecciona coincidencias para poder unir y generar el archivo.")
    else:
        st.warning("Selecciona al menos una columna en ambos archivos para comparar.")
else:
    st.info("Por favor, sube ambos archivos para proceder.")
