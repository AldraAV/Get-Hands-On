import os
import fitz  # PyMuPDF
from PyQt6.QtGui import QTextDocument, QPageSize, QPageLayout
from PyQt6.QtPrintSupport import QPrinter

def parse_pdf_to_md(pdf_path: str) -> str:
    """
    Extracción heurística de texto desde PDF a formato Markdown usando PyMuPDF (fitz).
    Detecta tablas con find_tables() y las renderiza como tablas Markdown.
    Detecta tamaños de fuente para recrear encabezados H1-H3.
    """
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return f"# Error al abrir el PDF\n{str(e)}"

    md_lines = []

    # Primera pasada: calcular tamaño de fuente base (mediana)
    font_sizes = []
    for page in doc:
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if b.get("type") == 0:
                for line in b.get("lines", []):
                    for span in line.get("spans", []):
                        font_sizes.append(span.get("size", 10.0))

    if not font_sizes:
        return "# Este PDF no contiene texto extraíble."

    font_sizes.sort()
    base_size = font_sizes[len(font_sizes) // 2]

    # Segunda pasada: extracción con detección de tablas intercaladas
    for page in doc:
        # --- Detectar tablas (requiere PyMuPDF >= 1.23.0) ---
        table_bboxes = []
        table_md_blocks = []  # list of (fitz.Rect, str_md)

        try:
            tabs = page.find_tables()
            for tab in tabs.tables:
                tbbox = fitz.Rect(tab.bbox)
                table_bboxes.append(tbbox)
                table_md_blocks.append((tbbox, _table_to_md(tab)))
            # Ordenar por posición vertical en la página
            table_md_blocks.sort(key=lambda x: x[0].y0)
        except AttributeError:
            # PyMuPDF < 1.23: sin soporte de find_tables, continúa sin tablas
            pass

        emitted_tables = set()
        blocks = page.get_text("dict").get("blocks", [])

        for b in blocks:
            bbox_b = fitz.Rect(b.get("bbox", [0, 0, 0, 0]))

            # Emitir tablas que aparecen antes o al nivel de este bloque
            for i, (tbbox, tmd) in enumerate(table_md_blocks):
                if i not in emitted_tables and tbbox.y0 <= bbox_b.y0:
                    md_lines.append(tmd)
                    md_lines.append("")
                    emitted_tables.add(i)

            # Saltar bloques que forman parte de una tabla ya extraída
            if any(tbbox.contains(bbox_b) or tbbox.intersects(bbox_b)
                   for tbbox in table_bboxes):
                continue

            if b.get("type") != 0:
                continue

            block_text = ""
            max_size_in_block = 0
            is_bold = False

            for line in b.get("lines", []):
                for span in line.get("spans", []):
                    text = span.get("text", "").strip()
                    if not text:
                        continue
                    size = span.get("size", base_size)
                    if size > max_size_in_block:
                        max_size_in_block = size
                    if span.get("flags", 0) & 2**4:
                        is_bold = True
                    block_text += text + " "

            block_text = block_text.strip()
            if not block_text:
                continue

            if max_size_in_block > base_size * 1.8:
                md_lines.append(f"# {block_text}")
            elif max_size_in_block > base_size * 1.4:
                md_lines.append(f"## {block_text}")
            elif max_size_in_block > base_size * 1.1:
                md_lines.append(f"### {block_text}")
            else:
                md_lines.append(f"**{block_text}**" if is_bold else block_text)

            md_lines.append("")

        # Emitir tablas que quedaron al final de la página
        for i, (tbbox, tmd) in enumerate(table_md_blocks):
            if i not in emitted_tables:
                md_lines.append(tmd)
                md_lines.append("")

    doc.close()
    return "\n".join(md_lines)


def _table_to_md(tab) -> str:
    """
    Convierte un objeto Table de PyMuPDF a sintaxis Markdown GFM.
    La primera fila se trata como encabezado con separador ---.
    """
    try:
        data = tab.extract()
    except Exception:
        return ""

    if not data:
        return ""

    md_rows = []
    for row_idx, row in enumerate(data):
        cells = [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
        md_rows.append("| " + " | ".join(cells) + " |")
        if row_idx == 0:
            md_rows.append("|" + "|".join(["---"] * len(cells)) + "|")

    return "\n".join(md_rows)


def markdown_to_html(md_text: str) -> str:
    """Convierte texto MD a HTML usando QTextDocument incorporado."""
    doc = QTextDocument()
    doc.setMarkdown(md_text)
    return doc.toHtml()


def export_html_to_pdf(html_content: str, output_path: str):
    """
    Renderiza un string HTML a un archivo físico PDF utilizando QPrinter.
    Mantiene a Get Hands-On con cero dependencias externas de compilación web.
    """
    document = QTextDocument()
    document.setHtml(html_content)
    
    printer = QPrinter(QPrinter.PrinterMode.HighResolution)
    printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
    printer.setOutputFileName(output_path)
    
    # Layout por defecto: Carta (Letter), márgenes de 10mm
    layout = QPageLayout()
    layout.setPageSize(QPageSize(QPageSize.PageSizeId.Letter))
    layout.setOrientation(QPageLayout.Orientation.Portrait)
    printer.setPageLayout(layout)
    
    document.print(printer)
    return True
