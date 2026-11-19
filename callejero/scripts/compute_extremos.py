import json, sys
from collections import defaultdict, Counter
DIR=sys.argv[1]; OUT=sys.argv[2]
def load(p):
    with open(p, encoding='utf-8') as f: return json.load(f)

# Tramos activos: id -> (nodoA, nodoB) redondeados
tramo_ends={}
for f in load(f"{DIR}/tramo.geojson")['features']:
    p=f['properties']; g=f.get('geometry')
    if p.get('FECBAJA') or not g or g['type']!='LineString': continue
    cs=g['coordinates']
    tramo_ends[p['ID_TRAMOVIAL']]=(tuple(round(v,6) for v in cs[0]), tuple(round(v,6) for v in cs[-1]))

# Relación tramo -> vía
via_tramos=defaultdict(list); tramo_via={}
for f in load(f"{DIR}/relacion.geojson")['features']:
    p=f['properties']; idt,cod=p['ID_TRAMOVIAL'],p['CODVIAL5']
    if idt in tramo_ends: via_tramos[cod].append(idt); tramo_via[idt]=cod

# nodo -> conjunto de vías que pasan por ahí
punto_vias=defaultdict(set)
for idt,(a,b) in tramo_ends.items():
    cod=tramo_via.get(idt)
    if cod is None: continue
    punto_vias[a].add(cod); punto_vias[b].add(cod)

# Para cada vía, sus nodos extremos (aparecen una sola vez entre SUS tramos)
extremos={}
for cod,tids in via_tramos.items():
    cont=Counter()
    for t in tids:
        a,b=tramo_ends[t]; cont[a]+=1; cont[b]+=1
    nodos_fin=[nodo for nodo,c in cont.items() if c==1]  # extremos de la cadena
    conect=set()
    for nodo in nodos_fin:
        for otra in punto_vias.get(nodo,()):
            if otra!=cod: conect.add(otra)
    if conect: extremos[cod]=sorted(conect)

json.dump({str(k):v for k,v in extremos.items()}, open(f"{OUT}/cal_extremos.json",'w',encoding='utf-8'), ensure_ascii=False)
print("Vías con extremos/conexiones:", len(extremos))
import statistics
tam=[len(v) for v in extremos.values()]
print("Media de conexiones por extremo:", round(statistics.mean(tam),1), "| máx:", max(tam))
