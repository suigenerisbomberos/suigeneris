import json, sys, math
from collections import defaultdict, Counter
from shapely.geometry import LineString
from shapely.ops import unary_union

DIR = sys.argv[1]; OUT = sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

LAT0=36.72; KX=111320.0*math.cos(math.radians(LAT0)); KY=110574.0
def tx(p): return (p[0]*KX, p[1]*KY)

tramo_geom={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    tramo_geom[p['ID_TRAMOVIAL']]=LineString([tx(c) for c in g['coordinates']])

via_tramos=defaultdict(list)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']
    if p['ID_TRAMOVIAL'] in tramo_geom: via_tramos[p['CODVIAL5']].append(p['ID_TRAMOVIAL'])

vias={r['cod']:r for r in load(f"{OUT}/cal_vias.json")}

# Tipos que son principales por naturaleza
TIPOS_PRINC={'Autovía','Autovia','Carretera','Avenida','Paseo','Alameda','Bulevar','Ronda','Plaza','Glorieta'}
UMBRAL_LARGA=700.0  # metros: una calle "larga" también es principal

long_m={}; principal={}
for cod,tids in via_tramos.items():
    L=sum(tramo_geom[t].length for t in tids)
    long_m[cod]=L
    tipo=vias.get(cod,{}).get('tipo','')
    principal[cod]= (tipo in TIPOS_PRINC) or (L>=UMBRAL_LARGA)

json.dump({str(k):(1 if v else 0) for k,v in principal.items()},
          open(f"{OUT}/cal_principal.json",'w',encoding='utf-8'))

nprin=sum(1 for v in principal.values() if v)
print("Vías con longitud:", len(long_m))
print(f"PRINCIPALES: {nprin}  ·  MENORES: {len(principal)-nprin}")
print("\nPrincipales por motivo:")
por_tipo=Counter()
for cod,v in principal.items():
    if not v: continue
    tipo=vias.get(cod,{}).get('tipo','')
    por_tipo['por tipo ('+tipo+')' if tipo in TIPOS_PRINC else 'calle larga (>=700m)']+=1
for k,n in por_tipo.most_common(12): print(f"   {n:5d}  {k}")
print("\nLas 10 vías más largas:")
for cod in sorted(long_m, key=lambda c:-long_m[c])[:10]:
    print(f"   {round(long_m[cod]):6d} m  {vias.get(cod,{}).get('display','?')}")
