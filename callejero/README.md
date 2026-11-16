# Callejero de Málaga — datos y preparación

Datos preparados para el módulo Callejero (ver hoja de ruta de José en
`~/Desktop/ACADEMIA/CALLEJERO/HOJA DE RUTA CALLEJERO.md`). Arquitectura: **Firebase**
(no Supabase). El contenido compartido irá bajo `/callejero/...` en Firestore.

## Fuente oficial
Portal `datosabiertos.malaga.eu` (CC BY 4.0 — citar la fuente en pantalla).
Base: `.../planimetria/callejero/`. Archivos usados: `da_cartografiaVial`,
`da_cartografiaTramoVial`, `da_cartografiaRelacionTramoVial`, `da_cartografiaTipoVial`,
`da_cartografiaBarrio`, `da_cartografiaDistritoMunicipal` (todos `-4326`, lon/lat).
Los `.geojson` crudos (≈19 MB) NO se versionan: se bajan y se procesan.

## Pipeline (`scripts/`, Python 3 + shapely)
1. `process_vias.py` → une Vial+Tramo+Relación (FECBAJA nula), normaliza nombres
   (artículo al frente, Title Case) y aplica tildes → `data/cal_vias.json`.
2. `geo.py` → calle↔barrio (longitud en cada barrio) y cruces (comparten extremo)
   → `data/cal_via_barrio.json`, `data/cal_cruces.json`.
3. `principal.py` → marca principal/menor (tipo + longitud ≥700 m) → `data/cal_principal.json`.
4. `paralelas.py` → paralelas por geometría (dir <15°, <150 m, solape >50%)
   → `data/cal_paralelas.json`. **Primera pasada con ruido: José revisa/descarta en el panel.**

## Resultado (validado contra cifras oficiales, 2026-11-16)
- **5.298 vías con trazado** (4.136 calles, 298 pasajes, 226 plazas, 136 avenidas,
  43 carreteras, 41 glorietas, 33 paseos, 7 autovías… — todo cuadra).
- 5.296 con barrio; 1.370 pasan por varios barrios.
- 10.764 pares de cruces (validado: Alameda Principal cruza con Alameda Colón,
  Córdoba, Puerta del Mar, Marqués de Larios, Plaza de la Marina, Puente de Tetuán).
- 798 principales / 4.499 menores.
- ~7.987 pares de paralelas (candidatos, a revisar).

## Formato de `cal_vias.json`
Lista de `{cod, tipo, codtip, nombre, display, nomvial_orig, nTramos}`.
`cod` = CODVIAL5 (clave para cruzar con barrios/cruces/paralelas/principal).

## Pendiente
Geometría de tramos para el mapa (Fase 1), distrito por vía, y cargar a Firestore.
2 PDF de José en iCloud sin descargar (distritos/barrios mudos, polígonos mudo).
