import sys, os, zipfile, re, json, unicodedata
PPTX=sys.argv[1]; DATA=sys.argv[2]

def norm(s):
    s=unicodedata.normalize('NFD', (s or '')).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ', s)
    TIPOS={'calle','c','avenida','avda','av','avd','plaza','pza','plza','paseo','po','camino','cno',
           'carretera','ctra','cra','glorieta','gta','pasaje','psje','alameda','bulevar','ronda',
           'travesia','subida','cuesta','explanada','muelle','parque','jardin','jardines'}
    CONECT={'de','del','la','el','los','las','y','e'}
    toks=[t for t in s.split() if t and t not in TIPOS and t not in CONECT]
    return ' '.join(toks)

def calle_de_dir(dirtxt):
    s=dirtxt or ''
    s=re.split(r'\bs/n\b', s, flags=re.I)[0]
    s=re.split(r'[,(0-9]', s)[0]
    return s.strip(' .')

# Índice de vías: nombre normalizado -> (display, coordenada)
vias={r['cod']:r for r in json.load(open(f"{DATA}/cal_vias.json",encoding='utf-8'))}
mapa=json.load(open(f"{DATA}/cal_mapa.geojson",encoding='utf-8'))
coord={}
for f in mapa['features']:
    cod=f['properties']['cod']
    xs=[];ys=[]
    for ln in f['geometry']['coordinates']:
        for p in ln: xs.append(p[0]); ys.append(p[1])
    if xs: coord[cod]=[round(sum(ys)/len(ys),6), round(sum(xs)/len(xs),6)]  # lat,lng medio
idx={}
for cod,r in vias.items():
    k=norm(r.get('display',''))
    if k and k not in idx: idx[k]=cod

def pptx_items(path):
    items={}
    with zipfile.ZipFile(path) as z:
        sl=sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)], key=lambda n:int(re.search(r'(\d+)',n).group(1)))
        for n in sl:
            raw=z.read(n).decode('utf-8','ignore').replace('</a:p>','\n')
            t=re.sub(r'<[^>]+>',' ',raw); t=re.sub(r'[ \t]+',' ',t)
            parts=[l.strip() for l in t.split('\n') if l.strip() and 'style.visibility' not in l]
            if len(parts)<2: continue
            nombre=parts[0].strip(' .')
            direccion=parts[1].strip()
            if nombre and nombre not in items: items[nombre]={'dir':direccion}
    return items

items=pptx_items(PPTX)
matched=[]; miss=[]
for nombre,info in items.items():
    calle=calle_de_dir(info['dir'])
    k=norm(calle)
    cod=idx.get(k)
    if cod and cod in coord:
        matched.append((nombre, calle, vias[cod]['display'], coord[cod]))
    else:
        miss.append((nombre, info['dir'], calle))
print(f"ITEMS: {len(items)} | CUADRADOS: {len(matched)} | SIN CUADRAR: {len(miss)}")
print("\n--- CUADRADOS (nombre -> calle detectada / vía del mapa) ---")
for n,c,v,_ in matched: print(f"  • {n}  ->  {c}  [{v}]")
print("\n--- SIN CUADRAR (dirección original) ---")
for n,d,c in miss: print(f"  • {n}  ->  dir: {d!r}  (calle: {c!r})")
