import json, sys
from collections import defaultdict
from shapely.geometry import LineString, MultiLineString, mapping
from shapely.ops import linemerge, unary_union

DIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

# Tramos activos en lon/lat
tramo={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    tramo[p['ID_TRAMOVIAL']]=g['coordinates']

via_tramos=defaultdict(list)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']
    if p['ID_TRAMOVIAL'] in tramo: via_tramos[p['CODVIAL5']].append(p['ID_TRAMOVIAL'])

vias={r['cod']:r for r in load(f"{OUT}/cal_vias.json")}

TOL=0.00002  # ~2 m
def r5(p): return [round(p[0],5), round(p[1],5)]

feats=[]
for cod,tids in via_tramos.items():
    lines=[LineString(tramo[t]) for t in tids]
    geom=unary_union(lines)
    try: geom=linemerge(geom)
    except Exception: pass
    geom=geom.simplify(TOL, preserve_topology=False)
    if geom.is_empty: continue
    if geom.geom_type=='LineString':
        coords=[[r5(c) for c in geom.coords]]
    else:
        coords=[[r5(c) for c in ls.coords] for ls in geom.geoms]
    v=vias.get(cod,{})
    feats.append({
        'type':'Feature',
        'properties':{'cod':cod,'n':v.get('display',''),'t':v.get('tipo','')},
        'geometry':{'type':'MultiLineString','coordinates':coords}
    })

fc={'type':'FeatureCollection','features':feats}
with open(f"{OUT}/cal_mapa.geojson",'w',encoding='utf-8') as f:
    json.dump(fc, f, ensure_ascii=False, separators=(',',':'))
print("Features (vías dibujables):", len(feats))
