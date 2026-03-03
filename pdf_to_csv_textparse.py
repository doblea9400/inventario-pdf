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

OUT_CSV = "listado_limpio.csv"

# Unidades comunes
UNITS = {'G', 'GR', 'ML', 'L', 'KG', 'UNID', 'UND', 'U', 'X', 'LT', 'LTS', 'W'}

# Marcas y palabras comunes de productos
PRODUCT_WORDS = {
    'MUNDO', 'MARINO', 'NOEL', 'POPPING', 'CANDY', 'TATTOO', 'ACEITE', 'DE', 'OLIVA',
    'JOHNSONS', 'ACHOCOLATADO', 'LONCH', 'AFEITADORA', 'APEX', 'VENUS', 'AGOGO',
    'BOLSA', 'AGUA', 'CRISTAL', 'CRYSTAL', 'GAS', 'NEVADA', 'SAN', 'FELIPE',
    'ALCOHOL', 'ALIVE', 'KILO', 'AMORI', 'TUBO', 'ANGELITOS', 'MINI', 'TIRA',
    'ANI', 'POP', 'CHUPETA', 'ANILLO', 'OSITO', 'LOKO', 'ANTENADOS', 'GRAMOS',
    'HOJILLAS', 'RISTRA', 'ARBOLITO', 'GRANDE', 'AREQUIPE', 'CAMPONESA', 'CHOCOLATE',
    'WEPA', 'AROMATEL', 'ATUN', 'DON', 'TUTO', 'TIGO', 'AXION', 'BABO', 'TUBULAR',
    'BALANCE', 'CLINICAL', 'POMO', 'SOBRE', 'DUO', 'BAMBINO', 'GELATINA', 'BARQUILLA',
    'BARRILETE', 'BASTON', 'CHUPIFIESTA', 'DELICIAS', 'BEANS', 'SODA', 'BEBIDA',
    'BEL', 'POTE', 'BELL', 'MONEDA', 'BELVITA', 'HONY', 'KRAKER', 'BESO', 'BEST',
    'WAFER', 'BIANCHI', 'BARRA', 'PEQUENO', 'PEQUEÑO', 'CHOCOLORES', 'CON', 'EXHIBIDOR',
    'BOMBON', 'SNACK', 'SURTIDO', 'BIG', 'BOM', 'BABY', 'COLA', 'LITROS', 'BLANCOX',
    'BLANQUEADOR', 'BONDI', 'BLISS', 'CALI', 'BLOCK', 'BOCADILLO', 'GUAYABA', 'PLATANO',
    'TAMARINDO', 'POTEX', 'VELENITAS', 'VELENO', 'BOCADILLOS', 'BOKA', 'LOKA', 'BOLA',
    'CHICLE', 'OJOS', 'ACIDOS', 'SANDIA', 'OHKA', 'BOLI', 'BULLS', 'FAMILIAR', 'PQNO',
    'BOLIKRUNCH', 'XXL', 'BOLON', 'BOLONCHO', 'BOMBONES', 'CUBITO', 'UNIDADES',
    'BOLSITA', 'BOMBILLO', 'ROJO', 'CORAZON', 'DECORAZON', 'LUIS', 'OSCAR', 'WYNCO',
    'DISPLAY', 'ROSA', 'BON', 'AMORY', 'AMISTAD', 'BOTA', 'NAVIDAD', 'BOTECITO', 'FUDGE',
    'BOTECITOS', 'BOTELLITA', 'BRIDGE', 'BRILLANTE', 'BRINKY', 'BUBBALOO', 'SPARKIES',
    'BUBBLEGUM', 'BUBBLEROLL', 'BUBBLES', 'PEANUT', 'TOGO', 'BUBY', 'BA', 'BUZZY',
    'CALEDONIA', 'CACAO', 'Y', 'LIMON', 'CAPRI', 'CAREMELLA', 'CARAMELO', 'DECAFE', 'GURME',
    'FLORESTAL', 'FRUNAS', 'FRUTICAS', 'MIST', 'ALOKADOS', 'DETAMARINDO', 'DISCA', 'EN',
    'GEL', 'JENGIBRE', 'COCO', 'CARBONERO', 'CAREFREE', 'PROTECTOR', 'CARRE', 'CARTOON',
    'LOLLIPOP', 'CELEMA', 'CEPILLO', 'DENTAL', 'COLGATE', 'GALACTIC', 'KIDS', 'CEREAL',
    'MAIZORITOS', 'LONCHERA', 'CERO', 'GRADOS', 'CHAO', 'FRUSH', 'LINEA', 'XTREME', 'EXTREME',
    'CHARMY', 'CHEESETRIS', 'CHESITOS', 'CHESSY', 'BULL', 'CHICCO', 'TOALLAS', 'CHICHARRON',
    'MUNCHY', 'CRIOLLO', 'PARRILLERO', 'PIGSY', 'SALSERITO', 'CHICLEFREE', 'GELLS', 'EXTRA',
    'FRESH', 'GUM', 'PZAS', 'TIKTOK', 'CHICLETS', 'CHIMO', 'APURENITO', 'EL', 'TIGRITO',
    'CHIPS', 'AHOY', 'NACIONAL', 'CHISKESITO', 'CHISKESITOS', 'CHISKRONCH', 'CHOCO',
    'BEST', 'BREAK', 'BALL', 'CHOCOGOLL', 'BONUCCI', 'CORONA', 'RICH', 'SAVOY', 'MEDIANO',
    'TUBE', 'GALLETA', 'JUGUETE', 'CHOCOLISTO', 'CHOCORAMO', 'BROWNIE', 'TAJADA',
    'BOMBON', 'BUM', 'GIRASOL', 'MICKY', 'PINKI', 'PALETA', 'PEQ', 'CHUPIGOOL', 'HEARTS',
    'CIFRUT', 'CINTA', 'CLISS', 'CLUB', 'SOCIAL', 'COCA', 'CRUNCH', 'RANCH', 'COCOSETTE',
    'COFFEE', 'DELIGHT', 'TRIPLE', 'ACCION', 'COLORETI', 'COMBO', 'COMPOTA', 'OSOLE',
    'CONITOS', 'RELLENOS', 'CONIX', 'CONSERVA', 'DELECHE', 'COTILLON', 'COTUFAS',
    'ACARAMELADAS', 'SABOR', 'CRACKIT', 'CRUJIENTE', 'TRUFA', 'VAINILLA', 'CRAKENAS',
    'SALTIN', 'TACOS', 'CREAM', 'CREMA', 'CULINARIA', 'DEARROZ', 'MARY', 'CREMADITAS',
    'CREMOSO', 'VERA', 'CRI', 'KROK', 'CRISKA', 'DORIKA', 'PEPIK', 'ESTRELLITA', 'CRISPIG',
    'DANDY', 'DANI', 'DELECHITAS', 'DELEITINAS', 'DETODITO', 'DIABLITO', 'LATA', 'DIAMOND',
    'RING', 'AROMAX', 'DOBLEGUM', 'DORITO', 'DINAMITA', 'DORITOS', 'DORT', 'KAT', 'DOVE',
    'ROLLON', 'DUCREM', 'EGGS', 'CHOCO', 'YOLIS', 'TIO', 'LECHE', 'ESPECIALIDADES', 'NESTLE',
    'ESTRELA', 'EXHIBIDOR', 'SUPER', 'TRULULU', 'FABULOSO', 'FELIZ', 'NAVIDAD', 'COLOMBINA',
    'FESTIVAL', 'FINGER', 'RN', 'FLAQUITO', 'FLIPS', 'CAJA', 'IMPORTADO', 'FORTNITE',
    'HUEVO', 'SORPRESA', 'FOSFOROS', 'FREEGELLS', 'BARRA', 'FRUTAS', 'RELLENAS', 'FRUTI',
    'FRUTINO', 'FUNDIPPERZ', 'GALA', 'CLASSIC', 'ICE', 'TRIPLEMAX', 'ULTRAMINT', 'GALAK',
    'TUBITO', 'BRO', 'CREME', 'RELLENA', 'INDEPENDENCIA', 'GEO', 'SWAFLES', 'GATORADE',
    'GEL', 'EGO', 'FIJADOR', 'ROLDA', 'GELA', 'PLAY', 'PAYASO', 'PORCIONES', 'GILLETTE',
    'ULTRAGRIP', 'GOLOZETAS', 'GOLPE', 'TODO', 'GOMITAS', 'BON', 'BUM', 'BRUSLI', 'GULI',
    'WYNCO', 'GOMUTCHO', 'GUMMY', 'HALLS', 'HAPPY', 'HOJILLA', 'DORCO', 'HOT', 'DOG',
    'MARSHMALLOWS', 'HUBBA', 'BUBBA', 'HUEVITO', 'ISELITAS', 'YUCA', 'JABON', 'ANITA',
    'HARMONY', 'LAK', 'FRAGANCE', 'LEMON', 'LIQUIDO', 'MEDICARE', 'ORO', 'PROTEX', 'REXONA',
    'ROMBO', 'JACK', 'SCHICHARRON', 'JAMON', 'ENDIABLADO', 'JET', 'BURBUJAS', 'SABORES',
    'SURTIDOS', 'JUCOSA', 'JUGO', 'DEL', 'VALLE', 'GUACAFRUIT', 'NATULAC', 'KELLOGGS',
    'KESITOS', 'KRON', 'MANI', 'LADY', 'SPEED', 'STICK', 'PRACTITAPA', 'PRACTITUBO',
    'LAILA', 'CALDO', 'DEPOLLO', 'LAPIZ', 'LABIAL', 'LAVALOZA', 'LAVAPLATOS', 'SUPREMO',
    'CARABOBO', 'CONDENSADA', 'CREMOR', 'CONDYLAC', 'DOBOM', 'LECHENATULAC', 'LENGUA',
    'PAINT', 'LIFESAVERS', 'LIMPIAPISOS', 'VINAGRE', 'LISTERINE', 'LOKINO', 'MONSTER',
    'FOOT', 'LOLLIPOP', 'LUM', 'COMPACT', 'AFEITA', 'M&M', 'CANDIES', 'MADAGASCAR', 'MAITA',
    'MAIZ', 'COTUFA', 'MAIZINA', 'AMERICANA', 'MAKSIM', 'MALLOWS', 'POP', 'BOKAS', 'CHIQUI',
    'JACKS', 'KING', 'SIN', 'SAL', 'MIXTO', 'MARIA', 'ITALIA', 'PAMPA', 'PUIG', 'TENTAZIONE',
    'TRIGO', 'ORO', 'MARIELITAS', 'CHIPS', 'MARILU', 'MARSHMALLOW', 'TWIST', 'MASCARILLA',
    'PANTENE', 'KARSEELL', 'MASMELO', 'EMOCIONES', 'MAX', 'MAXICOCO', 'SANDWICH', 'MECHAS',
    'LOCAS', 'MEGA', 'AROS', 'BOL', 'BIT', 'MENTA', 'HELADA', 'MENTHOPLUS', 'MENTITAS',
    'AMBROSOLI', 'FLORETE', 'MENTOS', 'MILKA', 'MILKYWAY', 'MILLOWS', 'MIMADITO', 'BUM',
    'CARRO', 'CASITA', 'CHICLETATTOO', 'CHIPSAHOY', 'MINICOCOSETTE', 'MINIFLAQUITO',
    'FUDGE', 'JELLY', 'AZUL', 'ROSADO', 'FIGURAS', 'FRUITS', 'NIÑO', 'REDONDO', 'TREN',
    'KEKS', 'NANOSOKA', 'OREO', 'PIRUETAS', 'WAFER', 'WORLD', 'MINIS', 'DANI', 'VAINILLA',
    'MIRRINGO', 'ADULTO', 'CACHORRO', 'MOLINO', 'MUU', 'MANTEQUILLA', 'NATUCHIPS', 'AJO',
    'PEREJIL', 'NATYS', 'NAVIDENAS', 'BANDEJA', 'NESTEA', 'NEVADAGAS', 'MANZANA', 'PARCH',
    'NUCITA', 'CRUNCHY', 'DOBLESABOR', 'VASO', 'NUTELLA', 'NUTELLO', 'NUTRIBELA', 'NUTTELINI',
    'OBLEAS', 'OFERTA', 'PRINGLES', 'OHKAROLLZ', 'ROLLZ', 'CARITAS', 'ATLANTIC', 'OKA',
    'POLVO', 'REVOLCON', 'FUSION', 'NANOS', 'ONCE', 'MOSTRADOR', 'ORIGINAL', 'OSTIS',
    'OVOMALTINA', 'PALETA', 'CHAVO', 'PALITOS', 'XTREME', 'XXL', 'PALMERITAS', 'PALMOLIVE',
    'PAÑAL', 'MIMLOT', 'PANCHI', 'PANDA', 'BUNNY', 'PANELADA', 'PANETTONE', 'PANQUE',
    'PAPAS', 'CRUNCH', 'DELI', 'CAMPO', 'PUNCH', 'ON', 'RUPLI', 'PAPEL', 'ALISOF', 'HOJAS',
    'ROSAL', 'AMARILLO', 'NARANJA', 'ROJO', 'VERDE', 'VINOTINTO', 'PEPITAS', 'PEPITO',
    'BARBANESA', 'JAIMITO', 'ORIGINAL', 'RIKOS', 'GRANDES', 'PHONEFLASH', 'PIAZZA',
    'PINGUINO', 'PINGUINOS', 'PINK', 'HEARTS', 'CHUPETAS', 'PINTA', 'LENGUA', 'PIRUETAS',
    'BANDEJA', 'PIRULETA', 'ASTRONAUTA', 'AUTO', 'CHUPETERA', 'ESTRELLA', 'MONSTRUO', 'NEON',
    'PIRULIN', 'DISPENSADOR', 'ESTUCHE', 'PITILLO', 'PLATANITOS', 'PLAY', 'ANILLOS',
    'TIBURONES', 'POPBULLS', 'COTUFAS', 'POPPIN', 'ICECREAM', 'POTETURRON', 'POWERADE',
    'PRESTOBARBA', 'PROTECTOR', 'DIARIO', 'PULP', 'SIXPACK', 'SIX', 'PACK', 'RAQUETY',
    'REDBULL', 'BULL', 'REFRESCO', 'REPITOS', 'RICATO', 'RICOBAMBI', 'RICOLATE', 'PALITOS',
    'RIMUNCA', 'DETIRA', 'RING', 'PON', 'RINGO', 'RISTRA', 'CEPILLO', 'RIZADA', 'RIZOS',
    'COLORIDOS', 'ROLLY', 'MINTY', 'ROSSO', 'BIANCO', 'ROYAL', 'LEUNTABLE', 'RUFFLES',
    'SALRICA', 'TACO', 'TACOS', 'SALRICAS', 'CLUB', 'SALSA', 'FRITZ', 'ROROS', 'SALSERITOS',
    'SALTIN', 'SAMBA', 'SAMY', 'SAPITO', 'SAVITAL', 'ACONDICIONADOR', 'SAVOY', 'SCHINCK',
    'SCOOTER', 'SERVILLETAS', 'TIPO', 'Z', 'SHAMPOO', 'OVERSKIN', 'SIMA', 'SKATE', 'SKITTLES',
    'SNACHOS', 'SNICKERS', 'SNOW', 'MINT', 'SOPA', 'MAGGI', 'SPEED', 'MAX', 'SPLOT', 'LINEA',
    'ACIDO', 'SR', 'MASMELITO', 'SUAVISANTE', 'SUAVITEL', 'BOLY', 'POPY', 'SUPERCOCO',
    'TURRON', 'SUSY', 'TAKIS', 'TAM', 'TE', 'CRYSTAL', 'TRITURADA', 'TERRY', 'WEPA', 'TETEROS',
    'TIP', 'TOP', 'SANITARIA', 'ALIVE', 'DIURNA', 'NOCTURNA', 'AMY', 'MILENA', 'WANITA',
    'TOALLITAS', 'UPPY', 'TOCINETA', 'VICKY', 'TOCINETIKAS', 'TORONTO', 'NEVADO', 'TORTILLAS',
    'TOSTON', 'TOY', 'TRACTOR', 'LASER', 'TREN', 'TRIDENT', 'TRIFOGON', 'TRINKETS', 'TROMPO',
    'TRONKOLATE', 'TRUE', 'BITES', 'TRUENO', 'TRUFFLES', 'PIRAMIDAL', 'TUBIS', 'TURRON',
    'BLANCO', 'CRISPY', 'ESPECIAL', 'UNID', 'UNIDAD', 'VARIOS', 'VENELUZ', 'WAFER',
    'COLOMBINA', 'CRACK', 'IT', 'RIKAS', 'XTREME', 'ROSA', 'VERDE', 'YESQUERO', 'ZIG', 'ZAG'
}

def clean_number_token(s):
    s = s.strip()
    if re.search(r'\d+\.\d+,\d+', s):
        s = s.replace('.', '').replace(',', '.')
    else:
        s = s.replace(',', '.')
    s = re.sub(r'[^0-9\.\-]', '', s)
    return s

def capitalize_title(text):
    """
    Convierte el texto a formato Title Case (Capitalize)
    Ejemplo: "agua san felipe" -> "Agua San Felipe"
    """
    if not text:
        return text
    
    words = text.split()
    capitalized_words = []
    
    for word in words:
        # Si es una unidad, mantener en mayúsculas
        if word.upper() in UNITS:
            capitalized_words.append(word.upper())
        # Si es "X" sola, mantener en mayúsculas
        elif word.upper() == 'X' and len(word) == 1:
            capitalized_words.append('X')
        # Si es una palabra común del diccionario, capitalizar correctamente
        elif word.upper() in PRODUCT_WORDS:
            capitalized_words.append(word.capitalize())
        # Para cualquier otra palabra, aplicar capitalize
        else:
            capitalized_words.append(word.capitalize())
    
    return ' '.join(capitalized_words)

def separate_words_intelligently(text):
    """Divide texto pegado en palabras usando el diccionario"""
    if not text:
        return text
    
    # Paso 1: Separar números de letras
    text = re.sub(r'(\d)([A-Za-z])', r'\1 \2', text)
    text = re.sub(r'([A-Za-z])(\d)', r'\1 \2', text)
    
    # Paso 2: Separar unidades
    for unit in UNITS:
        text = re.sub(rf'(\d)\s*({unit})\b', r'\1 \2', text, flags=re.IGNORECASE)
    text = re.sub(r'X\s*(\d+)', r'X \1', text, flags=re.IGNORECASE)
    
    # Paso 3: Dividir palabras largas usando el diccionario
    words = text.split()
    final_words = []
    
    for word in words:
        # Si es solo números o muy corta, dejarla
        if word.isdigit() or len(word) <= 3:
            final_words.append(word)
            continue
        
        # Si contiene números, separar
        if re.search(r'\d', word):
            final_words.append(word)
            continue
        
        # Intentar dividir palabra larga
        if len(word) > 6:
            found = False
            # Intentar dividir en 2 partes
            for i in range(3, len(word) - 2):
                part1 = word[:i].upper()
                part2 = word[i:].upper()
                if part1 in PRODUCT_WORDS and part2 in PRODUCT_WORDS:
                    final_words.append(word[:i])
                    final_words.append(word[i:])
                    found = True
                    break
                # También verificar si part1 es marca conocida
                if part1 in PRODUCT_WORDS and len(part2) > 2:
                    final_words.append(word[:i])
                    # Procesar recursivamente el resto
                    remaining = separate_words_intelligently(word[i:])
                    final_words.extend(remaining.split())
                    found = True
                    break
            
            if not found:
                final_words.append(word)
        else:
            final_words.append(word)
    
    return ' '.join(final_words)

def repair_name(name):
    """Función principal de reparación"""
    if not name:
        return name
    
    # Limpiar caracteres raros
    name = name.replace('"', '').replace("'", "").strip()
    name = re.sub(r'^[,\.\s]+', '', name)
    name = re.sub(r'\s+', ' ', name)
    
    # Separar palabras inteligentemente
    name = separate_words_intelligently(name)
    
    # Aplicar capitalize a todo el texto
    name = capitalize_title(name)
    
    # Limpieza final
    name = ' '.join(name.split())
    
    return name.strip()

def extract_data(pdf_path):
    rows = []
    price_pattern = re.compile(r'(\d+[\d\.,\s]+)$')

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: 
                continue
            
            lines = text.splitlines()
            for line in lines:
                line = line.strip().replace('"', '')
                
                # Saltar líneas de encabezado
                if 'COMERCIAL' in line or 'LISTADO' in line or 'FECHA' in line:
                    continue
                
                # Buscar líneas que empiecen con SKU (código de barras largo)
                if re.match(r'^\d{7,}', line):
                    parts = line.split(maxsplit=1)
                    if len(parts) < 2: 
                        continue
                    
                    sku = parts[0]
                    resto = parts[1]
                    
                    # Buscar precios al final
                    match_precios = price_pattern.search(resto)
                    if match_precios:
                        bloque_precios = match_precios.group(1).strip()
                        nombre_sucio = resto.replace(bloque_precios, "").strip()
                        
                        # Reparar nombre
                        nombre = repair_name(nombre_sucio)
                        
                        # Procesar números
                        nums = bloque_precios.split()
                        if len(nums) >= 2:
                            stock = clean_number_token(nums[0])
                            precio = nums[-1].strip()
                            precio = precio.replace('.', '').replace(',', '.') if re.search(r'\d+\.\d+,\d+', precio) else precio.replace(',', '.')
                            
                            # Solo agregar si el nombre tiene sentido
                            if len(nombre) > 5:
                                rows.append([sku, nombre, stock, precio])

    return rows

def main(pdf_file):
    print(f"[INFO] Procesando: {pdf_file}")
    
    data = extract_data(pdf_file)
    
    if data:
        with open(OUT_CSV, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)
            writer.writerow(['SKU', 'Nombre', 'Stock', 'Precio'])
            writer.writerows(data)
        print(f"\n✅ ¡ÉXITO! {len(data)} productos extraídos.")
        
        print("\n[REVISIÓN] Primeros productos:")
        for i, res in enumerate(data[:15], 1):
            print(f"\n{i}. SKU: {res[0]}")
            print(f"   NOMBRE: {res[1]}")
            print(f"   STOCK: {res[2]} | PRECIO: {res[3]}")
    else:
        print("❌ No se encontró el patrón de datos.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main("listado.pdf")
