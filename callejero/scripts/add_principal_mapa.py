import json, sys
MAPA=sys.argv[1]; PRIN=sys.argv[2]
mapa=json.load(open(MAPA,encoding='utf-8'))
prin=json.load(open(PRIN,encoding='utf-8'))  # {cod(str):0/1}
n=0
for f in mapa['features']:
    cod=f['properties']['cod']
    p=prin.get(str(cod), 0)
    f['properties']['p']=int(p)
    n+=p
json.dump(mapa, open(MAPA,'w',encoding='utf-8'), ensure_ascii=False, separators=(',',':'))
print("Features:", len(mapa['features']), "| principales:", n)
