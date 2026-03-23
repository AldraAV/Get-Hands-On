# MeterMano (Get Hands-On)
**Versión:** 1.0.0
**Arquitectura:** Native Desktop Application (PyQt6)

MeterMano es una suite integral y de alto rendimiento para la manipulación local de documentos PDF. Diseñada bajo una arquitectura modular y orientada a eventos, reemplaza la necesidad de servicios basados en la nube mediante el procesamiento On-Premise, garantizando máxima privacidad corporativa y baja latencia.

---

## 🛠️ Stack Tecnológico y Dependencias Core

El núcleo de renderizado y manipulación se fundamenta en las siguientes librerías:

*   **PyQt6:** Motor gráfico (GUI) nativo con manejo asíncrono de QThreads y Signals para evitar el bloqueo del Event Loop principal.
*   **PyMuPDF (fitz):** Motor PDF de bajo nivel utilizado para renderizado de alta velocidad, compresión binaria y extracción matricial de imágenes.
*   **PyTesseract:** Wrapper para el motor OCR óptico de Google, empleado en la vectorización de documentos escaneados.
*   **PikePDF / PyPDF:** Gestión de subestructuras de árboles PDF y encriptación robusta bajo el estándar AES-256.
*   **pdf2docx:** Conversor heurístico de cajas lógicas para transformación PDF → Word preservando layouts y tablas.
*   **Pillow (PIL) & img2pdf:** Pipeline sin pérdida (lossless) para la compresión e interpolación RGBA multicapa en la conversión de imágenes bidireccionales.

> **Nota Técnica (OCR):** El módulo de reconocimiento óptico de caracteres requiere que el binario `tesseract.exe` esté compilado e incluido en la variable de entorno PATH del sistema anfitrión.

---

## ⚙️ Características Técnicas (Features)

| Módulo | Algoritmo / Función | Capacidad Destacada |
| :--- | :--- | :--- |
| **Manipulación Estructural** | Split, Merge, Rotate, Extract | Procesamiento por chunks (Buffer memory), soporte de reordenamiento de objetos internos del PDF. |
| **Conversión Bi-Direccional** | Renderizado Matricial (Rasterizer) | PDF a Word (`.docx`), PDF a Imágenes (Soporte DPI Dinámico 150/300/600), Imágenes a PDF. |
| **Motor Batch** | Threading | Aplicación de operaciones (ej. Compresión múltiple) en paralelo sobre `N` archivos simultáneamente. |
| **Seguridad y Criptografía** | AES-256 (PikePDF) | Cifrado granular (Owner ID, User Pass) con restricción estricta de permisos de impresión, copia y modificación. |

---

## 🏗️ Estructura del Proyecto

La base de código respeta la separación de preocupaciones (Separation of Concerns), aislando la lógica de negocio (`core/`) de la presentación (`ui/`).

```text
get_hands_on/
├── core/
│   ├── batch.py           # Workers de ejecución múltiple y progreso
│   ├── converters.py      # Puente hacia pdf2docx, tesseract y rasterizadores
│   ├── pdf_ops.py         # Interfaces de mutación de PyMuPDF
│   └── security.py        # Módulo criptográfico AES
├── ui/
│   ├── main_window.py     # Controlador principal del Window Manager
│   ├── style.py           # Inyección de estilos QSS (Global Theme)
│   ├── components/        # Widgets atómicos (Paneles, Drag & Drop, Canvas)
│   └── dialogs/           # Ventanas modales transaccionales
├── workers/
│   ├── task_worker.py     # Implementación QRunnable / QThread
│   └── thumbnail_worker.py# Generador asíncrono de pre-visualizaciones
└── resources/             # Assets estáticos y binarios empotrados
```

## 🚀 Instalación y Build de Producción

Para entornos de desarrollo:
```bash
pip install -r requirements.txt
python -m get_hands_on
```

Para generar un binario nativo de distribución (Stand-alone Executable):
El repositorio incluye rutinas de empaquetado mediante `PyInstaller`. Las exclusiones de dependencias redundantes (ej. `[matplotlib, pandas]`) están estrictamente definidas en `MeterMano.spec` para minimizar el footprint en disco.
