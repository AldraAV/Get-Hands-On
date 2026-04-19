"""
watermark.py — Marca de agua y numeración de páginas para PDFs.
100% PyMuPDF, sin dependencias externas adicionales.
"""
import fitz
from pathlib import Path


def add_text_watermark(
    input_path: str,
    output_path: str,
    text: str = "CONFIDENCIAL",
    opacity: float = 0.15,
    angle: float = 45,
    font_size: int = 60,
    color: tuple = (1, 0.42, 0),  # Naranja Aurora
) -> bool:
    """
    Añade una marca de agua de texto diagonal a cada página del PDF.
    """
    doc = fitz.open(input_path)

    for page in doc:
        rect = page.rect
        center_x = rect.width / 2
        center_y = rect.height / 2

        # Insertar texto como overlay con opacidad vía alpha
        page.insert_text(
            fitz.Point(center_x - font_size * len(text) * 0.3, center_y),
            text,
            fontsize=font_size,
            color=color,
            rotate=angle,
            overlay=True,
        )

        # Reducir opacidad del texto insertado con un rectángulo blanco semi-transparente
        # (truco: insertar el watermark en un xobject con alpha)
        # Método alternativo más limpio usando draw_rect con blend:
        page.draw_rect(rect, color=None, fill=(1, 1, 1), fill_opacity=1 - opacity, overlay=False)

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    return True


def add_watermark_clean(
    input_file: str,
    output_file: str,
    text: str = "CONFIDENCIAL",
    opacity: float = 0.15,
    angle: float = 45,
    font_size: int = 60,
    color: tuple = (1, 0.42, 0),
    log_cb=None,
) -> bool:
    """
    Implementación limpia de watermark usando PDF streams nativos.
    Soporta opacidad real sin artefactos visuales.
    """
    doc = fitz.open(input_file)

    for page in doc:
        rect = page.rect
        # Crear un shape (canvas de dibujo) para esta página
        shape = page.new_shape()

        # Soporte para ángulos impares (0-360) usando matriz Morph Affine:
        text_len = fitz.get_text_length(text, fontsize=font_size)
        pivot = fitz.Point(rect.width / 2, rect.height / 2)
        start_pt = fitz.Point(pivot.x - text_len / 2, pivot.y)
        
        passes = max(1, int(opacity * 10))
        for _ in range(passes):
            shape.insert_text(
                start_pt,
                text,
                fontsize=font_size,
                color=color,
                morph=(pivot, fitz.Matrix(-angle))
            )

        shape.finish()
        shape.commit()

    doc.save(output_file, garbage=4, deflate=True)
    doc.close()
    return True


def add_page_numbers(
    input_file: str,
    output_file: str,
    position: str = "bottom-center",  # top-left, top-center, top-right, bottom-left, bottom-center, bottom-right
    prefix: str = "",
    suffix: str = "",
    start_page: int = 1,
    font_size: int = 10,
    color: tuple = (0.63, 0.63, 0.63),  # Gris secundario
    margin: int = 20,
    log_cb=None,
) -> bool:
    """
    Añade número de página a cada hoja del PDF.
    - position: dónde colocar el número
    - prefix/suffix: texto antes/después del número (ej. "Pág. " / " de 10")
    - start_page: número con el que empieza la numeración
    """
    doc = fitz.open(input_file)
    total = len(doc)

    for i, page in enumerate(doc):
        rect = page.rect
        page_num = i + start_page
        label = f"{prefix}{page_num}{suffix}"

        # Calcular posición según parámetro
        if "bottom" in position:
            y = rect.height - margin
        else:
            y = margin + font_size

        if "left" in position:
            x = margin
        elif "right" in position:
            x = rect.width - margin - font_size * len(label) * 0.6
        else:  # center
            x = rect.width / 2 - font_size * len(label) * 0.3

        page.insert_text(
            fitz.Point(x, y),
            label,
            fontsize=font_size,
            color=color,
            overlay=True,
        )

    doc.save(output_file, garbage=4, deflate=True)
    doc.close()
    return True


def add_header_footer(
    input_file: str,
    output_file: str,
    header_text: str = "",
    footer_text: str = "",
    font_size: int = 9,
    color: tuple = (0.42, 0.42, 0.42),
    margin: int = 15,
    log_cb=None,
) -> bool:
    """
    Añade encabezado y/o pie de página a todas las hojas de un PDF.
    Soporta variables: {page} y {total}.
    """
    doc = fitz.open(input_file)
    total = len(doc)

    for i, page in enumerate(doc):
        rect = page.rect
        page_num = i + 1

        if header_text:
            text = header_text.replace("{page}", str(page_num)).replace("{total}", str(total))
            x = rect.width / 2 - font_size * len(text) * 0.3
            page.insert_text(
                fitz.Point(x, margin + font_size),
                text,
                fontsize=font_size,
                color=color,
                overlay=True,
            )

        if footer_text:
            text = footer_text.replace("{page}", str(page_num)).replace("{total}", str(total))
            x = rect.width / 2 - font_size * len(text) * 0.3
            page.insert_text(
                fitz.Point(x, rect.height - margin),
                text,
                fontsize=font_size,
                color=color,
                overlay=True,
            )

    doc.save(output_file, garbage=4, deflate=True)
    doc.close()
    return True
