# Instrucciones para continuar el dashboard Mocho

> Estado final: los tres capítulos reutilizan el mapa 3D/2D de `map-common.js`. El capítulo 3 añade cinco campañas GPR con paleta Blues común de 0–17 m y una tabla web exacta. La interfaz muestra títulos sin números de figura, no enlaza a GitHub y los mapas comienzan en 3D. Consultar `PROJECT_CONTEXT.md` para las fuentes verificadas; no repetir esas búsquedas.

## 1. Leer el contexto y conservar el trabajo iniciado

1. Trabajar en `C:\Users\pauls\mocho-dashboard`.
2. Leer `PROJECT_CONTEXT.md`, `README.md` y este archivo; ejecutar `git status --short`.
3. Conservar las modificaciones existentes; los capítulos publicados son trabajo validado. No reiniciar ni sobrescribir el repositorio.
4. Los capítulos 1, 2 y 3 están terminados. Continuar solo a partir de una solicitud nueva del usuario.
5. Mantener fondo marfil, verdes apagados, tipografía editorial, firma de Paul Sandoval-Quilodrán y crédito GlacioUACh. Conservar la aplicación estática, sin compilación ni claves API, compatible con GitHub Pages.

## 2. Usar las fuentes ya identificadas

Raíz del proyecto científico: `P:\Projects\Mocho_DGA\2025-2026`.

Informe: `1_DASHBOARD\INFORME FINAL - Mocho 2025-2026_V_final.pdf`, relativo a esa raíz.

| Contenido | Página impresa | Página del PDF, contando desde 1 |
|---|---:|---:|
| Figura 2: balance de masa anual | 5 | 17 |
| Metodología y resultados de variaciones | 17–18 | 29–30 |
| Figura 4: dos series de superficie | 19 | 31 |
| Figura 7: contornos históricos de la capa de hielo | 22 | 34 |
| Discusión sobre nieve y aumento de superficie en 2025 | 23 | 35 |

Ya se inspeccionaron visualmente las Figuras 2, 4 y 7. Las capturas de consulta están en `.cache/figure2-page.png`, `.cache/figure-page-31.png` y `.cache/figure-page-34.png`. No publicarlas como sustituto de las visualizaciones interactivas.

Datos del capítulo 2: `1_DASHBOARD\AnexosDigitales\2_Variaciones_de_glaciares`.

- Libro: `Variaciones de glaciares 2025-2026.xlsx`.
- Hojas: `Gl Mocho` y `Capa de hielo Mocho Choshuenco`.
- Fondo para Figura 7: `1_Imágenes\2026-03-10-00_00_2026-03-10-23_59_Sentinel-2_L1C_False_color.tiff`.
- Capa de hielo 2025: `2_Polígonos\2025\Surface 2025_m.geojson`.
- Capa de hielo 2026: `2_Polígonos\2026\Surface2026.geojson`.
- No confundir esos archivos con `Cuenca_SO_*`, que representan el glaciar Mocho, una parte del complejo.

## 3. Terminar lo pendiente del capítulo 1

### Figura 2

1. Revisar y completar `history.js`, `history.css` y la sección añadida a `index.html`. La primera versión ya está escrita: no hace falta reconstruirla.
2. Usar `data/mass-balance-history.json`: 23 años hidrológicos, de 2003–2004 a 2025–2026, con 18 balances disponibles y 5 ausentes.
3. Mantener las barras de ganancias/pérdidas, consulta por cursor/toque/teclado, selectores desde/hasta, reinicio e incertidumbre opcional, sin tabla ni descarga CSV.
4. Mantener los años ausentes como `null`, nunca cero: 2006–2007, 2007–2008, 2008–2009, 2013–2014 y 2014–2015.
5. Comprobar valores de referencia: −0,88 en 2003–2004; +0,36 en 2004–2005; +0,69 en 2009–2010; −2,67 en 2022–2023; +0,88 en 2024–2025; −3,38 en 2025–2026. Unidad: m eq.a.
6. La Figura 2 debe quedar inmediatamente debajo del mapa, también en móvil. Revisar que su número de figura «02» no se confunda con el capítulo 2.

Fuente exacta activa: `data\bm_hist.xlsx`, hoja `Hoja1`. El script local `scripts/prepare_history_stakes.py` extrae esta serie y las balizas.

### Balizas

1. Revisar `addStakes()` en `app.js` y usar `data/stakes.geojson`.
2. Mostrar las 10 balizas verificadas: B8, B10, B11, B12, B13, B14, B15, B17, B18 y B19. Permitir activar/desactivar la capa y abrir una ficha por clic o teclado.
3. Fuente: `1_DASHBOARD\AnexosDigitales\3_Cinemática_glaciar\3_GPS\Nov2025\Balizas_Mocho20251121.geojson`.
4. Las fechas reales de medición son 22–23/11/2025, tomadas de `Averaging start`; no deducirlas del nombre del archivo. Los derivados usan los campos WGS84 `Longitude`/`Latitude`.
5. Corregir el texto dañado de `index.html`: `10 puntos ? 22?23 NOV 2025` debe decir `10 puntos · 22–23 NOV 2025`.
6. Corregir/verificar el anclaje del marcador: actualmente usa `anchor:'left'` sobre un botón con relleno. El centro del punto visible debe coincidir con la coordenada, no el borde del botón. Comprobarlo en 2D y 3D.
7. Resolver la superposición B15/EMAM-Mocho sin desplazar las coordenadas: B15 tiene prioridad mientras las balizas están visibles; EMAM-Mocho queda accesible al ocultarlas.
8. No presentar alturas elipsoidales GNSS como elevaciones sobre el nivel del mar. El derivado actual las excluye.

## 4. Incorporar el cambio de hoja hacia la derecha

1. Crear dos vistas dentro del mismo sitio, con rutas por hash: `#capitulo-1` y `#capitulo-2`. Sin hash, abrir el capítulo 1.
2. En el encabezado, mostrar el título del capítulo activo y un control claro: `01 Área de estudio` / `02 Variaciones de glaciares`.
3. Añadir al capítulo 1 un botón visible **«Variaciones de glaciares →»**. Al pulsarlo, entrar en la hoja siguiente, situada conceptualmente a la derecha.
4. En el capítulo 2, incluir **«← Área de estudio»** para volver. Usar una transición horizontal breve; desactivarla con `prefers-reduced-motion`.
5. Mostrar únicamente el capítulo activo; el oculto no debe recibir foco ni generar desbordamiento horizontal. No poner el capítulo 2 simplemente al final del desplazamiento vertical del capítulo 1.
6. Mantener desplazamiento vertical dentro de cada hoja. No capturar gestos ni flechas globales que interfieran con arrastrar mapas, desplazar gráficos o editar selectores. Los botones deben funcionar también en móvil.
7. Responder a cambios de hash y a Atrás/Adelante del navegador. Actualizar el título visible y llevar el foco al encabezado del capítulo abierto.
8. Crear el mapa del capítulo 2 al abrirlo por primera vez; reutilizarlo al volver. Llamar a `map.resize()` cuando su contenedor vuelva a ser visible y termine la transición.
9. Evitar IDs duplicados entre capítulos y conservar la selección/cámara de cada mapa durante los cambios de hoja.

## 5. Preparar los datos del capítulo 2

1. Crear `scripts/prepare_variations.py` que lea los originales sin modificarlos y genere derivados mínimos en `data/`.
2. Extraer las dos hojas del Excel con valores calculados (`data_only=True`). Ignorar filas vacías; conservar año, área, error, perímetro y tasa anual cuando existan.
3. Generar `data/glacier-variations.json`, separando explícitamente las series `glacier` y `icecap`; incluir unidades y procedencia por serie.
4. La hoja `Gl Mocho` tiene 17 observaciones: 1976, 1986, 2000, 2007, 2011, 2013, 2014, 2015, 2016, 2019, 2020, 2021, 2022, 2023, 2024, 2025 y 2026.
5. La hoja de capa de hielo tiene 12 observaciones: 1976, 1986, 2000, 2005, 2015, 2017, 2020, 2022, 2023, 2024, 2025 y 2026.
6. Conservar la precisión de los números del Excel y redondear únicamente al mostrarlos. Usar `Error (km²)` para la incertidumbre; no calcularla de nuevo a partir del mapa web.
7. Comprobar las tasas existentes. Si es necesario derivarlas, usar `(área actual − área anterior)/(año actual − año anterior)`; no asumir intervalos de un año.
8. No cambiar el año 1986 de las series a partir de la hoja de imágenes: esta última contiene una fecha de 1987. Conservar el año de la serie y documentar la discrepancia si se muestran las fechas de adquisición.
9. Reutilizar el procedimiento de `scripts/prepare_data.py` para generar un WebP georreferenciado de la imagen de 2026 y geometrías WGS84. Verificar el CRS real antes de transformar.

### Contornos históricos verificados

1. La Figura 7 contiene los mismos 12 años de la serie de capa de hielo: 1976, 1986, 2000, 2005, 2015, 2017, 2020, 2022, 2023, 2024, 2025 y 2026.
2. Los contornos de 1976 (`Surface1976_v2024.shp`), 1986 (`Surface_1986.shp`) y 2015 (`Mocho 20150411.shp`) están en `AnexosDigitales\2_Variaciones_de_glaciares\2_Polígonos` y corresponden a la capa de hielo completa.
3. Conservar las rutas exactas en `HISTORICAL`, la procedencia y el CRS de cada geometría. No sustituir las superficies publicadas por el área calculada del mapa.
4. No volver a buscar estos contornos ni reconstruir geometrías desde imágenes del informe.

## 6. Construir la Figura 7 interactiva

1. Encabezar el capítulo con **«02 · Variaciones de glaciares»** y una introducción breve a los cambios de superficie entre 1976 y 2026.
2. Colocar primero el mapa de la Figura 7, dominante y encuadrado sobre toda la capa de hielo Mocho–Choshuenco.
3. Usar MapLibre ya incluido en `vendor/`, fondo Sentinel-2 del **10/03/2026**, vista 2D inicial, zoom, reinicio y pantalla completa. No añadir una segunda dependencia cartográfica.
4. Mostrar líneas de contorno por año, con color y etiqueta identificables. Selección inicial: 1976 y 2026 si ambos están disponibles; si falta 1976, 2025 y 2026 con una nota de cobertura parcial.
5. Añadir lista de años con casillas independientes, «Mostrar todos» y «Restablecer comparación». Los años sin geometría deben figurar deshabilitados y explicados.
6. Al seleccionar un contorno, mostrar año, superficie e incertidumbre del Excel, fuente y unidad km². Si coinciden varias líneas bajo el cursor, permitir escoger el año en la ficha.
7. Mantener siempre visible la fecha del fondo: cambiar los contornos no cambia la imagen satelital. Ofrecer una leyenda clara y suficiente contraste entre años.
8. Añadir esta nota metodológica, en lenguaje breve: el aumento de superficie de 2025 está asociado a campos de nieve persistente incluidos en la delimitación; no debe interpretarse automáticamente como avance neto del hielo. Referencia: discusión del informe, p. 23.

## 7. Construir la Figura 4 interactiva debajo del mapa

1. Reproducir sus dos paneles: **a) Glaciar Mocho** y **b) Capa de hielo Mocho–Choshuenco**, ambos con área en km² frente a año.
2. Usar líneas, puntos y banda de incertidumbre, conservando los años de observación de cada serie. El eje horizontal debe ser temporal: respetar las distancias entre años.
3. Mantener ejes verticales propios para cada panel; no combinar las dos superficies en una única serie ni normalizarlas por defecto.
4. Permitir consulta con cursor, toque y teclado. Mostrar año, área ± error y tasa del intervalo precedente, cuando exista.
5. Añadir selección de intervalo compartida, activar/desactivar incertidumbre y restablecer, sin tabla ni descarga CSV. Reutilizar patrones de `history.js`, con un módulo separado para estas series.
6. Consultar solo observaciones reales. Las líneas unen observaciones, pero no crean mediciones anuales intermedias. No rellenar los años que faltan con ceros.
7. En el panel de capa de hielo, ofrecer «Ver contorno en el mapa» para el año consultado, habilitado únicamente si existe su geometría. Esta acción activa el contorno y desplaza la vista al mapa; no oculta otras comparaciones seleccionadas.
8. Conservar la trazabilidad en los derivados y la documentación, sin mostrar un bloque desplegable de fuentes en la interfaz. No confundir unidades de superficie (km²) con las de balance de masa del capítulo 1 (m eq.a.).

### Valores de control del capítulo 2

| Serie | 1976 | 2025 | 2026 |
|---|---:|---:|---:|
| Glaciar Mocho, km² | 6,22 ± 0,57 | 4,94 ± 0,09 | 4,91 ± 0,09 |
| Capa de hielo, km² | 28,175 ± 3,48 | 13,07 ± 0,57 | 12,12 ± 0,43 |

Entre 1976 y 2026, el cambio relativo es aproximadamente −21 % para Mocho y −57 % para la capa de hielo. Entre 2025 y 2026, las diferencias son −0,03 y −0,95 km², respectivamente. Usar los números originales para calcular, no los valores redondeados de esta tabla.

## 8. Verificar antes de dar el trabajo por terminado

1. Servir el sitio: `python -m http.server 8000 --bind 127.0.0.1`. Comprobar antes si el puerto ya está ocupado: podría seguir activo el servidor de la sesión anterior.
2. Ejecutar `scripts/check_dashboard.py`, que usa Playwright/Edge y cubre los tres capítulos.
3. Comprobar capítulo 1: mapa 3D/2D, capas, cuatro estaciones, dos cumbres, diez balizas, fichas, prioridad B15/EMAM-Mocho, gráfico, filtros, teclado e incertidumbre, sin tabla ni CSV en la Figura 2.
4. Comprobar navegación: siguiente/anterior, URL directa a los capítulos 2 y 3, recarga, Atrás/Adelante, foco y regreso a cada mapa sin quedar en blanco.
5. Comprobar la serie histórica: 17 y 12 observaciones, extremos documentados, banda de incertidumbre, años irregulares, rangos vacíos y selección de un solo año sin errores.
6. Comprobar Figura 7: los 12 controles activan su año, las fuentes y fechas son correctas, y funcionan la leyenda, la consulta de contornos y el enlace desde el gráfico.
7. Comprobar capítulo 3: cinco campañas exclusivas, escala Blues 0–17 m, tabla de cinco filas, relieve 3D/2D y fallos aislados de manifiesto o raster.
8. Probar escritorio de 1440 px y móvil de 390 px; comprobar capturas y ausencia de desbordamiento horizontal global. El desplazamiento horizontal dentro de un gráfico o tabla sí es aceptable.
9. Probar fallos de carga de JSON, imágenes y relieve externo. Un fallo en un capítulo no debe impedir abrir los demás.
10. Usar la habilidad de navegador si está disponible; el proyecto dispone de su comprobador local como alternativa.
11. Actualizar `README.md` y `PROJECT_CONTEXT.md`, revisar `git diff`, publicar un único commit en `main` y verificar `https://sqpaul.github.io/mocho-dashboard/`.

## 9. Evitar trabajo innecesario y problemas del entorno

- No añadir frameworks, servicios, autenticación ni un backend. Usar SVG/JavaScript para los gráficos y MapLibre existente para el mapa.
- No volver a buscar los datos de Figura 2: sus fuentes y derivados ya están identificados.
- Para leer Excel está verificado `C:\Users\pauls\anaconda3\python.exe`, que incluye `openpyxl`. El entorno `geopy` no incluía `openpyxl` durante esta sesión.
- PyMuPDF se instaló en `.cache/pdf-deps` para el Python de `geopy`, pero su lectura requirió permisos fuera del sandbox. Preferir las capturas ya disponibles cuando basten para comprobar la composición de las figuras.
- No buscar directamente texto dentro de todas las salidas de notebooks: contienen imágenes codificadas y producen volúmenes enormes. Si es necesario, leer únicamente `source` de las celdas de código.
- Publicar solo derivados necesarios. Excluir PDF completo, ZIP de anexos, registros GNSS crudos, caché y capturas de prueba.
- No ejecutar agentes adicionales salvo que el usuario lo pida. Completar por etapas y dar actualizaciones breves.

## Mensaje para entregar al siguiente modelo

> Lee `CONTINUAR_DASHBOARD.md`, `PROJECT_CONTEXT.md` y `README.md`. Los capítulos 1, 2 y 3 están completos; conserva las implementaciones y fuentes verificadas. Continúa únicamente desde una nueva solicitud del usuario, prueba el resultado y publica solo derivados web necesarios.
