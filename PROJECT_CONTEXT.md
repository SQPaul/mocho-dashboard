# Contexto de continuidad — Mocho Dashboard

Este documento permite retomar el trabajo sin reconstruir decisiones ni volver a explorar todos los anexos.

## Objetivo

Crear un dashboard público de despedida del proyecto de monitoreo del glaciar Mocho: una pieza profesional, visualmente memorable y útil para el equipo. Se desarrolla por capítulos a partir del informe final y sus anexos digitales. La primera entrega corresponde a **1.1 Área de estudio**.

## Estado actual

- Repositorio: https://github.com/SQPaul/mocho-dashboard
- Sitio público: https://sqpaul.github.io/mocho-dashboard/
- Rama publicada: main, raíz del repositorio mediante GitHub Pages.
- Primera vista terminada: mapa 3D/2D, imagen Sentinel-2, polígonos del glaciar y capa de hielo, referencias BMCH/AWS-Mocho, métricas, fuentes y diseño móvil.
- Capítulo 2: navegación horizontal `#capitulo-1` / `#capitulo-2`, Figura 4 con dos paneles interactivos, tabla y CSV; Figura 7 con el mismo mapa 3D/2D del capítulo 1 y 11 delimitaciones verificadas.
- Contornos disponibles: 1979, 1987, 2000, 2005, 2017, 2020, 2022, 2023, 2024, 2025 y 2026. Faltan 1976, 1986 y 2015 del informe. Los archivos de 1979 y 1987 conservan sus fechas; no sustituyen los años del informe.
- Balizas: diez puntos nativos de MapLibre sobre el relieve, sin desplazamientos de marcadores HTML; consulta mediante clic o selector accesible. B15 y la referencia AWS comparten coordenada.
- Autoría visible: **Diseño y desarrollo — Paul Sandoval-Quilodrán**; debajo, **Desarrollo del informe — GlacioUACh**.
- Tono: herramienta científica elegante con firma discreta; no incluir una despedida explícita.

## Fuentes de trabajo

- Carpeta original: P:\Projects\Mocho_DGA\2025-2026\1_DASHBOARD
- Informe base: INFORME FINAL - Mocho 2025-2026_V_final.pdf
- Datos: AnexosDigitales
- Sección usada: 1.1 Área de estudio, páginas impresas 3–4; BMCH desde Tabla 2, p. 30; referencia AWS-Mocho desde B15 del anexo 3.
- Capítulo 2: Figura 4, p. 19, Figura 7, p. 22 y Anexo 2, «Variaciones de glaciares 2025–2026».
- Imagen web: Sentinel-2 falso color del 25/03/2025. Geometrías reproyectadas desde UTM 18S a WGS84.
- Superficie y perímetro: DGA 2025. Elevaciones: DEM Pléiades 2020.
- Mapterhorn aporta el relieve visual y no reemplaza los DEM científicos.

## Decisiones

- Conservar el diseño actual: fondo marfil, verdes apagados, mapa dominante, tipografía editorial y controles discretos.
- Mantener el sitio estático, sin claves API ni compilación, compatible con GitHub Pages.
- No publicar el ZIP, el PDF completo ni registros GNSS crudos; publicar solo derivados necesarios.
- No inventar coordenadas. B15 representa el sector AWS-Mocho; AWS-DGA queda sin marcador hasta tener una ubicación verificada.
- Nota histórica: mediciones desde 2003, monitoreo intensivo desde 2020, pérdida de masa predominante y balances positivos en 2004–2005, 2009–2010 y 2024–2025.
- Cada capítulo nuevo debe mostrar fecha, unidad, fuente y advertencias metodológicas cuando corresponda.

## Arquitectura

- index.html, style.css, additions.css y app.js: aplicación estática.
- map-common.js: motor 3D, imagen georreferenciada, controles y fichas compartidos por ambos capítulos. variations.js / variations.css: mapa histórico, gráfico y navegación; history.js / history.css: Figura 2.
- scripts/prepare_variations.py: regenera series, contornos y fondo 2026 desde el archivo local. Respeta CRS 32718/32719, omite geometrías nulas y conserva las superficies publicadas independientemente del área geométrica.
- Fuentes históricas: `P:\Projects\Mocho_DGA\SIG\Delimitacion_glaciar` (1979–2022), `2023-2024\GIS\Delimitacion` (2023–2024) y anexo 2 de `2025-2026\1_DASHBOARD` (2025–2026). Rutas exactas en `HISTORICAL` del generador y propiedades de cada contorno.
- data/study-area.json, data/satellite-2025.webp, data/mass-balance-history.json, data/stakes.geojson, data/glacier-variations.json, data/icecap-history.geojson y data/satellite-2026.webp: derivados web.
- scripts/prepare_data.py: regenera derivados desde AnexosDigitales sin alterar originales.
- scripts/check_dashboard.py: prueba 3D, 2D, capas, fichas, controles, móvil y fallback.
- vendor/: MapLibre GL JS 6.8.0 y licencia.

## Cómo retomar

1. Leer este archivo y README.md.
2. Revisar git status y la versión pública.
3. Para datos nuevos, volver al informe y al anexo correspondiente; no inferir valores por nombres de archivo.
4. Servir localmente con: python -m http.server 8000 --bind 127.0.0.1.
5. Verificar con: python scripts/check_dashboard.py.
6. Hacer commit y push a main; verificar la URL pública con el mismo script.

## Próximo paso

La Figura 7 sigue teniendo cobertura parcial respecto del informe: faltan geometrías verificadas de 1976, 1986 y 2015. No volver a buscar los once contornos ya incorporados. Mantener la primera pantalla enfocada en el área de estudio.
