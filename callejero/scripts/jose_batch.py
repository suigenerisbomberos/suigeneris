import sys, os, zipfile, re, json, unicodedata, glob
DATA=sys.argv[1]; PRES=sys.argv[2]

def norm(s):
    s=unicodedata.normalize('NFD', (s or '')).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ', s)
    TIPOS={'calle','c','avenida','avda','av','avd','plaza','pza','plza','paseo','po','camino','cno',
           'carretera','ctra','cra','glorieta','gta','pasaje','psje','alameda','bulevar','ronda',
           'travesia','subida','cuesta','explanada','muelle','parque','jardin','jardines'}
    CONECT={'de','del','la','el','los','las','y','e'}
    toks=[t for t in s.split() if t and t not in TIPOS and t not in CONECT]
    return ' '.join(toks)
def calle_de_dir(d):
    s=re.split(r'\bs/n\b', d or '', flags=re.I)[0]
    s=re.split(r'[,(0-9]', s)[0]
    return s.strip(' .')

vias={r['cod']:r for r in json.load(open(f"{DATA}/cal_vias.json",encoding='utf-8'))}
mapa=json.load(open(f"{DATA}/cal_mapa.geojson",encoding='utf-8'))
coord={}
for f in mapa['features']:
    xs=[];ys=[]
    for ln in f['geometry']['coordinates']:
        for p in ln: xs.append(p[0]); ys.append(p[1])
    if xs: coord[f['properties']['cod']]=[round(sum(ys)/len(ys),6), round(sum(xs)/len(xs),6)]
idx={}
for cod,r in vias.items():
    k=norm(r.get('display',''))
    if k and k not in idx: idx[k]=cod

def items(path):
    out={}
    with zipfile.ZipFile(path) as z:
        sl=sorted([n for n in z.namelist() if re.match(r'ppt/slides/slide\d+\.xml$',n)], key=lambda n:int(re.search(r'(\d+)',n).group(1)))
        for n in sl:
            raw=z.read(n).decode('utf-8','ignore').replace('</a:p>','\n')
            t=re.sub(r'<[^>]+>',' ',raw); t=re.sub(r'[ \t]+',' ',t)
            parts=[l.strip() for l in t.split('\n') if l.strip() and 'style.visibility' not in l]
            if len(parts)<2: continue
            nom=parts[0].strip(' .')
            if nom and nom not in out: out[nom]={'dir':parts[1].strip()}
    return out

FUENTES=[
    ('Teatros, salas, etc, TEST.pptx','teatros'),
    ('Sedes de servicios públicos TEST.pptx','servicios_publicos'),
    ('Delegaciones TEST.pptx','delegaciones'),
    ('Hostales pensiones otros establecimientos test.pptx','hoteles'),
    ('CENTROS DE SALUD TEST.pptx','salud'),
]
# cargar puntos existentes y quitar los de josé (re-ejecutable)
pts=[p for p in json.load(open(f"{DATA}/cal_puntos.json",encoding='utf-8')) if p.get('src')!='jose']
resumen=[]
for fn,cat in FUENTES:
    path=os.path.join(PRES,fn)
    if not os.path.exists(path):
        g=glob.glob(os.path.join(PRES,'*'+fn.split()[0]+'*'))
        path=next((x for x in g if not os.path.basename(x).startswith('~$')), None)
    if not path or not os.path.exists(path): resumen.append((cat,'NO ENCONTRADO',0,0,[])); continue
    it=items(path); ok=0; miss=[]
    for nom,info in it.items():
        cod=idx.get(norm(calle_de_dir(info['dir'])))
        if cod and cod in coord:
            pts.append({'n':nom,'cat':cat,'lat':coord[cod][0],'lng':coord[cod][1],'calle':vias[cod]['display'],'src':'jose'})
            ok+=1
        else: miss.append(nom)
    resumen.append((cat,os.path.basename(path),len(it),ok,miss))

json.dump(pts, open(f"{DATA}/cal_puntos.json",'w',encoding='utf-8'), ensure_ascii=False)
print("TOTAL puntos ahora:", len(pts))
for cat,f,tot,ok,miss in resumen:
    print(f"\n### {cat}: {ok}/{tot} cuadrados  ({f})")
    if miss: print("   sin cuadrar:", '; '.join(miss[:12]) + (' …' if len(miss)>12 else ''))
