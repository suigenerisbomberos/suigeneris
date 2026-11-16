import json, sys

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

DIR = sys.argv[1]
for name in ['vial','tipovial','relacion','barrio','distrito','tramo']:
    d = load(f"{DIR}/{name}.geojson")
    feats = d.get('features', [])
    print(f"\n===== {name}.geojson =====")
    print("type:", d.get('type'), "| nº features:", len(feats))
    if feats:
        f0 = feats[0]
        props = f0.get('properties', {})
        geom = f0.get('geometry') or {}
        print("geometry type:", geom.get('type'))
        print("propiedades (ejemplo):")
        for k, v in props.items():
            print(f"   {k!r}: {v!r}")
