import pdfplumber
import re
import csv
from pathlib import Path

# ---------- CONFIG ----------
PRICE_IS_LAST = True   # usar la última columna numérica como "Precio"
OUT_CSV = "listado.csv"
REJECT_FILE = "rejected_lines.txt"
DEBUG_PRINT = True
# --------------------------

def clean_number(s):
    if s is None: return ''
    s = str(s).strip().replace(' ', '')
    # 2.605,71 -> 2605.71 ; 1.234 -> 1234
    if re.search(r'\d+\.\d+,\d+', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    return s

# Regex tentativa: SKU (digits) + espacio + descripcion (cualquier cosa no numérica al final) + stock + 4 números monetarios
LINE_RE = re.compile(
    r'^\s*(?P<sku>\d{1,})\s+(?P<desc>.+?)\s+(?P<stock>-?\d+(?:\.\d+)?)\s+(?P<c1>[\d\.,]+)\s+(?P<p1>[\d\.,]+)\s+(?P<c2>[\d\.,]+)\s+(?P<p2>[\d\.,]+)\s*$'
)

def parse_line(line):
    m = LINE_RE.match(line)
    if not m:
        return None
    sku = m.group('sku').strip()
    desc = m.group('desc').strip()
    stock = clean_number(m.group('stock'))
    # tomamos la última columna como precio unitario
    price = clean_number(m.group('p2'))
    return sku, desc, stock, price

def extract_from_text(pdf_path):
    rows = []
    rejected = []
    with pdfplumber.open(pdf_path) as pdf:
        for p, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            for ln in text.splitlines():
                ln = ln.strip()
                if not ln:
                    continue
                # saltar encabezados típicos
                if re.search(r'Codigo\s+Descripcion|LISTADO DE', ln, re.IGNORECASE):
                    continue
                parsed = parse_line(ln)
                if parsed:
                    rows.append(parsed)
                else:
                    rejected.append((p, ln))
    return rows, rejected

def save_csv(rows, out_csv):
    with open(out_csv, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['SKU','Nombre','Stock','Precio'])
        for r in rows:
            writer.writerow(r)

def save_rejected(rejected, fname):
    with open(fname, 'w', encoding='utf-8') as f:
        for p, ln in rejected:
            f.write(f"PAGE {p}: {ln}\n")

def main(pdf_file):
    print("[INFO] Extrayendo y parseando texto...")
    rows, rejected = extract_from_text(pdf_file)
    print(f"[INFO] Filas parseadas: {len(rows)}  Rechazadas: {len(rejected)}")
    if rows:
        save_csv(rows, OUT_CSV)
        print(f"[OK] CSV guardado: {OUT_CSV}")
    if rejected:
        save_rejected(rejected, REJECT_FILE)
        print(f"[WARN] Líneas rechazadas guardadas en: {REJECT_FILE}")
        if DEBUG_PRINT:
            print("\n--- Primeras 10 líneas rechazadas ---")
            for p, ln in rejected[:10]:
                print(f"PAGE {p}: {ln}")
            print("--- fin ---")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python pdf_to_csv_textparse.py listado.pdf")
        sys.exit(1)
    main(sys.argv[1])
