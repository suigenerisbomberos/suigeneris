import json, sys, math
from collections import defaultdict
from shapely.geometry import shape, LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

DIR=sys.argv[1]; MAPA=sys.argv[2]; OUTD=sys.argv[3]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

LAT0=36.72; KX=111320.0*math.cos(math.radians(LAT0)); KY=110574.0
def tx(p): return (p[0]*KX, p[1]*KY)
def geom_m(gj):
    t=gj['type']; c=gj['coordinates']
    if t=='Polygon': return shape({'type':'Polygon','coordinates':[[tx(p) for p in r] for r in c]})
    if t=='MultiPolygon': return shape({'type':'MultiPolygon','coordinates':[[[tx(p) for p in r] for r in poly] for poly in c]})
    raise ValueError(t)

# Distritos: num, nombre, geom(metros), bbox(lon/lat)
dists=[]
for f in load(f"{DIR}/distrito.geojson")['features']:
    p=f['properties']; g=f['geometry']
    xs=[]; ys=[]
    def walk(c):
        if isinstance(c[0],(int,float)): xs.append(c[0]); ys.append(c[1])
        else:
            for x in c: walk(x)
    walk(g['coordinates'])
    dists.append({'num':p['NUMERO'],'nombre':(p['NOMBRE'] or '').strip(),
                  'geom':geom_m(g),
                  'sw':[min(ys),min(xs)],'ne':[max(ys),max(xs)]})
dgeoms=[d['geom'] for d in dists]
dtree=STRtree(dgeoms)

# Tramos activos (metros) + relación
tramo={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    tramo[p['ID_TRAMOVIAL']]=LineString([tx(c) for c in g['coordinates']])
via_tramos=defaultdict(list)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']
    if p['ID_TRAMOVIAL'] in tramo: via_tramos[p['CODVIAL5']].append(p['ID_TRAMOVIAL'])

# Distrito principal (más metros) por vía
via_dist={}
for cod,tids in via_tramos.items():
    linea=unary_union([tramo[t] for t in tids])
    best=None; bl=0
    for i in dtree.query(linea):
        L=linea.intersection(dgeoms[i]).length
        if L>bl: bl=L; best=dists[i]['num']
    if best is not None: via_dist[cod]=best

# Añadir 'd' a cada feature del mapa servido
mapa=load(MAPA)
n=0
for f in mapa['features']:
    d=via_dist.get(f['properties']['cod'])
    if d is not None: f['properties']['d']=d; n+=1
with open(MAPA,'w',encoding='utf-8') as fo:
    json.dump(mapa, fo, ensure_ascii=False, separators=(',',':'))

# Lista de distritos para el selector
out=[{'num':d['num'],'nombre':d['nombre'],'sw':d['sw'],'ne':d['ne']} for d in sorted(dists,key=lambda x:x['num'])]
with open(f"{OUTD}/cal_distritos.json",'w',encoding='utf-8') as fo:
    json.dump(out, fo, ensure_ascii=False)

print("Distritos:", len(dists))
print("Vías con distrito:", len(via_dist), "de", len(via_tramos))
print("Features del mapa con 'd':", n)
for d in out: print("  ", d['num'], d['nombre'])
