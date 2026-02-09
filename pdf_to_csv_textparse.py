import pdfplumber
import csv
import sys
import re

# Intentar usar wordsegment si está instalado
try:
    from wordsegment import load, segment
    load()
    HAS_WORDSEG = True
except Exception:
    HAS_WORDSEG = False

# ---------- CONFIG ----------
OUT_CSV = "listado_limpio.csv"
# lista de unidades y tokens que queremos separar como palabras independientes
UNITS = ['G','GR','ML','L','KG','UNID','UN','X','X24','X12','X6','X30']
# --------------------------

def clean_number_token(s):
    s = s.strip()
    # normalizar 2.605,71 -> 2605.71 ; 1.234 -> 1234
    if re.search(r'\d+\.\d+,\d+', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    return s

def repair_name_with_wordsegment(name):
    """
    1) Inserta espacios alrededor de números y unidades.
    2) Usa wordsegment para segmentar la parte textual pegada.
    3) Reconstruye manteniendo números y unidades.
    """
    # 1) separar números de letras: "MUNDOMARINO80G" -> "MUNDOMARINO 80 G"
    # insertar espacio antes y después de números
    s = re.sub(r'(?<=\D)(?=\d)', ' ', name)   # letra->número
    s = re.sub(r'(?<=\d)(?=\D)', ' ', s)      # número->letra
    # normalizar espacios múltiples
    s = " ".join(s.split())

    tokens = s.split()
    out_tokens = []
    for t in tokens:
        # si es número o contiene dígitos, dejar tal cual (pero limpiar)
        if re.search(r'\d', t):
            out_tokens.append(t)
            continue
        # si es unidad conocida (ej G, ML) dejar en mayúscula
        if t.upper() in UNITS:
            out_tokens.append(t.upper())
            continue
        # usar wordsegment: requiere texto en minúsculas
        seg = segment(t.lower())
        # capitalizar cada palabra y añadir
        seg_cap = [w.upper() for w in seg]
        out_tokens.extend(seg_cap)
    # unir y limpiar espacios redundantes
    return " ".join(out_tokens).strip()

def repair_name_with_regex(name):
    """
    Heurística sin dependencias:
    - separa números
    - separa unidades comunes
    - inserta espacios entre letras y mayúsculas si detecta patrones
    """
    s = name.strip()
    # separar números de letras
    s = re.sub(r'(?<=\D)(?=\d)', ' ', s)
    s = re.sub(r'(?<=\d)(?=\D)', ' ', s)
    # insertar espacio antes de unidades comunes (ej: 80G -> 80 G)
    for u in UNITS:
        s = re.sub(r'(?i)(\d)'+re.escape(u)+r'\b', r'\1 ' + u, s)
    # intentar separar palabras compuestas en mayúsculas: insertar espacio entre secuencias de letras cuando hay cambio de patrón
    # ejemplo: ACEITEDEOLIVA -> ACEITE DE OLIVA (intento simple: separar por grupos de 3-)
    s = re.sub(r'([A-Z]{3,})(?=[A-Z])', lambda m: " ".join(re.findall(r'.{1,6}', m.group(1))), s)
    # limpiar múltiples espacios
    s = " ".join(s.split())
    # si queda todo junto (sin espacios) y es largo, intentar insertar espacios cada 6 caracteres como último recurso
    if ' ' not in s and len(s) > 12:
        s = " ".join([s[i:i+6] for i in range(0, len(s), 6)])
    return s.strip()

# función principal de reparación que el script usará
def repair_name(name):
    # limpiar caracteres raros
    name = name.replace('"', '').replace("'", "").strip()
    # si ya tiene espacios suficientes, devolver tal cual
    if len(name.split()) >= 2:
        return " ".join(name.split())
    # preferir wordsegment si está disponible
    if HAS_WORDSEG:
        try:
            return repair_name_with_wordsegment(name)
        except Exception:
            return repair_name_with_regex(name)
    else:
        return repair_name_with_regex(name)

# ---------- extracción (tu técnica de guillotina adaptada) ----------
def extract_data(pdf_path):
    rows = []
    price_pattern = re.compile(r'(\d+[\d\.,\s]+)$')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            for line in text.splitlines():
                line = line.strip().replace('"', '')
                
                # Buscamos líneas que empiecen con el SKU (número largo)
                if re.match(r'^\d{7,}', line):
                    parts = line.split(maxsplit=1)
                    if len(parts) < 2: continue
                    sku = parts[0]
                    resto = parts[1]
                    
                    match_precios = price_pattern.search(resto)
                    if match_precios:
                        bloque_precios = match_precios.group(1).strip()
                        nombre_sucio = resto.replace(bloque_precios, "").strip()
                        
                        # REPARAR NOMBRE: usar la función repair_name
                        nombre = repair_name(nombre_sucio)
                        
                        # 3. Procesar los números del bloque final
                        nums = bloque_precios.split()
                        if len(nums) >= 2:
                            stock = clean_number_token(nums[0])
                            precio = nums[-1].strip()
                            precio = precio.replace('.', '').replace(',', '.') if re.search(r'\d+\.\d+,\d+', precio) else precio.replace(',', '.')
                            rows.append([sku, nombre, stock, precio])

    return rows

def main(pdf_file):
    print(f"[INFO] Aplicando técnica de guillotina: {pdf_file}")
    if HAS_WORDSEG:
        print("[INFO] wordsegment disponible: usando segmentación automática.")
    else:
        print("[INFO] wordsegment NO disponible: usando heurística regex.")
    data = extract_data(pdf_file)
    
    if data:
        with open(OUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['SKU', 'Nombre', 'Stock', 'Precio'])
            writer.writerows(data)
        print(f"✅ ¡ÉXITO! {len(data)} productos extraídos.")
        res = data[0]
        print(f"[REVISIÓN] SKU: {res[0]} | NOMBRE: {res[1]} | STOCK: {res[2]} | PRECIO: {res[3]}")
    else:
        print("❌ No se encontró el patrón de datos.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main("listado.pdf")
