**CHECHÉ.**

**¡Ya está vivo!** 🖐️✨

Se ve exactamente como debería. Aurora, log en Consolas, firma de Aldra en el footer, el slogan naranja. **Fase 1 real.**

Y sí, tienes razón. Ahorita es funcional pero básico. Le falta ese peso visual que tiene Acrobat o los editores serios. Vamos a atacar eso.

---

## 🎯 LO QUE FALTA PARA QUE SE VEA SERIO

Hay tres capas de mejora:

**Capa 1 — Vista de páginas (la más importante)**

Lo que hace que Acrobat se sienta como herramienta real es que ves las páginas como miniaturas y puedes seleccionarlas, reordenarlas, marcarlas. Eso cambia todo.

```
┌──────────────────────────────────────────────┐
│  PÁGINAS DEL DOCUMENTO                       │
│  ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐   │
│  │  [1]  │ │  [2]  │ │  [3]  │ │  [4]  │   │
│  │  ███  │ │  ███  │ │  ███  │ │  ███  │   │
│  │  ███  │ │  ███  │ │  ███  │ │  ███  │   │
│  └───────┘ └───────┘ └───────┘ └───────┘   │
│   Pág. 1    Pág. 2    Pág. 3    Pág. 4     │
└──────────────────────────────────────────────┘
```

Cada miniatura es clickeable, seleccionable (Ctrl+Click para múltiples), y cuando seleccionas páginas los botones de Extraer/Eliminar/Rotar se activan automáticamente para esas páginas específicas. **Eso es lo que hace que se sienta pro.**

Se hace con `pdf2image` para renderizar las miniaturas y un `QGridLayout` de `QLabel` con bordes naranja al seleccionar.

---

**Capa 2 — Panel derecho más rico**

Ahorita el panel de operaciones es una columna de botones. Para que se vea como M365 necesita más estructura visual: separadores con títulos, iconos SVG reales (no emojis), y los botones que no aplican al contexto actual que estén deshabilitados con opacidad reducida.

Por ejemplo: si solo hay 1 archivo cargado, el botón "Unir PDFs" aparece apagado. Si hay páginas seleccionadas en la vista de miniaturas, "Extraer páginas" se ilumina con borde naranja. Eso se llama **UI contextual** y es lo que separa las herramientas serias de las básicas.

---

**Capa 3 — Feedback visual más rico**

Ahorita el feedback es solo texto en el log. Acrobat y M365 tienen animaciones sutiles. Cuando termina una operación, el archivo aparece en la lista con un checkmark verde animado.

---

## 🚀 FASE 3: EL GRAN CATÁLOGO (Rumbo a Adobe)

Para competir con Acrobat en funcionalidad ("Edición Individual"), necesitamos expandir el motor `core` drásticamente. Aquí está el menú de capabilities que podemos implementar:

### 1. Edición de Contenido (Hardcore)
> *La "magia" de Acrobat: cambiar texto e imágenes dentro del PDF.*
*   **Editar Texto**: Detectar bloques de texto, permitir reescribir, cambiar fuente/tamaño. (Library: `pymupdf` / `fitz`)
*   **Editar Imágenes**: Mover, redimensionar, reemplazar o borrar imágenes existentes.
*   **Redacción (Censura)**: Cubrir texto confidencial con barras negras reales (no solo dibujo encima).

### 2. Anotaciones y Revisión
*   **Resaltar (Highlight)**: Amarillo clásico, verde, etc.
*   **Notas Adhesivas (Sticky Notes)**: Comentarios flotantes.
*   **Dibujo a Mano Alzada**: Para tablets o firmas rápidas.
*   **Sellos (Stamps)**: "APROBADO", "CONFIDENCIAL", etc.

### 3. Formularios y Firmas
*   **Rellenar Formularios**: Detectar campos de texto interactivos.
*   **Firmar**: Insertar imagen de firma o dibujarla.

### 4. Conversión y OCR
*   **PDF a Word/Excel**: (Library: `pdf2docx`)
*   **OCR (Reconocimiento de Texto)**: Convertir PDFs escaneados (imágenes) en texto seleccionable. (Library: `tesseract` + `pytesseract`)
*   **Compresión**: Reducir tamaño de archivo (optimizar imágenes).

### 5. Seguridad
*   **Contraseñas**: Encriptar (User/Owner passwords).
*   **Marcas de Agua**: Texto o imagen semitransparente de fondo.

---

## 🗺️ PLAN TÉCNICO FASE 3 (Propuesta)

Para lograr "Edición de Archivos Individual", necesitamos un **Visor de Página Completa** (no solo miniaturas).

1.  **Nuevo Visor (Canvas)**: Una ventana o pestaña donde ves la página en grande.
2.  **Modo Edición**: Al activar, dibujamos "bounding boxes" alrededor de cada párrafo/imagen usando `pymupdf`.
3.  **Interacción**:
    *   Click en texto -> Abre cuadro de edición -> Enter -> `pymupdf` reemplaza el texto.
    *   Click en imagen -> Handles para redimensionar o Click derecho "Reemplazar".

¿Te late empezar por **Editor de Texto** (lo más difícil pero impresionante) o **Anotaciones** (más visual y rápido)?