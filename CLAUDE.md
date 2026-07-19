# CLAUDE.md — Plataforma de tests SUI GENERIS

Este archivo lo lee Claude Code automáticamente al abrir el proyecto. Fali (el dueño) NO programa. Ejecuta tú todo lo técnico y explícale en cristiano, sin dar por hecho conocimientos.

## Qué es este proyecto

Plataforma web de tests para opositores a bombero de la academia SUI GENERIS (Málaga, Rincón de la Victoria). Se usa como herramienta online de apoyo para los alumnos presenciales. Lanzamiento previsto: septiembre.

* Repositorio: `suigenerisbomberos/suigeneris`
* Web publicada: https://suigenerisbomberos.github.io/suigeneris (GitHub Pages)
* Arquitectura: un único archivo HTML (todo en uno: HTML + CSS + JS). Sin servidor backend.
* Base de datos y auth: Firebase (Firestore + Authentication)

## Funciones que ya tiene (NO romper)

Login de alumnos (email/contraseña), tests por tema, test mixto, simulacro cronometrado, repaso de falladas, ranking entre alumnos, sistema de puntos, rachas, logros/badges, control de dispositivos (máx. 3 por cuenta), modo estudio vs modo examen, notas por pregunta, historial, e instalable como app (PWA).

## Datos técnicos clave

* Proyecto Firebase: `suigeneris-66867`
* App ID: `1:495869347021:web:d603c9fade03a716d4d584`
* Cuentas admin: `josecarlos099@hotmail.com` y `miguelnl83@gmail.com`

### Firestore

* Colección `temas` → subcolección `preguntas`.
* Campos de cada pregunta: `enunciado` (texto), `opciones` (array de 4), `correcta` (índice base 0 de la opción correcta), `explicacion` (texto), `creadaEn` (serverTimestamp). NOTA: en el código el campo de fecha se llama `creadaEn` (en español), no `createdAt`. Los `bloques` y `temas` usan `creadoEn` y `orden`.
* El campo `explicacion` debe ir completo: por qué es correcta la buena + por qué falla cada incorrecta, concatenado con notación `->`. Nunca resumir ni truncar.

## Reglas de oro (aprendidas a base de errores)

* Compatibilidad Safari: el código ACTUAL usa módulos ES (`<script type="module">`) con el SDK moderno de Firebase v10. Esto funciona bien en Safari/iPhone SIEMPRE que la web se sirva por `https://` (que es como la usan los alumnos, vía GitHub Pages). Los módulos ES SOLO fallan si se abre el archivo HTML en local haciendo doble clic (protocolo `file://`). Para probar en local, hay que levantar un servidor local (p. ej. `python3 -m http.server`), no abrir el archivo directamente.
* Importar preguntas: solo `addDoc`. NUNCA borrar preguntas existentes salvo confirmación explícita de Fali.
* Antes de importar en lote, las reglas de Firestore se ponen temporalmente en `if true` y se restauran al terminar.

## Prioridades para el lanzamiento (por orden)

1. SEGURIDAD (urgente): las reglas de Firestore están en `if true`, o sea abiertas a cualquiera. Hay que cerrarlas a `request.auth != null`. Requiere acción manual de Fali en la consola de Firebase — guíale paso a paso.
2. Velocidad de carga con muchas preguntas ya cargadas.
3. Bug de la marca de agua: el archivo `MARCA AGUA A4_2025.png` tiene espacios en el nombre. En el login y en el CSS ya se referencia BIEN con `%20`. El fallo real está en el icono de la PWA: el `<link rel="manifest">` usa doble codificación `%2520` y por eso el icono de la app instalada no carga. Solución definitiva: renombrar el archivo a algo sin espacios (p. ej. `marca-agua.png`) y actualizar las 3 referencias (CSS, `<img>` del login y manifest).
4. Pulido en móvil y PWA (la mayoría de alumnos la usan en el móvil).
5. Opcional: dominio propio en vez del enlace de GitHub Pages.

## Marca e identidad

* Azul marino: `#1B2E4B`
* Naranja: `#D4500A`

## Cómo trabajar con Fali

* Órdenes directas en lenguaje llano. Sin preguntas de clarificación antes de empezar: aplica estos estándares desde el principio.
* Toma la iniciativa en estructura y organización.
* Cambios grandes o irreversibles (tocar Firebase, borrar datos, publicar): explícaselos antes y espera su OK.
* No es programador: nada de jerga sin traducir.
