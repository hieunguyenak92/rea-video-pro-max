# REA-Video-Pro-Max

## Descifra la edición. Crea algo nuevo con su estilo.

**Convierte un vídeo de referencia en una línea de tiempo con evidencias y una plantilla de estilo reutilizable. Añade otro guion y otros medios para renderizar tu propio vídeo.**

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

[Demostración grabada](docs/index.html) · [Vídeo A](docs/media/reference.mp4) · [Vídeo B](docs/media/adapted.mp4) · [Verificación (English)](docs/VALIDATION.md)

Una buena edición reúne decisiones sobre cortes, grupos de palabras, énfasis, movimiento y sonido. REA-Video-Pro-Max permite inspeccionar y reutilizar las partes compatibles de ese sistema.

```text
Vídeo A → análisis + línea de tiempo inferida → plantilla + contenido nuevo → proyecto editable → vídeo B
```

La demostración usa medios sintéticos propios. A y B tienen texto y medios distintos. La web estática muestra un resultado grabado; no ejecuta inferencia en directo ni sube vídeos de visitantes.

## Qué puedes pedir

- Desglosar el vídeo completo en planos, subtítulos, estilo, movimiento, señales de audio y línea de tiempo con evidencias temporales.
- Analizar tipografía, composición y colores de un fotograma. Una imagen aislada no establece tiempos de animación ni sonido.
- Aplicar el estilo extraído a un guion, imágenes o metraje nuevos para crear un vídeo diferente.
- Entregar solo la línea de tiempo y los archivos de análisis cuando ese sea el trabajo solicitado.

```text
Usa REA-Video-Pro-Max para analizar la línea de tiempo y el estilo de reference.mp4. Con mi nuevo guion y mis recursos, crea otro vídeo con subtítulos, movimiento y ritmo similares. Entrega la plantilla, el proyecto, el vídeo y las limitaciones pendientes.
```

## Primer resultado

Necesitas Python 3.11+, FFmpeg y FFprobe. El entorno Python usa Pillow, NumPy y PyAV. Tesseract es opcional para OCR; los datos de idioma instalados determinan qué idiomas pueden ejecutarse. Consulta el [alcance comprobado (English)](docs/SUPPORT-MATRIX.md).

macOS es la plataforma de desarrollo medida. Linux es un destino previsto de CI; el renderizador nativo en Windows no está certificado. La verificación de creación exige el recibo exacto del render y OCR independiente, por lo que el flujo completo necesita Tesseract con datos `eng`.

```sh
python -m venv .venv
# macOS / Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e .
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py doctor
```

```sh
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py analyze examples/reference.mp4 --out ./work/analysis --ocr auto --ocr-lang eng
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py template ./work/analysis/analysis.json --out ./work/style-template.json
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py compose ./work/style-template.json --content examples/content.json --out ./work/project
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py render ./work/project/project.json --out ./work/video-b.mp4
python skills/rea-video-pro-max/scripts/rea-video-pro-max.py verify ./work/project/project.json --mode style-transfer --render ./work/video-b.mp4 --ocr-lang eng
```

Los comandos usan la estructura del checkout Git. En el paquete de skill extraído, la entrada es `scripts/rea-video-pro-max.py`; conserva juntas las carpetas `lib`, `assets` y `references`. Usa el intérprete donde instalaste las dependencias; no copies únicamente el script.

## Usa tu propio contenido

`examples/content.json` es un ejemplo sintético de content binding: cada escena nueva tiene `id`, `text`, `duration`, `background`, `accent` y un `asset` opcional. `width`, `height` y `fps` definen la salida; `audio` y `font` son opcionales. Las rutas se resuelven respecto al archivo de bindings. El proyecto copia los recursos y registra sus hashes, sin sustituirlos silenciosamente por el metraje o la música de A. Las palabras nuevas necesitan tiempos nuevos; el método de estimación se declara cuando no hay alineación exacta.

El audio del vídeo de cada escena se silencia; proporciona un enlace `audio` nuevo para tener sonido. Los clips cortos mantienen su último fotograma. El renderizador nativo exige material orientado correctamente y con píxeles cuadrados. CSV solo exporta filas de planos. Revisa los límites de composición y agrupación para escrituras complejas o bidireccionales.

## Usar con Claude Code / Codex

Copia la carpeta completa `skills/rea-video-pro-max` al directorio de skills del host o pide a tu agente que la instale desde el checkout. Las ubicaciones locales habituales son `.claude/skills/rea-video-pro-max` y `.agents/skills/rea-video-pro-max`. Instalar la skill no instala FFmpeg, idiomas OCR ni pesos de modelos. La cuenta, los permisos y la política de datos del host son independientes. La [skill](skills/rea-video-pro-max/SKILL.md) y las referencias técnicas están en English.

## Archivos y exportación

- JSON nativo conserva análisis, línea de tiempo, datos de subtítulos/estilo/movimiento/audio, plantillas y proyectos. CSV sirve para revisar datos editoriales.
- SRT/WebVTT/ASS exportan texto y tiempos según cada formato. SRT no conserva toda la tipografía ni el movimiento.
- Usa solo los adaptadores de línea de tiempo que la versión instalada declare disponibles. El recibo indica el subconjunto, las aproximaciones y las pérdidas; no garantiza todos los efectos en cualquier editor.
- El renderizador por software compone el contenido nuevo y lo codifica con FFmpeg. No necesita los filtros opcionales `drawtext`, `ass` o `subtitles`.

## Límites importantes

Los metadatos medidos, el OCR, los ajustes de estilo y las hipótesis de edición son evidencias distintas. Un vídeo aplanado no determina de forma única los clips originales, capas ocultas, fuente, plugin, proyecto del editor o prompt de IA. El alcance inicial se centra en tiempos, subtítulos y primitivas 2D compatibles. No es un descompilador universal ni un líder de mercado demostrado. Oclusión compleja, reconstrucción 3D, máster HDR y recorridos NLE arbitrarios quedan fuera del alcance comprobado. Las escrituras complejas requieren shaping y pruebas propias; nueve traducciones no certifican nueve idiomas OCR o de renderizado.

El vídeo B se comprueba con su contenido nuevo, contrato de estilo y reproducción; no por identidad de píxeles de toda la imagen con A. La comprobación técnica y el juicio creativo humano son distintos. [Evidencia y límites (English)](docs/VALIDATION.md).

## Procesamiento local y créditos

El núcleo se ejecuta localmente, sin exigir una API de pago, subir vídeos a inferencia alojada ni publicar medios. Instalar dependencias o usar un proveedor opcional puede generar tráfico de red. El host Claude/Codex tiene sus propias políticas. [Privacy (English)](docs/PRIVACY.md). Inspirado en JuneYaooo/rea-video; es un producto independiente, no una actualización oficial. Se aplican por separado las licencias de código, fuentes, medios, códecs y modelos.

Los informes locales copian por defecto el medio de referencia y las evidencias. `report --no-media` omite solo la copia completa del medio; conserva texto OCR, rutas locales y recortes. Revísalos antes de compartir.

[Soporte (English)](SUPPORT.md) · [Mantenimiento (English)](docs/MAINTENANCE.md) · No se afirma una revisión profesional de las traducciones por hablantes nativos.

[Voz local y movimiento avanzado (referencia técnica en inglés)](skills/rea-video-pro-max/references/speech-and-motion.md).
