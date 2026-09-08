# Mocho · Atlas del glaciar

Atlas interactivo del glaciar Mocho. Incluye el capítulo 1 (área de estudio y balance de masa) y el capítulo 2 (variaciones de glaciares), basados en el Informe final — Mocho 2025–2026, versión final (DGA / Universidad Austral de Chile).

Sitio: https://sqpaul.github.io/mocho-dashboard/

## Uso

Desde esta carpeta: `python -m http.server 8000 --bind 127.0.0.1`. Abrir http://127.0.0.1:8000 o `http://127.0.0.1:8000/#capitulo-2`.

Web estática sin compilación ni claves API. Incluye relieve 3D/2D, balizas GNSS consultables, Figura 2 y navegación horizontal por capítulos. El capítulo 2 añade Figura 4 (dos series de superficie con filtros, incertidumbre, tabla y CSV) y Figura 7 (11 contornos sobre el mismo motor 3D, compartido en `map-common.js`). Requiere conexión para obtener el relieve externo de Mapterhorn; si falla, ambos mapas pasan a 2D.

## Fuentes

- Imagen Sentinel-2 del 25/03/2025 en falso color y delimitaciones de 2025: AnexosDigitales, anexo 2.
- Superficie 4,94 ± 0,09 km² y perímetro 13,09 km: Tabla 1, DGA (2025).
- Elevaciones 1.625 / 1.974 / 2.430 m s.n.m.: DEM Pléiades del 15/03/2020, citado en Tabla 1.
- BMCH: coordenadas geográficas de Tabla 2, p. 30.
- Sector AWS-Mocho: baliza B15, levantamiento de noviembre de 2025, anexo 3. Representa una referencia de sector, no la ubicación exacta de la estación. AWS-DGA se describe en la ficha sin asignar coordenadas no verificadas.
- Relieve de contexto: [Mapterhorn](https://mapterhorn.com/attribution/), con exageración vertical 1×. Es independiente de los DEM científicos del proyecto.

Se conservan las cifras publicadas en el informe. La geometría archivada tiene pequeñas diferencias respecto de sus atributos de superficie; no se sustituyen los valores del informe por cálculos del mapa. Los datos originales no se modifican.

## Datos web

`data/study-area.json`: geometrías WGS84, encuadre, fechas y procedencia. Los fondos `satellite-2025.webp` y `satellite-2026.webp` están georreferenciados en Web Mercator; el segundo corresponde al 10/03/2026. Las series de `glacier-variations.json` conservan los valores del Excel del Anexo 2.

`icecap-history.geojson` incorpora 1979, 1987, 2000, 2005, 2017, 2020, 2022, 2023, 2024, 2025 y 2026, con archivo y CRS original por contorno. Fuentes históricas: `Mocho_DGA/SIG/Delimitacion_glaciar` y `Mocho_DGA/2023-2024/GIS/Delimitacion`; años recientes: Anexo 2. La cobertura de la Figura 7 es parcial: faltan 1976, 1986 y 2015. Los archivos de 1979 y 1987 no se rebautizan como 1976 y 1986. No se publican el ZIP de anexos, los registros GNSS originales ni el PDF completo.

Regeneración: `python scripts/prepare_data.py --source RUTA/AnexosDigitales`. Dependencias: Fiona, Shapely, pyproj, Rasterio, NumPy y Pillow. No requiere GeoPandas.

Figura 2 y balizas: `python scripts/prepare_history_stakes.py`. Capítulo 2: `python scripts/prepare_variations.py` (añade openpyxl; rutas del archivo local definidas al inicio). El entorno `C:\Users\pauls\anaconda3\envs\geopy\python.exe` dispone de estas dependencias.

## Publicación y verificación

GitHub Pages: rama `main`, carpeta raíz. Las rutas relativas permiten servir el sitio bajo `/mocho-dashboard/`.

`scripts/check_dashboard.py` verifica el sitio con Playwright/Edge y guarda capturas de escritorio y móvil en `test-results/` (excluido de Git). Acepta una URL opcional para comprobar el sitio publicado.

Entorno de pruebas: Python de `geopy`, Microsoft Edge y Playwright 1.62 instalado con `python -m pip install --target .cache/browser-deps playwright`. Ejecutar `python scripts/check_dashboard.py` con ese mismo Python. Comprueba también coordenadas proyectadas en pantalla, consulta por teclado y fallos de datos, imagen y relieve.

MapLibre GL JS 6.8.0 se distribuye en `vendor/`, con su licencia BSD-3-Clause. Las licencias de las bibliotecas no se aplican automáticamente a los datos del proyecto. Tipografías DM Sans y Manrope mediante Google Fonts, con alternativas del sistema.

Diseño y desarrollo: [Paul Sandoval-Quilodrán](https://github.com/SQPaul). Desarrollo del informe: GlacioUACh.
