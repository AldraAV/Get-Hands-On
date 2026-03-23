# 🖐️ Get Hands-On (MeterMano)

> *"Le meto mano a tus archivos."*

**MeterMano** es una suite de manipulación de PDFs y documentos con interfaz nativa PyQt6. Diseñada para reemplazar Acrobat y herramientas online como ILovePDF con una alternativa local, rápida y sin suscripciones.

---

## ✨ Capacidades

### 📄 Manipulación de PDFs
| Operación | Descripción |
|---|---|
| **Separar** | 4 modos: todas las páginas, rango, específicas, por chunks |
| **Unir** | Combina múltiples PDFs en uno, con selección de páginas |
| **Rotar** | 90°, 180°, 270° en páginas seleccionadas |
| **Extraer** | Crea nuevo PDF solo con las páginas elegidas |
| **Eliminar** | Remueve páginas del documento |
| **Duplicar** | Clona páginas seleccionadas |
| **Reordenar** | Drag & drop en panel de miniaturas |
| **Insertar** | Páginas en blanco donde quieras |

### 🔄 Conversiones (Tier 1)
| Conversión | Motor | Resultado |
|---|---|---|
| **PDF → Word** | `pdf2docx` | `.docx` con layout, tablas e imágenes preservados |
| **PDF → Imágenes** | `pymupdf` | PNG o JPG a 150/300/600 DPI (seleccionable) |
| **Imágenes → PDF** | `img2pdf` + `Pillow` | Multi-imagen, soporta RGBA con fallback |
| **Comprimir PDF** | `pymupdf` | 3 niveles de calidad (alta/media/baja) |

### ✏️ Editor Visual (Beta)
- **Visor de páginas** con zoom, navegación y fit-to-width
- **Modo edición de texto** — Click en bloques de texto para editar
- **Modo anotaciones** — Resaltar, notas adhesivas, dibujo libre, sellos, marcas de agua, firmas

---

## 🚀 Instalación

### Prerequisitos
- Python 3.11+
- `pip install -r requirements.txt`

### Ejecutar
```bash
cd Get-Hands-On
python -m get_hands_on
```

### Dependencias principales
```
PyQt6          — GUI nativa
pymupdf (fitz) — Motor PDF principal (render, compress, images)
pdf2docx       — Conversión PDF → Word
pypdf/pikepdf  — Manipulación de estructura PDF
img2pdf        — Conversión imagen → PDF lossless
Pillow         — Procesamiento de imágenes
pytesseract    — OCR (futuro)
reportlab      — Generación de PDFs
python-docx    — Manipulación de Word
```

---

## 🏗️ Arquitectura

```
get_hands_on/
├── core/
│   ├── pdf_ops.py         # Motor PDF: split, merge, rotate, extract, delete, reorder
│   ├── converters.py      # Conversiones: PDF↔Word, PDF↔Images, Compress
│   └── annotations.py     # Anotaciones: highlight, stamps, watermarks
├── ui/
│   ├── main_window.py     # Ventana principal (Dashboard + Editor)
│   ├── style.py           # Aurora Theme (QSS)
│   ├── components/
│   │   ├── drop_area.py       # Zona de drag & drop
│   │   ├── file_list.py       # Lista de archivos cargados
│   │   ├── log_panel.py       # Log de actividad en tiempo real
│   │   ├── pages_panel.py     # Miniaturas de páginas (selección, reorder)
│   │   ├── document_canvas.py # Canvas del editor visual
│   │   └── annotation_toolbar.py # Toolbar lateral de anotaciones
│   └── dialogs/
│       ├── split_dialog.py    # Configuración de separación
│       └── merge_dialog.py    # Configuración de unión
├── workers/
│   ├── task_worker.py         # Worker genérico (QThread)
│   └── thumbnail_worker.py    # Renderizado de miniaturas en background
└── resources/                 # Íconos, fuentes, assets
```

---

## 🗺️ Roadmap

- [x] **Fase 1 (MVP)** — Manipulación básica: Unir, Separar, Rotar + UI Aurora
- [x] **Fase 1.5 (Conversiones)** — PDF↔Word, PDF↔Images, Compresión
- [ ] **Fase 2 (Experience)** — Miniaturas drag & drop, UI contextual, animaciones
- [ ] **Fase 2.5 (Tier 2)** — Word→PDF, Excel→PDF, PPT→PDF, OCR, HTML→PDF
- [ ] **Fase 3 (Adobe Killer)** — Edición de texto/imágenes inline, OCR masivo, formularios, firmas digitales, seguridad (passwords, cifrado)

---

## 🥚 Easter Egg

Abre un archivo llamado `cerezas.pdf` 🍒

---

*Parte del ecosistema Aldraverse.* ☀️
*Hecho por Cheché.*
