import json, sys, re
from collections import defaultdict, Counter

DIR = sys.argv[1]
OUT = sys.argv[2]

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# 1) Tipos de vía: CODTIPVIAL -> "Calle", "Plaza", ...
tipos = {}
for f in load(f"{DIR}/tipovial.geojson")['features']:
    p = f['properties']
    tipos[p['CODTIPVIAL']] = p['DESTIPVIAL'].strip()

# 2) Vías activas (FECBAJA nula): CODVIAL5 -> info
vias = {}
for f in load(f"{DIR}/vial.geojson")['features']:
    p = f['properties']
    if p.get('FECBAJA'):
        continue
    vias[p['CODVIAL5']] = {
        'cod': p['CODVIAL5'],
        'nomvial': p.get('NOMVIAL') or '',
        'codtip': p.get('CODTIPVIAL'),
        'codclase': p.get('CODCLASEVIAL'),
    }

# 3) Tramos activos (FECBAJA nula)
tramos_activos = set()
for f in load(f"{DIR}/tramo.geojson")['features']:
    p = f['properties']
    if p.get('FECBAJA'):
        continue
    tramos_activos.add(p['ID_TRAMOVIAL'])

# 4) Relación tramo->vía. Contar tramos activos por vía.
tramos_por_via = defaultdict(int)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p = f['properties']
    idt, cod = p['ID_TRAMOVIAL'], p['CODVIAL5']
    if idt in tramos_activos and cod in vias:
        tramos_por_via[cod] += 1

# Vías CON TRAZADO = las que tienen al menos un tramo activo
con_trazado = {cod: v for cod, v in vias.items() if tramos_por_via.get(cod, 0) > 0}

# ── Normalización de nombres ────────────────────────────────
SUFIJOS = ['DE LAS', 'DE LOS', 'DE LA', 'DEL', 'DE', 'LAS', 'LOS', 'LA', 'EL', 'Y']
CONECTORES = {'de','del','la','el','los','las','y','e','a','con','sin','por','en'}

# Corrector de tildes (los datos oficiales vienen SIN tildes). Centrado en los
# nombres/apellidos/lugares que más se repiten en el callejero de Málaga. Es
# un mejor-esfuerzo: José repasa los casos raros desde el panel.
ACENTOS = {
 'jose':'josé','maria':'maría','garcia':'garcía','jimenez':'jiménez','gomez':'gómez',
 'perez':'pérez','fernandez':'fernández','rodriguez':'rodríguez','martinez':'martínez',
 'sanchez':'sánchez','lopez':'lópez','gonzalez':'gonzález','diaz':'díaz','ramon':'ramón',
 'joaquin':'joaquín','agustin':'agustín','dominguez':'domínguez','gutierrez':'gutiérrez',
 'cristobal':'cristóbal','felix':'félix','julian':'julián','nicolas':'nicolás',
 'sebastian':'sebastián','vazquez':'vázquez','alvarez':'álvarez','ramirez':'ramírez',
 'bartolome':'bartolomé','matias':'matías','nuñez':'núñez','carrion':'carrión',
 'hernandez':'hernández','valdes':'valdés','calderon':'calderón','guillen':'guillén',
 'alarcon':'alarcón','suarez':'suárez','martin':'martín','marin':'marín','andres':'andrés',
 'tomas':'tomás','angel':'ángel','angeles':'ángeles','cesar':'césar','leon':'león',
 'galvez':'gálvez','barcelo':'barceló','velazquez':'velázquez','benitez':'benítez',
 'ibañez':'ibáñez','tellez':'téllez','chacon':'chacón','mendez':'méndez','millan':'millán',
 'galan':'galán','beltran':'beltrán','duran':'durán','guzman':'guzmán','farfan':'farfán',
 'mejias':'mejías','raul':'raúl','victor':'víctor','ruben':'rubén','simon':'simón',
 'adrian':'adrián','hernan':'hernán','lucia':'lucía','sofia':'sofía','rocio':'rocío',
 'ines':'inés','cadiz':'cádiz','cordoba':'córdoba','jaen':'jaén','almeria':'almería',
 'america':'américa','aragon':'aragón','malaga':'málaga','andalucia':'andalucía',
 'cartama':'cártama','coin':'coín','almogia':'almogía','olias':'olías','cortes':'cortés',
 'jesus':'jesús','bailen':'bailén','alcazar':'alcázar','rio':'río','capitan':'capitán',
 'alferez':'alférez','marques':'marqués','corazon':'corazón','concepcion':'concepción',
 'purisima':'purísima','autovia':'autovía','callejon':'callejón','travesia':'travesía',
}

def _cap_como(orig, nuevo):
    # Copia el patrón de mayúsculas de la palabra original a la acentuada.
    if orig.isupper(): return nuevo.upper()
    if orig[:1].isupper(): return nuevo[:1].upper() + nuevo[1:]
    return nuevo

def aplicar_acentos(texto):
    # Reemplaza palabra a palabra, conservando espacios y guiones.
    partes = re.split(r'([\s\-]+)', texto)
    out = []
    for p in partes:
        low = p.lower()
        out.append(_cap_como(p, ACENTOS[low]) if low in ACENTOS else p)
    return ''.join(out)

def title_word(w):
    # Mantiene guiones: VALLE-INCLAN -> Valle-Inclan
    return '-'.join(part.capitalize() for part in w.split('-'))

def normaliza(nomvial):
    s = ' '.join((nomvial or '').split())  # colapsa espacios
    up = s.upper()
    art = ''
    for suf in SUFIJOS:
        if up == suf:
            break
        if up.endswith(' ' + suf):
            art = suf
            s = s[:len(s) - len(suf) - 1].rstrip()
            break
    # Title-case del núcleo
    palabras = [title_word(w) for w in s.split(' ') if w]
    # conectores internos en minúscula (no el primero)
    out = []
    for i, w in enumerate(palabras):
        out.append(w if i == 0 else (w.lower() if w.lower() in CONECTORES else w))
    nucleo = ' '.join(out)
    if art:
        arttxt = art.lower()
        nombre = f"{arttxt} {nucleo}" if nucleo else arttxt
    else:
        nombre = nucleo
    return nombre

registro = []
for cod, v in con_trazado.items():
    tipo = aplicar_acentos(tipos.get(v['codtip'], '¿?'))
    nombre = aplicar_acentos(normaliza(v['nomvial']))
    display = f"{tipo} {nombre}".strip()
    registro.append({
        'cod': cod,
        'tipo': tipo,
        'codtip': v['codtip'],
        'nombre': nombre,
        'display': display,
        'nomvial_orig': v['nomvial'],
        'nTramos': tramos_por_via[cod],
    })

registro.sort(key=lambda r: (r['nombre'].lower(), r['tipo']))

# Guardar JSON
with open(f"{OUT}/cal_vias.json", 'w', encoding='utf-8') as f:
    json.dump(registro, f, ensure_ascii=False)

# Guardar listado legible
with open(f"{OUT}/LISTADO_VIAS.txt", 'w', encoding='utf-8') as f:
    for r in registro:
        f.write(f"{r['display']}   ·  (orig: {r['nomvial_orig'].strip()})\n")

# Informe
print("Vías activas (con y sin trazado):", len(vias))
print("Vías CON TRAZADO:", len(con_trazado))
print("\nPor tipo (con trazado):")
c = Counter(tipos.get(v['codtip'], '¿?') for v in con_trazado.values())
for tipo, n in c.most_common():
    print(f"   {n:5d}  {tipo}")
print("\nEjemplos de normalización (20 al azar por orden):")
for r in registro[:20]:
    print(f"   {r['display']:45s}  <-  {r['nomvial_orig'].strip()}")
