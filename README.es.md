# REA-Video-Pro-Max

## Dale a Claude y Codex la mirada de un editor.

**Desglosa el ritmo, los subtítulos y el movimiento de un vídeo de referencia. Convierte esas decisiones en un estilo reutilizable. Renderiza un vídeo nuevo con tus propias palabras y recursos.**

Los grandes montajes tienen su propio lenguaje. Hazlo parte de tu caja de herramientas creativa.

[**▶ Explora la demo en vivo**](https://hieunguyenak92.github.io/rea-video-pro-max/) · [**Descarga el skill**](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip) · [Versión v0.1.1](https://github.com/hieunguyenak92/rea-video-pro-max/releases/tag/v0.1.1)

[English](README.md) · [Tiếng Việt](README.vi.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [Español](README.es.md) · [Português](README.pt-BR.md) · [简体中文](README.zh-CN.md) · [ไทย](README.th.md) · [Français](README.fr.md)

**Skill para Claude Code / Codex · CLI + MCP opcional · Procesamiento local · Apache-2.0**

---

## De «Me encanta este montaje» a «Esta es mi versión».

Encuentras un vídeo con la energía que buscas: el ritmo de sus cortes, la forma en que aparecen los subtítulos, un resaltado que recorre cada frase, un zoom que da impulso a una imagen fija.

REA-Video-Pro-Max convierte los elementos compatibles de ese estilo en algo que puedes examinar, ajustar y reutilizar. Aporta un guion, imágenes, clips o narración nuevos. Al terminar, tendrás un proyecto editable y un vídeo realmente renderizado.

| Referencia A | Tu nuevo vídeo B |
| :---: | :---: |
| [![Fotograma del vídeo de referencia propio](docs/media/readme-reference.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) | [![Fotograma renderizado con texto nuevo y recursos independientes](docs/media/readme-new-video.png)](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) |
| Estudia el ritmo de los planos y el tratamiento de los subtítulos. | Aplica el estilo reutilizable a otra historia. |

*Fotogramas reales de la demo propia incluida. B utiliza texto nuevo, recursos generados de forma independiente y una nueva temporización de subtítulos. El [recorrido interactivo](https://hieunguyenak92.github.io/rea-video-pro-max/#workspace) permite recorrer ambos vídeos y examinar la línea de tiempo registrada, la plantilla, el proyecto y la verificación.*

```text
Reference video → editing evidence + timeline → reusable style
                                                   + your new content
                                                   → editable project + Video B
```

## Pon una referencia a trabajar

| Lo que quieres hacer | Lo que te llevas |
| --- | --- |
| Entender por qué un montaje transmite lo que transmite | Intervalos de planos, texto visible, apariencia de subtítulos, movimiento aparente y señales de audio, vinculados a marcas de tiempo y evidencias. |
| Llevar un tratamiento de subtítulos a otra historia | Tipografía, composición y paletas de resaltado reutilizables, aplicadas a las palabras nuevas con su propia temporización. |
| Crear un formato de vídeo repetible | Una plantilla de estilo que puedes vincular a otro guion y otro conjunto de recursos. |
| Dirigir el resultado | Una línea de tiempo/proyecto nativo en JSON con recursos copiados y hashes, que puedes examinar, modificar y volver a renderizar. |
| Integrar el análisis en tu propio flujo | Archivos estructurados, un inspector sin conexión, exportaciones de subtítulos e intercambio de líneas de tiempo con límites definidos. |

Úsalo para presentar un producto, crear un clip educativo, desarrollar una serie de creador, estudiar un montaje o construir una herramienta de vídeo a medida. Si solo necesitas el desglose, el análisis y la línea de tiempo son entregables completos por sí mismos.

## Un prompt para iniciar el flujo

Instala el skill incluido, entrega a tu agente la referencia y tu contenido nuevo, y pídele lo siguiente. Este prompt en inglés está listo para usar:

```text
Use REA-Video-Pro-Max to break down reference.mp4: shot rhythm,
subtitle layout, highlight colors and supported motion.
Extract a reusable style, then use my new script and assets to make
an original video with a similar editing language.
Render the video, keep the editable project, verify the new content,
and show me any effects that need an approximation.
```

Tú diriges la historia. El skill aporta al agente un flujo concreto y herramientas ejecutables para analizar, componer, renderizar y verificar.

## Lo que hace útil este flujo

- **Un montaje que puedes examinar.** Las marcas de tiempo de presentación decodificadas, las evidencias por fotograma y la cobertura hacen trazable la línea de tiempo. Las señales medidas, los resultados de modelos y las decisiones de edición inferidas conservan sus propias etiquetas.
- **Detalles de subtítulos que llegan al proyecto.** Estima el tamaño visible, la posición, el relleno y el contorno; conserva las distintas paletas de resaltado y variantes de estilo observadas. Redistribuye y vuelve a temporizar las palabras nuevas durante la composición.
- **Movimiento que conserva su dirección.** Ajusta modelos acotados de movimiento de similitud/afín y curvas temporales candidatas. El renderizador nativo puede reutilizar el componente de zoom compatible con su signo, incluido el alejamiento.
- **Un proyecto sobre el que seguir creando.** Las imágenes, clips, fuentes y audio opcional nuevos se copian en un proyecto portátil. Las vinculaciones explícitas y los hashes permiten examinar el contenido elegido.
- **Voz cuando el trabajo la necesita.** El ASR local opcional con faster-whisper proporciona intervalos de palabras derivados del modelo. Una correspondencia estricta entre guion y audio puede vincularlos al contenido nuevo; se requiere un modelo local indicado explícitamente.
- **Un resultado que puedes comprobar.** Verifica la correspondencia entre proyecto y salida, decodifica el vídeo renderizado y comprueba el contenido de los subtítulos mediante OCR independiente. Guarda las evidencias junto al resultado.

El renderizador nativo admite **subtítulos estáticos / con fundido / pop / deslizamiento**, **transiciones de corte / disolución / fundido / barrido** y **fondos estáticos / con panzoom de dirección definida**. El análisis puede conservar observaciones de movimiento más ricas de las que el renderizador nativo puede reproducir. [Compatibilidad exacta (inglés)](docs/SUPPORT-MATRIX.md).

## Consigue tu primer resultado

### 1. Prepara el entorno de ejecución

Necesitas **Python 3.11+**, **FFmpeg + FFprobe** y una compilación de FFmpeg con **libx264**. Instala **Tesseract con los datos de idioma `eng`** para ejecutar el ejemplo incluido de OCR y verificación de subtítulos. Las dependencias de Python se instalan a continuación.

```sh
git clone https://github.com/hieunguyenak92/rea-video-pro-max.git
cd rea-video-pro-max
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e .
rea-video-pro-max doctor
```

Estos comandos de shell están pensados para macOS/Linux. El CI de la versión pasó en Linux y macOS; el renderizado nativo en Windows no está certificado. `doctor` informa de las herramientas realmente disponibles en tu equipo.

### 2. Dale el skill a tu agente

Copia la carpeta **completa** `skills/rea-video-pro-max` al directorio de skills de tu proyecto:

| Entorno | Destino dentro del proyecto |
| --- | --- |
| Claude Code | `.claude/skills/rea-video-pro-max` |
| Codex | `.agents/skills/rea-video-pro-max` |

También puedes extraer ahí el [ZIP del skill](https://github.com/hieunguyenak92/rea-video-pro-max/releases/download/v0.1.1/rea-video-pro-max-v0.1.1-skill.zip). Mantén juntos `lib`, `assets`, `scripts` y `references`. Para una instalación solo desde el ZIP, instala sus dependencias de Python con `python -m pip install -r /path/to/rea-video-pro-max/requirements.txt`; el punto de entrada es `python /path/to/rea-video-pro-max/scripts/rea-video-pro-max.py`. Los comandos de consola que siguen proceden de la instalación del repositorio anterior. Tu agente debe usar el intérprete que contiene esas dependencias.

### 3. Ejecuta el ejemplo A → B incluido

```sh
rea-video-pro-max analyze examples/reference.mp4 --out work/analysis --ocr required --ocr-lang eng
rea-video-pro-max template work/analysis/analysis.json --out work/style-template.json
rea-video-pro-max compose work/style-template.json --content examples/content.json --out work/project
rea-video-pro-max render work/project/project.json --out work/video-b.mp4
rea-video-pro-max verify work/project/project.json --mode style-transfer --render work/video-b.mp4 --ocr-lang eng
```

Abre `work/video-b.mp4`. El proyecto portátil está en `work/project/`; el análisis de la referencia está en `work/analysis/`. Usa un directorio de salida nuevo para cada composición. Para generar un inspector de análisis sin conexión, ejecuta:

```sh
rea-video-pro-max report work/analysis/analysis.json --out work/report
```

Después abre `work/report/timeline.html` localmente. La [CLI, el skill y el MCP opcional comparten el mismo núcleo (inglés)](skills/rea-video-pro-max/references/runtime-and-support.md).

<details>
<summary><strong>Hazlo tuyo: ¿qué contiene una vinculación de contenido?</strong></summary>

Una vinculación de contenido es un archivo JSON que define tus nuevas escenas, texto, recursos y audio/fuente opcionales. Tu agente puede crearlo a partir de un brief normal. Empieza con [examples/content.json](examples/content.json).

```json
{
  "schema_version": 1,
  "kind": "rea-video-content",
  "width": 640,
  "height": 360,
  "fps": 24,
  "scenes": [
    {
      "id": "intro",
      "text": "Your next story starts here",
      "duration": 3.0,
      "background": [18, 24, 38],
      "accent": [108, 240, 190]
    }
  ]
}
```

Añade una ruta `asset` para una imagen o un vídeo, y `audio` para una banda sonora o narración explícita. Las rutas de los recursos se resuelven respecto a este archivo JSON. El renderizador usa el contenido nuevo elegido; reutilizar los recursos exactos de la referencia requiere una aceptación explícita.

Las palabras nuevas reciben una temporización nueva. La distribución ponderada por caracteres es una estimación. Proporciona intervalos de palabras nuevos o usa ASR local con correspondencia estricta cuando la sincronización con la voz sea importante. [Guía de voz y movimiento (inglés)](skills/rea-video-pro-max/references/speech-and-motion.md).

</details>

## Mira el trabajo detrás de la promesa

**v0.1.1 superó 176 pruebas locales**, incluido el caso real de ASR local opcional. [El CI alojado superó tres trabajos de Linux/macOS](https://github.com/hieunguyenak92/rea-video-pro-max/actions/runs/43324016397). Los seis artefactos publicados de la versión se descargaron y se compararon con los bytes y sumas de comprobación locales.

Las evidencias incluyen una reproducción completa propia de **A → análisis → estilo → B nuevo**, una tarea independiente en vietnamita con tipografía/contorno corregidos y dos tratamientos de resaltado, y una tarea de movimiento que conserva la dirección de acercamiento/alejamiento. Son casos propios acotados: demuestran el flujo presentado, sin establecer una precisión general para todos los géneros o idiomas.

[Examinar el análisis](docs/evidence/reference-analysis.json) · [Leer la plantilla](docs/evidence/style-template.json) · [Abrir el proyecto](docs/evidence/project.json) · [Revisar la verificación](docs/evidence/verification.json) · [Detalles de validación (inglés)](docs/VALIDATION.md)

## Conserva el resultado. Amplía el sistema.

| Formato | Qué contiene |
| --- | --- |
| JSON nativo | Análisis, líneas de tiempo, datos de subtítulos/estilo/movimiento/audio, plantillas y proyectos nativos editables. |
| CSV | Filas de planos para inspección y procesamiento posterior. |
| SRT / WebVTT | Texto visible e intervalos de los subtítulos. |
| ASS | Temporización de subtítulos con un estilo sustituto explícito; la apariencia observada y la incertidumbre permanecen en las evidencias nativas. |
| OTIO / EDL | Segmentos opcionales de la referencia en OTIO con anotaciones; EDL para cortes medidos con CFR entero. Los informes de exportación describen las pérdidas. |
| MP4 + HTML sin conexión | El vídeo nuevo y un informe de análisis local que puedes examinar. |

El proyecto nativo es JSON editable. Esta versión no exporta proyectos nativos de Premiere, Resolve, After Effects o CapCut, ni FCPXML. La importación de los archivos de intercambio compatibles en editores externos sigue sin verificarse. [Límites de exportadores y renderizador (inglés)](docs/SUPPORT-MATRIX.md).

## Conoce los límites creativos

La versión actual se centra en evidencias de edición observables y en la reutilización de estilos **2D** compatibles. Las fuentes originales exactas, capas ocultas, plugins, recursos de origen e historial del proyecto pueden seguir siendo desconocidos. El OCR y los ajustes de movimiento pueden equivocarse; la cobertura muestreada y la incertidumbre permanecen visibles.

Los clips vinculados deben estar orientados correctamente y tener píxeles cuadrados. Su audio de escena se silencia; proporciona el audio explícitamente. Las escrituras complejas necesitan fuentes y conformación tipográfica adecuadas; se rechazan los subtítulos bidireccionales. Las nueve traducciones del README describen el producto y no certifican nueve idiomas de OCR/renderizado. La valoración del estilo creativo y del sonido sigue requiriendo revisión humana. [Matriz completa de compatibilidad (inglés)](docs/SUPPORT-MATRIX.md).

El procesamiento principal se ejecuta localmente y no requiere una API de modelos de pago ni subir contenido. Las dependencias y la preparación de modelos opcionales pueden necesitar acceso a la red; el entorno Claude/Codex tiene sus propias políticas de datos. Los informes locales incluyen los recursos de referencia y recortes de forma predeterminada. `report --no-media` omite la copia completa de la referencia, pero conserva el texto y los recortes. [Privacidad (inglés)](docs/PRIVACY.md).

## Ayuda a dar forma al próximo flujo de edición

**Si quieres este flujo en tu caja de herramientas creativa, dale una estrella al proyecto.** Así ayudarás a otros creadores y desarrolladores de IA a descubrirlo.

**Haz un fork y construye tu propio vocabulario de edición:** añade un tratamiento de subtítulos, desarrolla un adaptador de renderizado, amplía una exportación o aporta un ejemplo propio que vaya de la referencia al resultado. Incluye evidencias reproducibles para que cada nueva capacidad se gane su lugar.

[**⭐ Dale una estrella en GitHub**](https://github.com/hieunguyenak92/rea-video-pro-max) · [**🍴 Haz un fork y crea**](https://github.com/hieunguyenak92/rea-video-pro-max/fork) · [Contribuir (inglés)](CONTRIBUTING.md) · [Proponer una tarea](https://github.com/hieunguyenak92/rea-video-pro-max/issues)

Proyecto independiente, inspirado en [JuneYaooo/rea-video](https://github.com/JuneYaooo/rea-video). [Apache-2.0](LICENSE); las condiciones específicas de fuentes, códecs y modelos se conservan en [NOTICE](NOTICE).

[Soporte (inglés)](SUPPORT.md) · [Mantenimiento (inglés)](docs/MAINTENANCE.md) · [Instrucciones del skill (inglés)](skills/rea-video-pro-max/SKILL.md)
