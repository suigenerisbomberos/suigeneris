import json, sys, math
from shapely.geometry import shape
from shapely.strtree import STRtree

DIR=sys.argv[1]; MAPA=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

LAT0=36.72; KX=111320.0*math.cos(math.radians(LAT0)); KY=110574.0
def tx(p): return (p[0]*KX, p[1]*KY)
def gm(gj):
    t=gj['type']; c=gj['coordinates']
    if t=='Polygon': return shape({'type':'Polygon','coordinates':[[tx(p) for p in r] for r in c]})
    if t=='MultiPolygon': return shape({'type':'MultiPolygon','coordinates':[[[tx(p) for p in r] for r in poly] for poly in c]})
    raise ValueError(t)

dists=[]
for f in load(f"{DIR}/distrito.geojson")['features']:
    dists.append((f['properties']['NUMERO'], gm(f['geometry'])))
dgeoms=[d[1] for d in dists]
dtree=STRtree(dgeoms)

# distrito de cada barrio (num -> distrito) por mayor solape
bar_dist={}
for f in load(f"{DIR}/barrio.geojson")['features']:
    g=f.get('geometry')
    if not g: continue
    bg=gm(g); best=None; ba=0
    for i in dtree.query(bg):
        try: a=bg.intersection(dgeoms[i]).area
        except Exception: a=0
        if a>ba: ba=a; best=dists[i][0]
    if best is not None: bar_dist[f['properties']['NUMBARRIO']]=best

mapa=load(MAPA); n=0
for f in mapa['features']:
    d=bar_dist.get(f['properties']['num'])
    if d is not None: f['properties']['d']=d; n+=1
with open(MAPA,'w',encoding='utf-8') as fo:
    json.dump(mapa, fo, ensure_ascii=False, separators=(',',':'))
print("Barrios con distrito:", n, "de", len(mapa['features']))
