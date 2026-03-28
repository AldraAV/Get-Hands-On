# 🖐️ Get Hands-On (MeterMano)
**Versión:** 1.1.0
**Arquitectura:** Native Desktop Application (PyQt6)

MeterMano es una suite integral y de alto rendimiento para la manipulación local de documentos PDF y redacción técnica en Markdown. Diseñada bajo una arquitectura modular y orientada a eventos, reemplaza la necesidad de servicios basados en la nube mediante el procesamiento On-Premise, garantizando máxima privacidad y baja latencia.

---

## 🛠️ Stack Tecnológico y Dependencias Core

El núcleo de renderizado y manipulación se fundamenta en las siguientes librerías:

*   **PyQt6:** Motor gráfico (GUI) nativo con manejo asíncrono de QThreads y Signals para evitar el bloqueo del Event Loop principal. Incluye `QTextDocument` y `QPdfWriter` para el pipeline de renderizado Markdown → HTML → PDF.
*   **PyMuPDF (fitz ≥ 1.23):** Motor PDF de bajo nivel utilizado para renderizado de alta velocidad, compresión binaria, extracción matricial de imágenes y — desde v1.23 — **detección geométrica de tablas** (`page.find_tables()`) para extracción estructurada de contenido tabular.
*   **PyTesseract:** Wrapper para el motor OCR óptico de Google, empleado en la vectorización de documentos escaneados.
*   **PikePDF / PyPDF:** Gestión de subestructuras de árboles PDF y encriptación robusta bajo el estándar AES-256.
*   **pdf2docx:** Conversor heurístico de cajas lógicas para transformación PDF → Word preservando layouts y tablas.
*   **Pillow (PIL) & img2pdf:** Pipeline sin pérdida (lossless) para la compresión e interpolación RGBA multicapa en la conversión de imágenes bidireccionales.

> **Nota Técnica (OCR):** El módulo de reconocimiento óptico de caracteres requiere que el binario `tesseract.exe` esté compilado e incluido en la variable de entorno PATH del sistema anfitrión.

> **Nota Técnica (Tablas):** La detección de tablas PDF requiere PyMuPDF >= 1.23.0. En versiones anteriores, el extractor de Markdown opera en modo texto plano sin reconstrucción de estructura tabular.

---

## ⚙️ Características Técnicas (Features)

| Módulo | Algoritmo / Función | Capacidad Destacada |
| :--- | :--- | :--- |
| **Manipulación Estructural** | Split, Merge, Rotate, Extract | Procesamiento por chunks (Buffer memory), soporte de reordenamiento de objetos internos del PDF. |
| **Conversión Bi-Direccional** | Renderizado Matricial (Rasterizer) | PDF a Word (`.docx`), PDF a Imágenes (Soporte DPI Dinámico 150/300/600), Imágenes a PDF. |
| **Motor Batch** | Threading | Aplicación de operaciones (ej. Compresión múltiple) en paralelo sobre `N` archivos simultáneamente. |
| **Seguridad y Criptografía** | AES-256 (PikePDF) | Cifrado granular (Owner ID, User Pass) con restricción estricta de permisos de impresión, copia y modificación. |
| **Editor Markdown (NUEVO v1.1)** | Split-View / QSplitter | Panel dual con edición raw MD (izquierda) y previsualización HTML en vivo con CSS Aurora (derecha). |
| **Extractor PDF → MD (NUEVO v1.1)** | PyMuPDF `get_text("dict")` + `find_tables()` | Heurística de tamaño de fuente para reconstruir jerarquía `#`/`##`/`###`. Tablas del PDF → sintaxis GFM `\| col \|`. |
| **Exportador MD → PDF (NUEVO v1.1)** | `QTextDocument` + `QPdfWriter` | Renderizado MD a HTML con CSS inyectado, exportación a PDF tamaño Carta sin dependencias externas de WebKit. |
| **Guardado Markdown (NUEVO v1.1)** | I/O UTF-8 nativo | Exportación directa del contenido del editor a `.md` o `.txt` con actualización del nombre en la barra de título. |

---

## 🏗️ Estructura del Proyecto

La base de código respeta la separación de preocupaciones (Separation of Concerns), aislando la lógica de negocio (`core/`) de la presentación (`ui/`).

```text
get_hands_on/
├── core/
│   ├── batch.py           # Workers de ejecución múltiple y progreso
│   ├── converters.py      # Puente hacia pdf2docx, tesseract y rasterizadores
│   ├── markdown_ops.py    # [NUEVO] Motor MD↔PDF: extracción heurística, detección de tablas y exportación
│   ├── pdf_ops.py         # Interfaces de mutación de PyMuPDF
│   └── security.py        # Módulo criptográfico AES
├── ui/
│   ├── main_window.py     # Controlador principal del Window Manager (QStackedWidget: Dashboard / Canvas / MD Editor)
│   ├── style.py           # Inyección de estilos QSS (Global Theme Aurora)
│   ├── components/
│   │   ├── markdown_editor.py  # [NUEVO] Widget Editor Markdown Split-View (QSplitter)
│   │   └── ...            # Otros widgets atómicos (Paneles, Drag & Drop, Canvas)
│   └── dialogs/           # Ventanas modales transaccionales
├── workers/
│   ├── task_worker.py     # Implementación QRunnable / QThread
│   └── thumbnail_worker.py# Generador asíncrono de pre-visualizaciones
└── resources/             # Assets estáticos y binarios empotrados
```

---

## 📝 Editor Markdown (v1.1)

El módulo de Editor Markdown se accede desde el botón **`📝 Editor Markdown (.md ↔ .pdf)`** en el panel de Conversiones del Dashboard principal.

### Flujo de trabajo
```
PDF ──find_tables()──► Tablas GFM ──╮
                                    ├──► Panel Editor (Raw MD) ──► Previsualización live HTML/CSS
PDF ──heurística fuentes──► Texto ──╯                          ──► Guardar .md
                                                               ──► Exportar PDF estilizado
```

### Barra de herramientas
| Botón | Acción |
| :--- | :--- |
| ⬅ Volver | Regresa al Dashboard principal sin perder el contenido del editor |
| 📂 Abrir .MD | Carga un archivo `.md` o `.txt` existente en el panel de edición |
| 🪄 Extraer desde PDF | Analiza un PDF con PyMuPDF y reconstruye su contenido como Markdown |
| 💾 Guardar .MD | Escribe el contenido actual del editor como archivo `.md` en disco |
| ⬇️ Exportar a PDF | Renderiza el Markdown con CSS Aurora y genera un PDF tamaño Carta |

### Detección de tablas
El extractor (`markdown_ops.py`) realiza dos pasadas sobre cada página del PDF:
1. **Pasada de tablas:** `page.find_tables()` detecta bordes geométricos de celdas y extrae el contenido en `list[list[str]]`, que se serializa a sintaxis GFM (`| col | col |` con separador `---`).
2. **Pasada de texto:** Los bloques de texto cuyo bounding box intersecte con una región de tabla ya extraída son omitidos, evitando duplicados. El resto se clasifica por tamaño de fuente (mediana como referencia) en `#`, `##`, `###` o párrafo.

---

## 🚀 Instalación y Build de Producción

Para entornos de desarrollo:
```bash
pip install -r requirements.txt
python -m get_hands_on
```

Para generar un binario nativo de distribución (Stand-alone Executable):
El repositorio incluye rutinas de empaquetado mediante `PyInstaller`. Las exclusiones de dependencias redundantes (ej. `[matplotlib, pandas]`) están estrictamente definidas en `MeterMano.spec` para minimizar el footprint en disco.



