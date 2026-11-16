import json, sys, math
from collections import defaultdict
from shapely.geometry import LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree

DIR=sys.argv[1]; OUT=sys.argv[2]
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

# Geometría por vía + orientación dominante (tensor de orientación) + longitud
geo={}; ang={}; cent={}; length={}
cods=[]
for cod,tids in via_tramos.items():
    line=unary_union([tramo_geom[t] for t in tids])
    geoms=[line] if line.geom_type=='LineString' else list(line.geoms)
    sx=sy=0.0; L=0.0
    for ls in geoms:
        cs=list(ls.coords)
        for i in range(len(cs)-1):
            dx=cs[i+1][0]-cs[i][0]; dy=cs[i+1][1]-cs[i][1]
            seg=math.hypot(dx,dy)
            if seg==0: continue
            th=math.atan2(dy,dx)
            sx+=seg*math.cos(2*th); sy+=seg*math.sin(2*th); L+=seg
    if L==0: continue
    geo[cod]=line; ang[cod]=0.5*math.atan2(sy,sx); length[cod]=L
    cent[cod]=line.centroid; cods.append(cod)

def diff_ang(a,b):
    d=abs(a-b)%math.pi
    return min(d, math.pi-d)  # 0..pi/2

# Índice espacial de líneas para buscar vecinas cercanas
geoms_list=[geo[c] for c in cods]
tree=STRtree(geoms_list)

MAXD=150.0; MAXANG=math.radians(15); MINOVER=0.5
pares=[]; lado={}
vistos=set()
for c in cods:
    g=geo[c]; axis=ang[c]
    ux,uy=math.cos(axis),math.sin(axis)   # eje de la vía c
    cand=tree.query(g.buffer(MAXD))
    for i in cand:
        o=cods[i]
        if o==c: continue
        key=(c,o) if c<o else (o,c)
        if key in vistos: continue
        if diff_ang(ang[c],ang[o])>MAXANG: continue
        d=g.distance(geo[o])
        if d>MAXD or d<0.5: continue  # d<0.5: se tocan, no son paralelas
        # Solape: proyectar puntos de ambas sobre el eje de c
        def proj(line):
            vals=[]
            parts=[line] if line.geom_type=='LineString' else list(line.geoms)
            for ls in parts:
                for x,y in ls.coords: vals.append(x*ux+y*uy)
            return min(vals),max(vals)
        a0,a1=proj(g); b0,b1=proj(geo[o])
        ov=max(0.0, min(a1,b1)-max(a0,b0))
        if ov < MINOVER*min(a1-a0, b1-b0): continue
        vistos.add(key)
        # lado: signo del producto cruzado eje_c x (centro_o - centro_c)
        cx=cent[o].x-cent[c].x; cy=cent[o].y-cent[c].y
        cross=ux*cy-uy*cx
        pares.append((c,o,round(d)))

print("Pares de paralelas detectadas:", len(pares))
json.dump([[c,o,d] for c,o,d in pares], open(f"{OUT}/cal_paralelas.json",'w',encoding='utf-8'))

def nom(c): return vias.get(c,{}).get('display',f'cod {c}')
# Muestra: 25 pares, variados por distancia
pares_ord=sorted(pares, key=lambda x:x[2])
muestra=pares_ord[:8]+pares_ord[len(pares_ord)//2:len(pares_ord)//2+9]+pares_ord[-8:]
print("\n=== MUESTRA PARA REVISAR (nombre A  ||  nombre B  · distancia) ===")
for c,o,d in muestra:
    print(f"   {nom(c):38s} || {nom(o):38s}  · {d} m")
