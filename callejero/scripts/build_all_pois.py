import os, re, json, time, urllib.parse, urllib.request, fitz
DATA="/Users/josecarlos/suigeneris/callejero/data"
FOLDER="/Users/josecarlos/Desktop/ACADEMIA/CALLEJERO/CALLEJERO PARA PLATAFORMA/PUNTOS DE INTERES PLATAFORMA 2026"
CACHE="/private/tmp/claude-501/-Users-josecarlos/94dd0558-d88d-45a3-b9de-098330d09584/scratchpad/geocache.json"

cache=json.load(open(CACHE,encoding='utf-8')) if os.path.exists(CACHE) else {}
def _enmalaga(c): return bool(c) and 36.58<c[0]<36.85 and -4.70<c[1]<-4.25
def geocode(q):
    if not q or not q.strip(): return None
    if q in cache: res=cache[q]
    else:
        url="https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&q="+urllib.parse.quote(q)
        try:
            req=urllib.request.Request(url, headers={'User-Agent':'SuiGenerisCallejero/1.0 (educativo)'})
            d=json.load(urllib.request.urlopen(req, timeout=25))
            res=[round(float(d[0]['lat']),6), round(float(d[0]['lon']),6)] if d else None
        except Exception: res=None
        cache[q]=res; json.dump(cache, open(CACHE,'w',encoding='utf-8')); time.sleep(1.1)
    return res if _enmalaga(res) else None   # candado: fuera de Málaga = no vale

HEAD={'nombres','nombre','direccion','dirección','situación','situacion','ubicación','ubicacion','ficha nombre','sui generis','nombre '}
def es_vaga(d):
    dl=d.lower().strip()
    return any(dl.startswith(x) for x in ['esta','está','en el','en la','detras','detrás','situad','junto','dentro','parte','ladera','frente','margen','ambos','sobre','cruza','entre'])
def limpia(d):
    d=re.sub(r'^\s*c/\.?\s*','Calle ',d,flags=re.I)
    d=re.sub(r'^\s*cl\.?\s+','Calle ',d,flags=re.I)
    d=re.sub(r'^\s*(avda|av)\.?\s+','Avenida ',d,flags=re.I)
    d=re.sub(r'^\s*pl\.?\s+','Plaza ',d,flags=re.I)
    d=re.sub(r'\bN[ºo°]\s*','',d)
    d=re.split(r';|código postal|c\.p\.', d, flags=re.I)[0]
    d=re.sub(r'\(.*?\)',' ',d); d=re.sub(r'\bs/n\b',' ',d,flags=re.I)
    d=re.sub(r'/\s*\d+.*$','',d)  # quita "/5º/B" etc.
    return re.sub(r'\s+',' ',d).strip(' .,')
def calle_sola(d): return re.split(r'[,0-9]', limpia(d))[0].strip(' .')

def entradas(path):
    doc=fitz.open(path); lines=[]
    for pg in doc:
        for l in pg.get_text().split('\n'):
            l=l.strip()
            if l and l.lower() not in HEAD: lines.append(l)
    # Detecta el formato del PDF
    barenums=sum(1 for l in lines if re.match(r'^\d+\s*$', l))
    numtext =sum(1 for l in lines if re.match(r'^\d+\s+\S', l))
    out=[]
    if barenums>=3 and barenums>=numtext*0.5:
        # MODO número-solo: cada ficha empieza por un número en su propia línea.
        # El bloque llega hasta el SIGUIENTE número-solo (así "5 Estrellas", que
        # empieza por dígito, NO corta la ficha; es contenido, no ficha nueva).
        i=0
        while i<len(lines):
            if not re.match(r'^\d+\s*$', lines[i]): i+=1; continue
            j=i+1; blk=[]
            while j<len(lines) and not re.match(r'^\d+\s*$', lines[j]): blk.append(lines[j].strip()); j+=1
            popped=False
            while blk and blk[-1].lower() in ('málaga','malaga'): blk.pop(); popped=True
            if popped and len(blk)>=3:        # tipo / nombre / dirección
                nombre=(blk[0]+' '+blk[1]).strip(); direccion=blk[2]
            elif len(blk)>=2:                 # nombre / dirección (+extra ignorado)
                nombre=blk[0]; direccion=blk[1]
            elif len(blk)==1:
                nombre=blk[0]; direccion=''
            else: nombre=''; direccion=''
            if nombre: out.append((re.sub(r'\s*\(\d+\)\s*$','',nombre.strip(' .')), direccion))
            i=j
    elif numtext>=3:
        # MODO formato A: "N Nombre" y la dirección en la línea siguiente
        i=0
        while i<len(lines):
            m=re.match(r'^(\d+)\s+(.+)$', lines[i])
            if m and len(m.group(2))>2:
                nombre=re.sub(r'\s*\(\d+\)\s*$','',m.group(2)).strip(' .'); direccion=''
                if i+1<len(lines) and not re.match(r'^\d+(\s|$)', lines[i+1]): direccion=lines[i+1].strip(); i+=1
                out.append((nombre,direccion))
            i+=1
    else:
        # MODO C: sin números, pares nombre/dirección alternos
        def addr_like(l):
            ll=l.lower().strip()
            if re.match(r'^(c/|cl\b|av\b|avda|avenida|calle|plaza|pl\b|paseo|camino|ctra|carretera|urb)', ll): return True
            return ('nº' in ll) or bool(re.search(r',\s*\d', l)) or bool(re.search(r'\b29\d{3}\b', l))
        prev=None
        for l in lines:
            if addr_like(l):
                if prev: out.append((prev.strip(' .'), l.strip())); prev=None
            else: prev=l
    return out

def geo_entry(nom, d):
    if d and not es_vaga(d):
        c=geocode(limpia(d)+', Málaga, España')
        if c: return c
    c=geocode(f"{nom}, Málaga, España")
    if c: return c
    if d: return geocode(calle_sola(d)+', Málaga, España')
    return None

FILES=[
 ("01 Bibliotecas Málaga 2026.pdf","bibliotecas","Bibliotecas","#e11d48"),
 ("02 Centros Educativos (Colegios, Institutos, etc 2026.pdf","colegios","Colegios e institutos","#facc15"),
 ("03 Cementerios 2026.pdf","cementerios","Cementerios","#6b7280"),
 ("04 Consulados en Málaga 2026.pdf","consulados","Consulados","#1e3a8a"),
 ("05 Delegaciones Oficiales Málaga 2026.pdf","delegaciones","Delegaciones","#6366f1"),
 ("06 Facultades, Escuelas Universitarias, Colegios Oficiales y otros 2026.pdf","facultades","Facultades y universidades","#0891b2"),
 ("07 Hoteles de Málaga 2026.pdf","hoteles","Hoteles","#a855f7"),
 ("08 Hospitales y Centros de Salud 2026.pdf","salud","Hospitales y salud","#22c55e"),
 ("09 Instalaciones Deportivas 2.pdf","deportivas","Instalaciones deportivas","#84cc16"),
 ("10 Mercados Municipales 2.pdf","mercados","Mercados","#14b8a6"),
 ("11 Comisarias de policía Nacional y Local - Comandancia Guardia Civil 2026.pdf","comisarias","Comisarías y G. Civil","#334155"),
 ("13 Jardines y Parques 2026.pdf","jardines","Jardines y parques","#16a34a"),
 ("14 Juntas Municipales de Distritos 2.pdf","juntas","Juntas de distrito","#7c3aed"),
 ("16 Parroquias de Málaga 2026.pdf","parroquias","Parroquias","#b45309"),
 ("17 Playas de Málaga 2026.pdf","playas","Playas","#38bdf8"),
 ("19 Polígonos Industriales y Comerciales de Málaga 2026.pdf","poligonos","Polígonos","#78716c"),
 ("20 Puentes sobre el Guadalmedina 2026.pdf","puentes","Puentes Guadalmedina","#d97706"),
 ("21 Servicios Públicos sedes Málaga 2026.pdf","servicios_publicos","Servicios públicos","#0ea5e9"),
 ("22 Teatros, Salas de Espectáculos y Centros Culturales 2026.pdf","teatros","Teatros y salas","#d946ef"),
 ("23 Museos de Málaga 2026.pdf","museos","Museos","#8b5e3c"),
 ("24 Palacios y castillos Málaga capital 2.pdf","palacios","Palacios y castillos","#9f1239"),
 ("Fuentes Ornamentales 2026.pdf","fuentes","Fuentes","#06b6d4"),
]
EXTRA={'facultades':[("UAX Mare Nostrum - Campus de Málaga","Camino de la Térmica 90"),
                     ("Universidad Europea de Andalucía","Calle Eolo 10")]}

pts=[p for p in json.load(open(f"{DATA}/cal_puntos.json",encoding='utf-8')) if p.get('src') in ('osm',)]
cats={'bomberos':{'l':'Parques de bomberos','c':'#dc2626'}}
resumen=[]
for fn,slug,label,color in FILES:
    cats[slug]={'l':label,'c':color}
    path=os.path.join(FOLDER,fn)
    if not os.path.exists(path): resumen.append((label,'NO ENCONTRADO',0,0)); continue
    ent=entradas(path)+[(n,d) for n,d in EXTRA.get(slug,[])]
    ok=0; miss=[]
    for nom,d in ent:
        if not nom: continue
        c=geo_entry(nom,d)
        if not c: miss.append(nom); continue
        pts.append({'n':nom,'cat':slug,'lat':c[0],'lng':c[1],'calle':(limpia(d) if d else ''),'src':'pdf'})
        ok+=1
    resumen.append((label,fn,len(ent),ok))
    print(f"{label}: {ok}/{len(ent)}", flush=True)

json.dump(pts, open(f"{DATA}/cal_puntos.json",'w',encoding='utf-8'), ensure_ascii=False)
json.dump(cats, open(f"{DATA}/cal_categorias.json",'w',encoding='utf-8'), ensure_ascii=False)
print("LISTO. TOTAL puntos:", len(pts))
