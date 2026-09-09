# Mocho · Atlas del glaciar

Atlas interactivo del glaciar Mocho. Incluye el capítulo 1 (área de estudio y balance de masa), el capítulo 2 (variaciones de glaciares), el capítulo 3 (caracterización del manto nival) y el capítulo 4 (cinemática glaciar), basados en datos del proyecto DGA / Universidad Austral de Chile.

Sitio: https://sqpaul.github.io/mocho-dashboard/

## Uso

Desde esta carpeta: `python -m http.server 8000 --bind 127.0.0.1`. Abrir http://127.0.0.1:8000 o usar `#capitulo-2`, `#capitulo-3` y `#capitulo-4` para acceder directamente a las hojas siguientes.

Web estática sin compilación ni claves API. Incluye relieve 3D/2D, cuatro estaciones meteorológicas, las cumbres Mocho y Choshuenco, balizas GNSS consultables, balance de masa histórico y navegación horizontal por capítulos. El capítulo 2 añade dos series interactivas de superficie y 12 contornos; el capítulo 3 incorpora cinco campañas GPR y una tabla de resumen; el capítulo 4 muestra velocidad superficial interpolada y velocidades anuales en diez balizas. Los cuatro mapas comparten `map-common.js`. Requiere conexión para obtener el relieve externo de Mapterhorn; si falla, pasan a 2D. Las vistas no usan numeración de figura ni descargas.

## Fuentes

- Imagen Sentinel-2 del 10/03/2026 en falso color y delimitaciones de 2026: AnexosDigitales, anexo 2.
- Superficie 4,91 ± 0,09 km² y perímetro 12,45 km: Anexo 2, Figura 4 (2026).
- Elevaciones 1.625 / 1.974 / 2.430 m s.n.m.: DEM Pléiades del 15/03/2020, citado en Tabla 1.
- Estaciones meteorológicas: AWS Mocho1, AWS Mocho2 y AWS DGA desde `estaciones.gpkg`; EMAM-Mocho comparte exactamente las coordenadas WGS84 de la baliza B15.
- Cumbres Mocho y Choshuenco: `cumbres.shp`, reproyectado desde UTM 18S a WGS84.
- Balizas del capítulo 1: la interfaz publica únicamente sus coordenadas WGS84; B15 tiene prioridad interactiva sobre EMAM-Mocho cuando ambas capas están visibles.
- Relieve de contexto: [Mapterhorn](https://mapterhorn.com/attribution/), con exageración vertical 1×. Es independiente de los DEM científicos del proyecto.
- Manto nival: GeoTIFF GPR del 08/10/2021, 14/10/2022, 17/10/2023, 19/10/2024 y 19/10/2025. Los raster se publican con la paleta Blues y una escala común de 0–17 m; la tabla conserva literalmente el resumen proporcionado para cada campaña.
- Cinemática glaciar: `Vel_GPS202510-202604.tif` y `Vel anual balizas_Mocho2025-2026.geojson`, ambos en EPSG:32718. El raster representa OCT 2025–ABR 2026 y se publica con paleta rainbow de 0–30 m/a. B11 conserva su velocidad del período 2024–2025; las otras nueve balizas corresponden a 2025–2026.

Se conservan las cifras publicadas en el informe. La geometría archivada tiene pequeñas diferencias respecto de sus atributos de superficie; no se sustituyen los valores del informe por cálculos del mapa. Los datos originales no se modifican.

## Datos web

`data/study-area.json`: geometrías 2026, cuatro estaciones y dos cumbres en WGS84, encuadre, fechas y procedencia. Las estaciones conservan únicamente nombre, latitud y longitud como metadata. El fondo activo `satellite-2026.webp` está georreferenciado en Web Mercator y corresponde al 10/03/2026. Las series de `glacier-variations.json` conservan los valores del Excel del Anexo 2.

`icecap-history.geojson` incorpora 1976, 1986, 2000, 2005, 2015, 2017, 2020, 2022, 2023, 2024, 2025 y 2026, con archivo y CRS original por contorno. Fuentes históricas: `Mocho_DGA/SIG/Delimitacion_glaciar`, `Mocho_DGA/2023-2024/GIS/Delimitacion` y los polígonos verificados del Anexo 2. La Figura 7 tiene cobertura completa respecto de la serie publicada. No se publican el ZIP de anexos, los registros GNSS originales ni el PDF completo.

`gpr-campaigns.json` describe las cinco campañas, sus coordenadas WGS84, la escala compartida, el espesor GPR muestreado en las diez balizas y la tabla de resumen. `gpr-2021.webp` a `gpr-2025.webp` son derivados RGBA transparentes; los GeoTIFF originales permanecen fuera de Git.

`velocity-2025-2026.json` describe el período, la escala rainbow, la georreferenciación del raster y diez balizas reproyectadas a WGS84 con solo nombre, período y velocidad anual. `velocity-202510-202604.webp` es el derivado RGBA transparente. Los insumos de `data/Velocidad/` permanecen fuera de Git.

Regeneración: `python scripts/prepare_data.py --source RUTA/AnexosDigitales`. El generador toma por defecto `data/geometrias/estaciones.gpkg`, `data/geometrias/cumbres.shp` y B15 desde el derivado de balizas. Dependencias: Fiona, Shapely, pyproj, Rasterio, NumPy y Pillow. No requiere GeoPandas.

Figura 2 y balizas: `python scripts/prepare_history_stakes.py`; la serie usa por defecto `data/bm_hist.xlsx` e incluye 2025–2026. Capítulo 2: `python scripts/prepare_variations.py` (añade openpyxl; rutas del archivo local definidas al inicio). El entorno `C:\Users\pauls\anaconda3\envs\geopy\python.exe` dispone de estas dependencias.

Capítulo 3: `python scripts/prepare_gpr.py`. Lee `data/GPR/GPR_DDMMYYYY.tif`, aplica Blues 0–17 m, muestrea cada raster en las coordenadas de `data/stakes.geojson` y genera únicamente los WebP y el manifiesto necesarios para la web. Requiere Rasterio, pyproj, NumPy, Pillow y Matplotlib.

Capítulo 4: `python scripts/prepare_velocity.py`. Lee los dos insumos de `data/Velocidad/`, conserva NoData como transparencia, aplica rainbow 0–30 m/a, transforma el raster y las balizas desde EPSG:32718 a WGS84 y genera solo los dos derivados web.

## Publicación y verificación

GitHub Pages: rama `main`, carpeta raíz. Las rutas relativas permiten servir el sitio bajo `/mocho-dashboard/`.

`scripts/check_dashboard.py` verifica los cuatro capítulos con Playwright/Edge y guarda capturas de escritorio y móvil en `test-results/` (excluido de Git). Acepta una URL opcional para comprobar el sitio publicado.

Entorno de pruebas: Python de `geopy`, Microsoft Edge y Playwright 1.62 instalado con `python -m pip install --target .cache/browser-deps playwright`. Ejecutar `python scripts/check_dashboard.py` con ese mismo Python. Comprueba también coordenadas proyectadas en pantalla, consulta por teclado y fallos de datos, imagen y relieve.

MapLibre GL JS 6.8.0 se distribuye en `vendor/`, con su licencia BSD-3-Clause. Las licencias de las bibliotecas no se aplican automáticamente a los datos del proyecto. Tipografías DM Sans y Manrope mediante Google Fonts, con alternativas del sistema.

Diseño y desarrollo: Paul Sandoval-Quilodrán. Desarrollo del informe: GlacioUACh.
