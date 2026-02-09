import pdfplumber
import csv
import re
import io
import streamlit as st

# Intentar usar wordsegment
try:
    from wordsegment import load, segment
    load()
    HAS_WORDSEG = True
except Exception:
    HAS_WORDSEG = False

# ---------- CONFIG ----------
UNITS = ['G','GR','ML','L','KG','UNID','UN','X','X24','X12','X6','X30']

def clean_number_token(s):
    s = s.strip()
    if re.search(r'\d+\.\d+,\d+', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    return s

def repair_name_with_wordsegment(name):
    s = re.sub(r'(?<=\D)(?=\d)', ' ', name)
    s = re.sub(r'(?<=\d)(?=\D)', ' ', s)
    s = " ".join(s.split())
    tokens = s.split()
    out_tokens = []
    for t in tokens:
        if re.search(r'\d', t):
            out_tokens.append(t)
            continue
        if t.upper() in UNITS:
            out_tokens.append(t.upper())
            continue
        seg = segment(t.lower())
        seg_cap = [w.upper() for w in seg]
        out_tokens.extend(seg_cap)
    return " ".join(out_tokens).strip()

def repair_name_with_regex(name):
    s = name.strip()
    s = re.sub(r'(?<=\D)(?=\d)', ' ', s)
    s = re.sub(r'(?<=\d)(?=\D)', ' ', s)
    for u in UNITS:
        s = re.sub(r'(?i)(\d)'+re.escape(u)+r'\b', r'\1 ' + u, s)
    s = re.sub(r'([A-Z]{3,})(?=[A-Z])', lambda m: " ".join(re.findall(r'.{1,6}', m.group(1))), s)
    s = " ".join(s.split())
    if ' ' not in s and len(s) > 12:
        s = " ".join([s[i:i+6] for i in range(0, len(s), 6)])
    return s.strip()

def repair_name(name):
    name = name.replace('"', '').replace("'", "").strip()
    if len(name.split()) >= 2:
        return " ".join(name.split())
    if HAS_WORDSEG:
        try:
            return repair_name_with_wordsegment(name)
        except Exception:
            return repair_name_with_regex(name)
    return repair_name_with_regex(name)

def extract_data(pdf_file):
    rows = []
    price_pattern = re.compile(r'(\d+[\d\.,\s]+)$')

    # Abrimos el PDF desde el objeto de memoria de Streamlit
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            for line in text.splitlines():
                line = line.strip().replace('"', '')
                if re.match(r'^\d{7,}', line):
                    parts = line.split(maxsplit=1)
                    if len(parts) < 2: continue
                    sku, resto = parts[0], parts[1]
                    
                    match_precios = price_pattern.search(resto)
                    if match_precios:
                        bloque_precios = match_precios.group(1).strip()
                        nombre_sucio = resto.replace(bloque_precios, "").strip()
                        nombre = repair_name(nombre_sucio)
                        
                        nums = bloque_precios.split()
                        if len(nums) >= 2:
                            stock = clean_number_token(nums[0])
                            precio = nums[-1].strip()
                            precio = precio.replace('.', '').replace(',', '.') if re.search(r'\d+\.\d+,\d+', precio) else precio.replace(',', '.')
                            rows.append([sku, nombre, stock, precio])
    return rows

# ---------- INTERFAZ STREAMLIT ----------
st.set_page_config(page_title="PDF a CSV Pro", page_icon="📄")
st.title("🚀 Extractor de Inventario Pro")
st.markdown("Sube tu PDF y separaremos los nombres pegados automáticamente usando NLP.")

uploaded_file = st.file_uploader("Elige tu archivo PDF", type="pdf")

if uploaded_file is not None:
    if st.button("Procesar Inventario"):
        with st.spinner('Analizando y segmentando palabras...'):
            data = extract_data(uploaded_file)
            
        if data:
            st.success(f"¡Éxito! Se encontraron {len(data)} productos.")
            
            # Crear CSV en memoria
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['SKU', 'Nombre', 'Stock', 'Precio'])
            writer.writerows(data)
            
            # Mostrar vista previa
            st.table(data[:10]) 
            
            # Botón de descarga
            st.download_button(
                label="📥 Descargar CSV Limpio",
                data=output.getvalue(),
                file_name="inventario_reparado.csv",
                mime="text/csv"
            )
        else:
            st.error("No se detectaron datos en el formato esperado.")
