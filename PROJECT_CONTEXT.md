# Contexto de continuidad — Mocho Dashboard

Este documento permite retomar el trabajo sin reconstruir decisiones ni volver a explorar todos los anexos.

## Objetivo

Crear un dashboard público de despedida del proyecto de monitoreo del glaciar Mocho: una pieza profesional, visualmente memorable y útil para el equipo. Se desarrolla por capítulos a partir del informe final y sus anexos digitales. La primera entrega corresponde a **1.1 Área de estudio**.

## Estado actual

- Repositorio: https://github.com/SQPaul/mocho-dashboard
- Sitio público: https://sqpaul.github.io/mocho-dashboard/
- Rama publicada: main, raíz del repositorio mediante GitHub Pages.
- Primera vista terminada: mapa 3D/2D, imagen Sentinel-2 y delimitaciones 2026, cuatro estaciones meteorológicas, cumbres Mocho/Choshuenco, métricas, fuentes y diseño móvil.
- Capítulos 1 a 5 terminados: navegación horizontal mediante `#capitulo-1` a `#capitulo-5`; balance de masa, dos paneles históricos de superficie, 12 delimitaciones de la capa de hielo, cinco campañas GPR, cinemática glaciar y un álbum vertical de siete fotografías. La interfaz omite números de figura y descargas.
- Contornos disponibles: 1976, 1986, 2000, 2005, 2015, 2017, 2020, 2022, 2023, 2024, 2025 y 2026. La cobertura de la Figura 7 está completa.
- Balizas del capítulo 1: diez puntos nativos de MapLibre sobre el relieve, sin desplazamientos de marcadores HTML; la ficha consultable muestra solo nombre y coordenadas WGS84. B15 y EMAM-Mocho comparten coordenada, con prioridad para la baliza.
- Autoría visible: **Diseño y desarrollo — Paul Sandoval-Quilodrán**; debajo, **Desarrollo del informe — GlacioUACh**.
- Tono: herramienta científica elegante con firma discreta; no incluir una despedida explícita.

## Fuentes de trabajo

- Carpeta original: P:\Projects\Mocho_DGA\2025-2026\1_DASHBOARD
- Informe base: INFORME FINAL - Mocho 2025-2026_V_final.pdf
- Datos: AnexosDigitales
- Sección usada: 1.1 Área de estudio, páginas impresas 3–4; estaciones y cumbres desde los insumos locales de `data/geometrias`; EMAM-Mocho desde B15 del anexo 3.
- Capítulo 2: Figura 4, p. 19, Figura 7, p. 22 y Anexo 2, «Variaciones de glaciares 2025–2026».
- Capítulo 3: `data/GPR/GPR_DDMMYYYY.tif`, campañas del 08/10/2021 al 19/10/2025; tabla transcrita de `Tabla_resumen_GPR.png` sin recalcular sus valores.
- Capítulo 4: `data/Velocidad/Vel_GPS202510-202604.tif` y `data/Velocidad/Vel anual balizas_Mocho2025-2026.geojson`; raster OCT 2025–ABR 2026 y diez velocidades anuales, con B11 procedente de 2024–2025.
- Capítulo 5: siete fotografías numeradas en `data/album/`, publicadas en el mismo orden y sin títulos ni pies de foto.
- Imagen web: Sentinel-2 falso color del 10/03/2026. Geometrías 2026 reproyectadas desde UTM 18S a WGS84.
- Superficie y perímetro: Anexo 2, Figura 4 (2026). Elevaciones: DEM Pléiades 2020.
- Mapterhorn aporta el relieve visual y no reemplaza los DEM científicos.

## Decisiones

- Conservar el diseño actual: fondo marfil, verdes apagados, mapa dominante, tipografía editorial y controles discretos.
- Mantener el sitio estático, sin claves API ni compilación, compatible con GitHub Pages.
- No publicar el ZIP, el PDF completo ni registros GNSS crudos; publicar solo derivados necesarios.
- No inventar ni desplazar coordenadas. AWS Mocho1, AWS Mocho2 y AWS DGA usan el GeoPackage verificado; EMAM-Mocho usa exactamente la posición de B15.
- Nota histórica: mediciones desde 2003, monitoreo intensivo desde 2020, pérdida de masa predominante y balances positivos en 2004–2005, 2009–2010 y 2024–2025.
- Cada capítulo nuevo debe mostrar fecha, unidad, fuente y advertencias metodológicas cuando corresponda.

## Arquitectura

- index.html, style.css, additions.css y app.js: aplicación estática.
- map-common.js: motor 3D, imagen georreferenciada y controles compartidos por los cuatro capítulos cartográficos. variations.js / variations.css: mapa histórico, gráfico y navegación; history.js / history.css: balance de masa; snow.js / snow.css: campañas GPR y tabla; velocity.js / velocity.css: raster rainbow y balizas de cinemática; album.js / album.css: álbum vertical y foco continuo por scroll.
- scripts/prepare_variations.py: regenera series, contornos y fondo 2026 desde el archivo local. Respeta CRS 32718/32719, omite geometrías nulas y conserva las superficies publicadas independientemente del área geométrica.
- Fuentes históricas: `P:\Projects\Mocho_DGA\SIG\Delimitacion_glaciar` (2000–2022), `2023-2024\GIS\Delimitacion` (2023–2024) y anexo 2 de `2025-2026\1_DASHBOARD` (1976, 1986, 2015, 2025 y 2026). Rutas exactas en `HISTORICAL` del generador y propiedades de cada contorno.
- data/study-area.json, data/mass-balance-history.json, data/stakes.geojson, data/glacier-variations.json, data/icecap-history.geojson, data/gpr-campaigns.json, cinco `gpr-YYYY.webp`, derivados de velocidad, data/album.json, siete `album-NN.webp` y data/satellite-2026.webp: derivados web activos. La serie de balance llega a 2025–2026; `satellite-2025.webp` se conserva como antecedente.
- scripts/prepare_data.py: regenera derivados desde AnexosDigitales sin alterar originales.
- scripts/prepare_gpr.py: aplica Blues con escala fija 0–17 m, preserva NoData como transparencia, transforma las cuatro esquinas de cada GeoTIFF a WGS84 y muestrea el espesor en las diez balizas.
- scripts/prepare_velocity.py: aplica rainbow con escala fija 0–30 m/a, preserva NoData como transparencia y transforma el raster y las diez balizas desde EPSG:32718 a WGS84. Publica B11 como una única baliza con período 2024–2025.
- scripts/prepare_album.py: ordena las fotos por nombre numérico, corrige orientación EXIF y publica WebP de hasta 2000 px de ancho junto a un manifiesto mínimo.
- scripts/check_dashboard.py: prueba los cinco capítulos, 3D, 2D, capas, fichas, controles, foco del álbum, móvil y fallback.
- vendor/: MapLibre GL JS 6.8.0 y licencia.

## Cómo retomar

1. Leer este archivo y README.md.
2. Revisar git status y la versión pública.
3. Para datos nuevos, volver al informe y al anexo correspondiente; no inferir valores por nombres de archivo.
4. Servir localmente con: python -m http.server 8000 --bind 127.0.0.1.
5. Verificar con: python scripts/check_dashboard.py.
6. Hacer commit y push a main; verificar la URL pública con el mismo script.

## Próximo paso

No quedan tareas pendientes en los capítulos 1 a 5. Para futuras ampliaciones, mantener la primera pantalla enfocada en el área de estudio y conservar la trazabilidad de cada derivado al regenerar los datos.
