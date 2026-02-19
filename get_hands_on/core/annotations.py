"""
annotations.py — Motor de anotaciones PDF usando PyMuPDF.
Funciones puras que operan sobre fitz.Page.
"""

import fitz
from pathlib import Path


# ─── HIGHLIGHTING & TEXT MARKUP ───────────────────────────

def add_highlight(page, quads, color=(1, 1, 0)):
    """Resaltar texto. Color por defecto: amarillo."""
    annot = page.add_highlight_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def add_underline(page, quads, color=(0, 0, 1)):
    """Subrayar texto. Color por defecto: azul."""
    annot = page.add_underline_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


def add_strikeout(page, quads, color=(1, 0, 0)):
    """Tachar texto. Color por defecto: rojo."""
    annot = page.add_strikeout_annot(quads)
    annot.set_colors(stroke=color)
    annot.update()
    return annot


# ─── STICKY NOTES ─────────────────────────────────────────

def add_sticky_note(page, point, text, icon="Note"):
    """Agregar nota adhesiva en un punto.
    Icons: Note, Comment, Help, Insert, Key, Paragraph.
    """
    annot = page.add_text_annot(point, text, icon=icon)
    annot.set_colors(stroke=(1, 0.65, 0.1))  # Naranja Aurora
    annot.update()
    return annot


# ─── STAMPS ───────────────────────────────────────────────

STAMPS = {
    "APROBADO": fitz.TEXT_ALIGN_CENTER,
    "RECHAZADO": fitz.TEXT_ALIGN_CENTER,
    "CONFIDENCIAL": fitz.TEXT_ALIGN_CENTER,
    "BORRADOR": fitz.TEXT_ALIGN_CENTER,
    "FINAL": fitz.TEXT_ALIGN_CENTER,
    "COPIA": fitz.TEXT_ALIGN_CENTER,
    "REVISADO": fitz.TEXT_ALIGN_CENTER,
    "URGENTE": fitz.TEXT_ALIGN_CENTER,
}


def add_stamp(page, rect, stamp_text="APROBADO", color=(1, 0, 0), fontsize=36, opacity=0.5):
    """Agregar sello de texto con rotación y opacidad."""
    # Dibujar rectángulo de fondo semitransparente
    shape = page.new_shape()
    shape.draw_rect(rect)
    shape.finish(
        color=color,
        fill=None,
        width=3,
        stroke_opacity=opacity,
    )
    shape.commit()

    # Insertar texto del sello
    page.insert_textbox(
        rect,
        stamp_text,
        fontsize=fontsize,
        fontname="helv",
        color=color,
        align=fitz.TEXT_ALIGN_CENTER,
    )
    return True


# ─── FREEHAND DRAWING (INK ANNOTATION) ───────────────────

def add_freehand(page, points_list, color=(0, 0, 0), width=2):
    """Dibujo a mano alzada. points_list = [[point1, point2, ...], ...]
    Cada sub-lista es un trazo continuo.
    """
    annot = page.add_ink_annot(points_list)
    annot.set_colors(stroke=color)
    annot.set_border(width=width)
    annot.update()
    return annot


# ─── SIGNATURE ────────────────────────────────────────────

def add_signature(page, rect, image_path):
    """Insertar imagen de firma en el rectángulo especificado."""
    page.insert_image(rect, filename=str(image_path))
    return True


# ─── WATERMARK ────────────────────────────────────────────

def add_watermark_to_page(page, text="CONFIDENCIAL", fontsize=60,
                          color=(0.75, 0.75, 0.75), opacity=0.3, rotation=45):
    """Agregar marca de agua diagonal a una página."""
    rect = page.rect

    # Calcular posición central
    cx = rect.width / 2
    cy = rect.height / 2

    # Insertar texto con rotación usando shape
    tw = fitz.TextWriter(page.rect)
    font = fitz.Font("helv")

    # Calcular tamaño del texto
    text_width = font.text_length(text, fontsize=fontsize)

    # Punto de inicio centrado
    start_x = cx - text_width / 2
    start_y = cy + fontsize / 2

    tw.append((start_x, start_y), text, font=font, fontsize=fontsize)
    tw.write_text(page, color=color, opacity=opacity, morph=(fitz.Point(cx, cy), fitz.Matrix(rotation)))

    return True


def add_watermark_to_all(doc, text="CONFIDENCIAL", **kwargs):
    """Agregar marca de agua a todas las páginas."""
    for page in doc:
        add_watermark_to_page(page, text, **kwargs)
    return True


# ─── REDACTION ────────────────────────────────────────────

def redact_area(page, rect, fill_color=(0, 0, 0)):
    """Censurar un área permanentemente (negro por defecto)."""
    annot = page.add_redact_annot(rect, fill=fill_color)
    page.apply_redactions()
    return True


# ─── TEXT SEARCH FOR ANNOTATIONS ──────────────────────────

def search_text_quads(page, search_text):
    """Buscar texto y retornar quads para anotaciones."""
    return page.search_for(search_text, quads=True)


# ─── LIST ANNOTATIONS ────────────────────────────────────

def list_annotations(page):
    """Listar todas las anotaciones de una página."""
    annots = []
    for annot in page.annots():
        annots.append({
            "type": annot.type[1],  # Nombre del tipo
            "rect": annot.rect,
            "content": annot.info.get("content", ""),
        })
    return annots


def delete_annotation(page, annot):
    """Eliminar una anotación."""
    page.delete_annot(annot)
    return True
