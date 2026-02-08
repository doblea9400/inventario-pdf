import streamlit as st
import pandas as pd
import io
from pdf_to_csv_textparse import extract_from_text # Importamos tu lógica

# Configuración de la página
st.set_page_config(page_title="Convertidor PDF a WordPress", page_icon="📦")

st.title("🚀 Conversor de Inventario")
st.markdown("Sube tu PDF de **Comercial Super C** para generar el CSV de WordPress.")

# 1. Selector de archivos
uploaded_file = st.file_uploader("Elige el archivo PDF", type="pdf")

if uploaded_file is not None:
    with st.spinner('Procesando PDF...'):
        # Guardamos temporalmente el archivo subido para que tu script lo lea
        with open("temp_upload.pdf", "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # 2. Ejecutar tu función de extracción
        rows, rejected = extract_from_text("temp_upload.pdf")
        
    if rows:
        # Convertimos a DataFrame para mostrarlo bonito en la web
        df = pd.DataFrame(rows, columns=['SKU', 'Nombre', 'Stock', 'Precio'])
        
        st.success(f"✅ ¡Éxito! Se encontraron {len(rows)} productos.")
        
        # 3. Mostrar vista previa
        st.subheader("Vista previa de los datos")
        st.dataframe(df, use_container_width=True)
        
        # 4. Botón de descarga
        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False, encoding='utf-8')
        
        st.download_button(
            label="⬇️ Descargar CSV para WordPress",
            data=csv_buffer.getvalue(),
            file_name="importar_a_wordpress.csv",
            mime="text/csv",
        )
    else:
        st.error("No se pudieron extraer datos. Revisa el formato del PDF.")

    # Mostrar errores de líneas rechazadas (opcional)
    if rejected:
        with st.expander("Ver líneas rechazadas (errores de lectura)"):
            for p, ln in rejected[:20]:
                st.text(f"Pág {p}: {ln}")