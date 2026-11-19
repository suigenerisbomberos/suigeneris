import json, sys, re
from shapely.geometry import shape, mapping

DIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

CONECT={'de','del','la','el','los','las','y'}
ACC={'historico':'histórico','jardin':'jardín','cadiz':'cádiz','bailen':'bailén',
 'malaga':'málaga','maria':'maría','jose':'josé','andalucia':'andalucía','olias':'olías',
 'martiricos':'martiricos','caña':'caña','leon':'león','angeles':'ángeles','capuchinos':'capuchinos'}
def titul(s):
    s=' '.join(s.strip().split())
    out=[]
    for i,w in enumerate(s.split(' ')):
        lw=w.lower()
        lw=ACC.get(lw,lw)
        if i>0 and lw in CONECT: out.append(lw)
        else: out.append(lw[:1].upper()+lw[1:])
    return ' '.join(out)

R=5
def rc(coords):
    if isinstance(coords[0],(int,float)): return [round(coords[0],R), round(coords[1],R)]
    return [rc(c) for c in coords]

feats=[]
for f in load(f"{DIR}/barrio.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if not g: continue
    geom=shape(g).simplify(0.00008, preserve_topology=True)  # ~8 m
    if geom.is_empty: continue
    gj=mapping(geom)
    gj['coordinates']=rc(gj['coordinates'])
    feats.append({'type':'Feature',
      'properties':{'num':p['NUMBARRIO'],'n':titul(p['NOMBARRIO'] or '')},
      'geometry':gj})

fc={'type':'FeatureCollection','features':feats}
with open(f"{OUT}/cal_barrios.geojson",'w',encoding='utf-8') as fo:
    json.dump(fc, fo, ensure_ascii=False, separators=(',',':'))
print("Barrios:", len(feats))
print("Ejemplos:", ', '.join(x['properties']['n'] for x in feats[:12]))
