import json, sys, math
from collections import defaultdict
from shapely.geometry import LineString, Point, MultiLineString
from shapely.ops import unary_union, linemerge
DIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

LAT0=36.72; KX=111320.0*math.cos(math.radians(LAT0)); KY=110574.0
def tx(p): return (p[0]*KX, p[1]*KY)

# Tramos activos: geometría (metros) + endpoints (lon/lat redondeados)
tg={}; tends={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    cs=g['coordinates']
    tg[p['ID_TRAMOVIAL']]=LineString([tx(c) for c in cs])
    tends[p['ID_TRAMOVIAL']]=(tuple(round(v,6) for v in cs[0]), tuple(round(v,6) for v in cs[-1]))

via_tramos=defaultdict(list); tramo_via={}
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']; idt,cod=p['ID_TRAMOVIAL'],p['CODVIAL5']
    if idt in tg: via_tramos[cod].append(idt); tramo_via[idt]=cod

punto_vias=defaultdict(set)
for idt,(a,b) in tends.items():
    cod=tramo_via.get(idt)
    if cod is None: continue
    punto_vias[a].add(cod); punto_vias[b].add(cod)

cruces=load(f"{OUT}/cal_cruces.json")  # {cod(str):[cods]}

orden={}
for cod,tids in via_tramos.items():
    key=str(cod)
    vecinos=cruces.get(key)
    if not vecinos or len(vecinos)<3: continue
    # línea de la vía (metros), para proyectar
    L=unary_union([tg[t] for t in tids])
    try: L=linemerge(L)
    except Exception: pass
    if isinstance(L, MultiLineString):
        L=max(L.geoms, key=lambda g:g.length)
    # nodos de esta vía (lon/lat) -> punto metros
    nodos=set()
    for t in tids:
        a,b=tends[t]; nodos.add(a); nodos.add(b)
    # para cada vecino, su nodo compartido con la vía -> distancia a lo largo
    dist={}
    for v in vecinos:
        mejor=None
        for nodo in nodos:
            if v in punto_vias.get(nodo,()):
                d=L.project(Point(tx(list(nodo))))
                if mejor is None or d<mejor: mejor=d
        if mejor is not None: dist[v]=mejor
    if len(dist)<3: continue
    orden[key]=[v for v,_ in sorted(dist.items(), key=lambda kv:kv[1])]

json.dump(orden, open(f"{OUT}/cal_orden.json",'w',encoding='utf-8'), ensure_ascii=False)
print("Vías con cruces ordenados (>=3):", len(orden))
