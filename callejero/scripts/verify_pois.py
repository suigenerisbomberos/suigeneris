import os, re, json, fitz
from collections import Counter
DATA="/Users/josecarlos/suigeneris/callejero/data"
FOLDER="/Users/josecarlos/Desktop/ACADEMIA/CALLEJERO/CALLEJERO PARA PLATAFORMA/PUNTOS DE INTERES PLATAFORMA 2026"
FILES=[
 ("01 Bibliotecas Málaga 2026.pdf","bibliotecas"),("02 Centros Educativos (Colegios, Institutos, etc 2026.pdf","colegios"),
 ("03 Cementerios 2026.pdf","cementerios"),("04 Consulados en Málaga 2026.pdf","consulados"),
 ("05 Delegaciones Oficiales Málaga 2026.pdf","delegaciones"),("06 Facultades, Escuelas Universitarias, Colegios Oficiales y otros 2026.pdf","facultades"),
 ("07 Hoteles de Málaga 2026.pdf","hoteles"),("08 Hospitales y Centros de Salud 2026.pdf","salud"),
 ("09 Instalaciones Deportivas 2.pdf","deportivas"),("10 Mercados Municipales 2.pdf","mercados"),
 ("11 Comisarias de policía Nacional y Local - Comandancia Guardia Civil 2026.pdf","comisarias"),
 ("13 Jardines y Parques 2026.pdf","jardines"),("14 Juntas Municipales de Distritos 2.pdf","juntas"),
 ("16 Parroquias de Málaga 2026.pdf","parroquias"),("17 Playas de Málaga 2026.pdf","playas"),
 ("19 Polígonos Industriales y Comerciales de Málaga 2026.pdf","poligonos"),("20 Puentes sobre el Guadalmedina 2026.pdf","puentes"),
 ("21 Servicios Públicos sedes Málaga 2026.pdf","servicios_publicos"),("22 Teatros, Salas de Espectáculos y Centros Culturales 2026.pdf","teatros"),
 ("23 Museos de Málaga 2026.pdf","museos"),("24 Palacios y castillos Málaga capital 2.pdf","palacios"),
 ("Fuentes Ornamentales 2026.pdf","fuentes"),
]
def maxnum(path):
    doc=fitz.open(path); mx=0
    for pg in doc:
        for l in pg.get_text().split('\n'):
            m=re.match(r'^\s*(\d{1,3})(\s|$)', l.strip())
            if m: mx=max(mx,int(m.group(1)))
    return mx

pts=json.load(open(f"{DATA}/cal_puntos.json",encoding='utf-8'))
porcat=Counter(p['cat'] for p in pts)
oob=Counter()
for p in pts:
    if not(36.58<p['lat']<36.85 and -4.70<p['lng']<-4.25): oob[p['cat']]+=1
print(f"{'categoría':22}{'PDF(nº)':>8}{'puestos':>9}{'fuera':>7}")
for fn,slug in FILES:
    path=os.path.join(FOLDER,fn)
    mx=maxnum(path) if os.path.exists(path) else 0
    flag=' ⚠️' if (mx-porcat.get(slug,0))>mx*0.15 and mx>0 else ''
    print(f"{slug:22}{mx:>8}{porcat.get(slug,0):>9}{oob.get(slug,0):>7}{flag}")
print("\nTOTAL puntos:",len(pts))
