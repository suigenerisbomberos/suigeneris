import sys, os, zipfile, re, json, unicodedata, glob, time, urllib.parse, urllib.request
DATA=sys.argv[1]; PRES=sys.argv[2]; CACHE=sys.argv[3]

cache=json.load(open(CACHE,encoding='utf-8')) if os.path.exists(CACHE) else {}
def geocode(q):
    if q in cache: return cache[q]
    url="https://nominatim.openstreetmap.org/search?format=json&limit=1&countrycodes=es&q="+urllib.parse.quote(q)
    try:
        req=urllib.request.Request(url, headers={'User-Agent':'SuiGenerisCallejero/1.0 (educativo)'})
        d=json.load(urllib.request.urlopen(req, timeout=20))
        res=[round(float(d[0]['lat']),6), round(float(d[0]['lon']),6)] if d else None
    except Exception: res=None
    cache[q]=res; json.dump(cache, open(CACHE,'w',encoding='utf-8')); time.sleep(1.1)
    return res

def norm(s):
    s=unicodedata.normalize('NFD',(s or '')).encode('ascii','ignore').decode().lower()
    s=re.sub(r'[^a-z0-9 ]',' ',s)
    TIPOS={'calle','c','avenida','avda','av','avd','plaza','pza','plza','paseo','po','camino','cno','carretera','ctra','cra','glorieta','gta','pasaje','psje','alameda','bulevar','ronda','travesia','subida','cuesta','explanada','muelle','parque','jardin','jardines'}
    CONECT={'de','del','la','el','los','las','y','e'}
    return ' '.join(t for t in s.split() if t and t not in TIPOS and t not in CONECT)
def limpia_dir(d):
    s=re.sub(r'\(.*?\)',' ', d or ''); s=re.sub(r'\bs/n\b',' ',s,flags=re.I)
    return re.sub(r'\s+',' ',s).strip(' .,')
def solo_calle(d):
    return re.split(r'[,(0-9]', limpia_dir(d))[0].strip(' .')

vias={r['cod']:r for r in json.load(open(f"{DATA}/cal_vias.json",encoding='utf-8'))}
idx={}
for cod,r in vias.items():
    k=norm(r.get('display',''))
    if k and k not in idx: idx[k]=r.get('display','')

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
            if nom and nom not in out: out[nom]=parts[1].strip()
    return out

FUENTES=[('Teatros, salas, etc, TEST.pptx','teatros'),('Sedes de servicios públicos TEST.pptx','servicios_publicos'),
         ('Delegaciones TEST.pptx','delegaciones'),('Hostales pensiones otros establecimientos test.pptx','hoteles')]
pts=[p for p in json.load(open(f"{DATA}/cal_puntos.json",encoding='utf-8')) if p.get('src')!='jose']
resumen=[]
for fn,cat in FUENTES:
    path=os.path.join(PRES,fn)
    if not os.path.exists(path): resumen.append((cat,'NO ENCONTRADO',0,0)); continue
    it=items(path); ok=0; miss=[]
    for nom,dirtxt in it.items():
        d=limpia_dir(dirtxt)
        coord=geocode(d+', Málaga, España') or geocode(solo_calle(dirtxt)+', Málaga, España')
        if not coord: miss.append(nom); continue
        calle=idx.get(norm(solo_calle(dirtxt))) or solo_calle(dirtxt)
        pts.append({'n':nom,'cat':cat,'lat':coord[0],'lng':coord[1],'calle':calle,'src':'jose'})
        ok+=1
    resumen.append((cat,os.path.basename(path),len(it),ok,miss))

json.dump(pts, open(f"{DATA}/cal_puntos.json",'w',encoding='utf-8'), ensure_ascii=False)
print("TOTAL:", len(pts))
for r in resumen:
    cat,f,tot,ok,miss = (r+([],))[:5] if len(r)<5 else r
    print(f"{cat}: {ok}/{tot}" + (f"  sin geo: {'; '.join(miss[:8])}" if miss else ''))
