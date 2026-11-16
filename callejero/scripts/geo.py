import json, sys, math
from collections import defaultdict, Counter
from shapely.geometry import LineString, shape
from shapely.strtree import STRtree
from shapely.ops import unary_union

DIR = sys.argv[1]
OUT = sys.argv[2]

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

# Proyección aproximada a metros (Málaga ~36.72N)
LAT0 = 36.72
KX = 111320.0 * math.cos(math.radians(LAT0))
KY = 110574.0
def tx(lon, lat): return (lon * KX, lat * KY)

def geom_m(gj):
    # Reconstruye una geometría shapely en METROS desde un geometry GeoJSON.
    t = gj['type']; c = gj['coordinates']
    def pt(p): return tx(p[0], p[1])
    def ring(r): return [pt(p) for p in r]
    if t == 'Polygon':
        return shape({'type':'Polygon','coordinates':[[pt(p) for p in rr] for rr in c]})
    if t == 'MultiPolygon':
        return shape({'type':'MultiPolygon','coordinates':[[[pt(p) for p in rr] for rr in poly] for poly in c]})
    if t == 'LineString':
        return LineString([pt(p) for p in c])
    if t == 'MultiLineString':
        from shapely.geometry import MultiLineString
        return MultiLineString([[pt(p) for p in ln] for ln in c])
    raise ValueError(t)

# ── Barrios (metros) ───────────────────────────────────────
barrios = []  # (num, nombre, geom)
for f in load(f"{DIR}/barrio.geojson")['features']:
    p = f['properties']; g = f.get('geometry')
    if not g: continue
    barrios.append((p['NUMBARRIO'], (p['NOMBARRIO'] or '').strip(), geom_m(g)))
barrio_geoms = [b[2] for b in barrios]
btree = STRtree(barrio_geoms)
print("Barrios:", len(barrios))

# ── Tramos activos (metros) + endpoints en grados (para cruces) ──
raw = load(f"{DIR}/tramo.geojson")['features']
tramo_geom = {}     # id -> LineString (metros)
tramo_ends = {}     # id -> (p0, p1) en grados redondeados
for f in raw:
    p = f['properties']; g = f.get('geometry')
    if p.get('FECBAJA') or not g or g['type'] != 'LineString': continue
    idt = p['ID_TRAMOVIAL']
    tramo_geom[idt] = geom_m(g)
    cs = g['coordinates']
    tramo_ends[idt] = (tuple(round(v,6) for v in cs[0]), tuple(round(v,6) for v in cs[-1]))
print("Tramos activos con geometría:", len(tramo_geom))

# ── Relación tramo -> vía ──
via_tramos = defaultdict(list)
for f in load(f"{DIR}/relacion.geojson")['features']:
    p = f['properties']
    idt, cod = p['ID_TRAMOVIAL'], p['CODVIAL5']
    if idt in tramo_geom:
        via_tramos[cod].append(idt)

# ── CALLE ↔ BARRIO ─────────────────────────────────────────
via_barrio = {}
multi_barrio = 0
for cod, tids in via_tramos.items():
    linea = unary_union([tramo_geom[t] for t in tids])
    cand = btree.query(linea)
    metros = {}
    for i in cand:
        inter = linea.intersection(barrio_geoms[i])
        L = inter.length
        if L > 1.0:  # al menos 1 metro dentro
            metros[i] = metros.get(i, 0) + L
    if not metros:
        continue
    ordenados = sorted(metros.items(), key=lambda kv: -kv[1])
    via_barrio[cod] = [{'barrio': barrios[i][1], 'num': barrios[i][0], 'metros': round(m)} for i, m in ordenados]
    if len(ordenados) > 1: multi_barrio += 1

con_barrio = len(via_barrio)
print(f"\nVías con barrio asignado: {con_barrio}")
print(f"Vías que pasan por MÁS de un barrio: {multi_barrio}")

# ── CRUCES (comparten extremo) ─────────────────────────────
punto_vias = defaultdict(set)  # endpoint -> set de vías
tramo_via = {}
for cod, tids in via_tramos.items():
    for t in tids:
        tramo_via[t] = cod
for idt, (a, b) in tramo_ends.items():
    cod = tramo_via.get(idt)
    if cod is None: continue
    punto_vias[a].add(cod)
    punto_vias[b].add(cod)

pares = set()
vecinos = defaultdict(set)
for pt, vias in punto_vias.items():
    if len(vias) >= 2:
        vl = sorted(vias)
        for i in range(len(vl)):
            for j in range(i+1, len(vl)):
                pares.add((vl[i], vl[j]))
                vecinos[vl[i]].add(vl[j])
                vecinos[vl[j]].add(vl[i])
print(f"\nPares de vías que se cruzan: {len(pares)}")
print(f"Vías con al menos un cruce: {len(vecinos)}")

# Guardar
json.dump(via_barrio, open(f"{OUT}/cal_via_barrio.json",'w',encoding='utf-8'), ensure_ascii=False)
json.dump({str(k): sorted(v) for k,v in vecinos.items()}, open(f"{OUT}/cal_cruces.json",'w',encoding='utf-8'), ensure_ascii=False)

# Validación legible: cruces de la Alameda Principal
vias = {r['cod']: r for r in load(f"{OUT}/cal_vias.json")}
def nom(c): return vias.get(c,{}).get('display', f'cod {c}')
ala = [c for c,r in vias.items() if 'Alameda Principal' in r['display']]
if ala:
    c = ala[0]
    print(f"\nEjemplo — cruces de «{nom(c)}»:")
    for o in sorted(vecinos.get(c, []), key=nom)[:15]:
        print("   ·", nom(o))
