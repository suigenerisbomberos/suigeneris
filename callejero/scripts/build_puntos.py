import json, sys, math
from collections import defaultdict
from shapely.geometry import LineString, Point
from shapely.strtree import STRtree
from shapely.ops import unary_union

DIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

LAT0=36.72; KX=111320.0*math.cos(math.radians(LAT0)); KY=110574.0
def tx(lon,lat): return (lon*KX, lat*KY)

# Líneas de calle (metros) + nombre para asignar "está en calle X"
tg={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    tg[p['ID_TRAMOVIAL']]=LineString([tx(c[0],c[1]) for c in g['coordinates']])
via_tramos=defaultdict(list)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']
    if p['ID_TRAMOVIAL'] in tg: via_tramos[p['CODVIAL5']].append(p['ID_TRAMOVIAL'])
vias={r['cod']:r for r in load(f"{OUT}/cal_vias.json")}
cods=[]; geoms=[]
for cod,tids in via_tramos.items():
    cods.append(cod); geoms.append(unary_union([tg[t] for t in tids]))
tree=STRtree(geoms)
def calle_de(lon,lat):
    pt=Point(tx(lon,lat))
    i=tree.nearest(pt)
    idx = i if isinstance(i,int) else int(i)
    cod=cods[idx]
    return vias.get(cod,{}).get('display','')

FUENTES=[
    ('poi_monumentos','NOMBRE','monumentos'),
    ('poi_mercados','TOOLTIP','mercados'),
    ('poi_colegios','NOMBRE','colegios'),
    ('poi_consulados','TOOLTIP','consulados'),
    ('poi_bibliotecas','NOMBRE','bibliotecas'),
]
puntos=[]
for archivo,campo,cat in FUENTES:
    try: d=load(f"{DIR}/{archivo}.geojson")
    except Exception as e: print('no',archivo,e); continue
    n=0
    for f in d['features']:
        g=f.get('geometry'); pr=f.get('properties',{})
        if not g or g['type']!='Point': continue
        lon,lat=g['coordinates'][0], g['coordinates'][1]
        nombre=(pr.get(campo) or '').strip()
        if not nombre: continue
        puntos.append({'n':nombre,'cat':cat,'lat':round(lat,6),'lng':round(lon,6),'calle':calle_de(lon,lat)})
        n+=1
    print(f"{cat}: {n}")

json.dump(puntos, open(f"{OUT}/cal_puntos.json",'w',encoding='utf-8'), ensure_ascii=False)
print("TOTAL puntos:", len(puntos))
