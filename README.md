# Mocho · Atlas del glaciar

Área de estudio del glaciar Mocho en un mapa 3D. Primera entrega basada en la sección 1.1 del Informe final — Mocho 2025–2026, versión final (DGA / Universidad Austral de Chile).

Sitio: https://sqpaul.github.io/mocho-dashboard/

## Uso

Desde esta carpeta: `python -m http.server 8000 --bind 127.0.0.1`. Abrir http://127.0.0.1:8000.

Web estática sin compilación ni claves API. Incluye relieve 3D/2D, zoom, giro, reinicio, pantalla completa, capas seleccionables y fichas. Requiere conexión para obtener el relieve externo de Mapterhorn.

## Fuentes

- Imagen Sentinel-2 del 25/03/2025 en falso color y delimitaciones de 2025: AnexosDigitales, anexo 2.
- Superficie 4,94 ± 0,09 km² y perímetro 13,09 km: Tabla 1, DGA (2025).
- Elevaciones 1.625 / 1.974 / 2.430 m s.n.m.: DEM Pléiades del 15/03/2020, citado en Tabla 1.
- BMCH: coordenadas geográficas de Tabla 2, p. 30.
- Sector AWS-Mocho: baliza B15, levantamiento de noviembre de 2025, anexo 3. Representa una referencia de sector, no la ubicación exacta de la estación. AWS-DGA se describe en la ficha sin asignar coordenadas no verificadas.
- Relieve de contexto: [Mapterhorn](https://mapterhorn.com/attribution/), con exageración vertical 1×. Es independiente de los DEM científicos del proyecto.

Se conservan las cifras publicadas en el informe. La geometría archivada tiene pequeñas diferencias respecto de sus atributos de superficie; no se sustituyen los valores del informe por cálculos del mapa. Los datos originales no se modifican.

## Datos web

`data/study-area.json`: geometrías WGS84, encuadre, fechas y procedencia. `data/satellite-2025.webp`: derivado de visualización reproyectado a Web Mercator. No se publican el ZIP de anexos, los registros GNSS originales ni el PDF completo.

Regeneración: `python scripts/prepare_data.py --source RUTA/AnexosDigitales`. Dependencias: Fiona, Shapely, pyproj, Rasterio, NumPy y Pillow. No requiere GeoPandas.

## Publicación y verificación

GitHub Pages: rama `main`, carpeta raíz. Las rutas relativas permiten servir el sitio bajo `/mocho-dashboard/`.

`scripts/check_dashboard.py` verifica el sitio con Playwright/Edge y guarda capturas de escritorio y móvil en `test-results/` (excluido de Git). Acepta una URL opcional para comprobar el sitio publicado.

MapLibre GL JS 6.8.0 se distribuye en `vendor/`, con su licencia BSD-3-Clause. Las licencias de las bibliotecas no se aplican automáticamente a los datos del proyecto. Tipografías DM Sans y Manrope mediante Google Fonts, con alternativas del sistema.

Diseño y desarrollo: [Paul Sandoval-Quilodrán](https://github.com/SQPaul). Desarrollo del informe: GlacioUACh.
