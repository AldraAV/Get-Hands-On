"""
DocumentCanvas — Editor PDF central de Get Hands-On.
Visor de página completa con modos de operación, zoom inteligente y edición de texto.
"""

import fitz
import traceback
from enum import Enum
from pathlib import Path

from PyQt6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsRectItem, QFileDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QRectF
from PyQt6.QtGui import (
    QPixmap, QImage, QPainter, QWheelEvent, QTransform,
    QColor, QPen, QBrush, QCursor
)
from ..style import AURORA


class EditorMode(Enum):
    VIEW = "view"
    EDIT_TEXT = "edit_text"
    ANNOTATE = "annotate"


class HoverableBlock(QGraphicsRectItem):
    """Bloque de texto interactivo con hover visual."""

    def __init__(self, x, y, w, h, block_no, text, canvas):
        super().__init__(x, y, w, h)
        self.block_no = block_no
        self.text = text
        self.canvas = canvas

        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.setAcceptHoverEvents(True)
        self.setData(0, block_no)
        self.setData(1, text)

    def hoverEnterEvent(self, event):
        if self.canvas.mode == EditorMode.EDIT_TEXT:
            self.setPen(QPen(QColor("#4A9EFF"), 1.5, Qt.PenStyle.DashLine))
            self.setBrush(QBrush(QColor(74, 158, 255, 20)))
            self.setCursor(QCursor(Qt.CursorShape.IBeamCursor))
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setPen(QPen(Qt.PenStyle.NoPen))
        self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        self.unsetCursor()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if self.canvas.mode == EditorMode.EDIT_TEXT and event.button() == Qt.MouseButton.LeftButton:
            # Feedback de selección
            self.setPen(QPen(QColor(AURORA['accent_orange']), 2))
            self.setBrush(QBrush(QColor(255, 122, 24, 30)))

            # Obtener info de fuente del bloque
            font_info = self.canvas._get_block_font(
                self.canvas.doc.load_page(self.canvas.current_page_idx),
                self.canvas._block_rect(self.block_no)
            ) if self.canvas.doc else None

            # Abrir editor avanzado
            from ..dialogs.text_edit_dialog import TextEditDialog
            dialog = TextEditDialog(self.text, font_info=font_info, parent=self.canvas)
            if dialog.exec():
                new_text = dialog.new_text
                if new_text and new_text != self.text:
                    self.canvas._apply_text_change(
                        self.block_no, new_text,
                        fontname=dialog.font_name,
                        fontsize=dialog.font_size,
                        color=dialog.get_color_normalized()
                    )
            else:
                # Restaurar visual
                self.setPen(QPen(Qt.PenStyle.NoPen))
                self.setBrush(QBrush(QColor(0, 0, 0, 0)))
        else:
            super().mousePressEvent(event)


class DocumentCanvas(QGraphicsView):
    """Visor de documento con zoom inteligente, modos de edición y navegación."""

    page_changed = pyqtSignal(int, int)   # (current_page, total_pages)
    zoom_changed = pyqtSignal(int)        # zoom percentage
    mode_changed = pyqtSignal(str)        # mode name
    status_message = pyqtSignal(str)      # status bar messages

    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc = None
        self.current_page_idx = 0
        self.zoom_factor = 1.5  # Default 150% para buena legibilidad
        self.file_path = None
        self.mode = EditorMode.VIEW
        self._has_unsaved_changes = False

        # Scene
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)

        # Render hints
        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)

        # Style
        self.setStyleSheet(f"""
            QGraphicsView {{
                background: {AURORA['bg_deep']};
                border: none;
            }}
        """)

        # Main pixmap item
        self.pixmap_item = QGraphicsPixmapItem()
        self.scene.addItem(self.pixmap_item)

        # Annotation state
        self._init_annotation_state()

    # ─── DOCUMENT LIFECYCLE ───────────────────────────────────

    def load_document(self, file_path: Path):
        """Carga un documento PDF."""
        self.file_path = file_path
        try:
            if self.doc:
                self.doc.close()
            self.doc = fitz.open(str(file_path))
            self.current_page_idx = 0
            self.zoom_factor = 1.5
            self._has_unsaved_changes = False
            self.render_page()
            self.resetTransform()
            self.status_message.emit(f"Cargado: {file_path.name} ({len(self.doc)} páginas)")
        except Exception as e:
            self.status_message.emit(f"❌ Error: {e}")

    def save_changes(self) -> bool:
        """Guarda cambios. Intenta incremental primero, luego save-as."""
        if not self.doc or not self.file_path:
            return False

        # Intentar guardar incremental
        try:
            temp_path = self.file_path.parent / f".~{self.file_path.name}.tmp"
            self.doc.save(str(temp_path))
            self.doc.close()

            # Reemplazar original con temp
            import shutil
            shutil.move(str(temp_path), str(self.file_path))

            # Reabrir documento
            self.doc = fitz.open(str(self.file_path))
            self._has_unsaved_changes = False
            self.status_message.emit(f"💾 Guardado: {self.file_path.name}")
            return True

        except Exception as e:
            self.status_message.emit(f"⚠️ Error guardando: {e}")
            # Cleanup temp
            if temp_path.exists():
                temp_path.unlink()
            return False

    def save_as(self) -> bool:
        """Guardar como nuevo archivo."""
        if not self.doc:
            return False

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar Como", str(self.file_path.parent),
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return False

        try:
            self.doc.save(file_path)
            self.file_path = Path(file_path)
            self._has_unsaved_changes = False
            self.status_message.emit(f"💾 Guardado como: {Path(file_path).name}")
            return True
        except Exception as e:
            self.status_message.emit(f"❌ Error: {e}")
            return False

    @property
    def has_unsaved_changes(self):
        return self._has_unsaved_changes

    @property
    def total_pages(self):
        return len(self.doc) if self.doc else 0

    @property
    def current_page(self):
        return self.current_page_idx + 1

    # ─── MODES ────────────────────────────────────────────────

    def set_mode(self, mode: EditorMode):
        """Cambia el modo del editor."""
        self.mode = mode

        if mode == EditorMode.VIEW:
            self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        elif mode == EditorMode.EDIT_TEXT:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)
        elif mode == EditorMode.ANNOTATE:
            self.setDragMode(QGraphicsView.DragMode.NoDrag)

        self.mode_changed.emit(mode.value)
        self.render_page()  # Re-render para actualizar interactividad

    # ─── RENDERING ────────────────────────────────────────────

    def render_page(self):
        """Renderiza la página actual a alta calidad."""
        if not self.doc:
            return

        try:
            page = self.doc.load_page(self.current_page_idx)

            # Renderizar siempre a zoom_factor × 72 DPI
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            fmt = QImage.Format.Format_RGB888
            qimg = QImage(pix.samples, pix.width, pix.height, pix.stride, fmt)
            qpixmap = QPixmap.fromImage(qimg.copy())

            self.pixmap_item.setPixmap(qpixmap)
            self.scene.setSceneRect(0, 0, pix.width, pix.height)

            # Solo mostrar bloques de texto cuando estamos en modo edición
            self._clear_overlays()
            if self.mode == EditorMode.EDIT_TEXT:
                self._render_text_blocks(page)

            # Emitir señales
            self.page_changed.emit(self.current_page_idx + 1, len(self.doc))
            self.zoom_changed.emit(int(self.zoom_factor * 100))

        except Exception as e:
            self.status_message.emit(f"❌ Error renderizando: {e}")

    def _clear_overlays(self):
        """Limpia todos los items excepto el pixmap principal."""
        for item in self.scene.items():
            if item != self.pixmap_item:
                self.scene.removeItem(item)

    def _render_text_blocks(self, page):
        """Renderiza bloques de texto interactivos con hover."""
        blocks = page.get_text("blocks")

        for b in blocks:
            x0, y0, x1, y1, text, block_no, block_type = b

            # Solo bloques de texto (type 0), no imágenes (type 1)
            if block_type != 0:
                continue

            # Escalar al zoom
            sx0 = x0 * self.zoom_factor
            sy0 = y0 * self.zoom_factor
            sw = (x1 - x0) * self.zoom_factor
            sh = (y1 - y0) * self.zoom_factor

            block = HoverableBlock(sx0, sy0, sw, sh, block_no, text, self)
            self.scene.addItem(block)

    # ─── TEXT EDITING ─────────────────────────────────────────

    def _block_rect(self, block_no):
        """Obtener fitz.Rect de un bloque por número."""
        if not self.doc:
            return fitz.Rect(0, 0, 100, 100)
        page = self.doc.load_page(self.current_page_idx)
        blocks = page.get_text("blocks")
        if block_no < len(blocks):
            return fitz.Rect(blocks[block_no][:4])
        return fitz.Rect(0, 0, 100, 100)

    def _apply_text_change(self, block_no, new_text, fontname=None, fontsize=None, color=None):
        """Reemplaza texto. Usa fuente del diálogo o detecta la original."""
        if not self.doc:
            return

        try:
            page = self.doc.load_page(self.current_page_idx)
            blocks = page.get_text("blocks")

            if block_no < len(blocks):
                b = blocks[block_no]
                rect = fitz.Rect(b[:4])

                # Usar params del diálogo, o detectar originales
                if fontname is None or fontsize is None or color is None:
                    font_info = self._get_block_font(page, rect)
                    fontname = fontname or font_info.get("font", "helv")
                    fontsize = fontsize or font_info.get("size", 11)
                    color = color or font_info.get("color", (0, 0, 0))

                # 1. Redactar viejo contenido
                page.add_redact_annot(rect, fill=(1, 1, 1))
                page.apply_redactions()

                # 2. Insertar nuevo texto con fuente elegida
                page.insert_textbox(
                    rect, new_text,
                    fontsize=fontsize,
                    fontname=fontname,
                    color=color,
                    align=fitz.TEXT_ALIGN_LEFT
                )

                self._has_unsaved_changes = True
                self.render_page()
                self.status_message.emit(f"✏️ Texto editado en bloque {block_no}")

        except Exception as e:
            self.status_message.emit(f"❌ Error editando texto: {e}")

    def _get_block_font(self, page, rect):
        """Detecta fuente, tamaño y color del primer span en el rect."""
        try:
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                if block.get("type") != 0:
                    continue
                block_rect = fitz.Rect(block["bbox"])
                if block_rect.intersects(rect):
                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            # Extraer color del int (sRGB packed)
                            c = span.get("color", 0)
                            r = ((c >> 16) & 0xFF) / 255.0
                            g = ((c >> 8) & 0xFF) / 255.0
                            b = (c & 0xFF) / 255.0
                            return {
                                "size": span.get("size", 11),
                                "font": "helv",  # PyMuPDF solo acepta built-in names para insert
                                "color": (r, g, b)
                            }
        except Exception:
            pass
        return {"size": 11, "font": "helv", "color": (0, 0, 0)}

    # ─── NAVIGATION ───────────────────────────────────────────

    def next_page(self):
        if self.doc and self.current_page_idx < len(self.doc) - 1:
            self.current_page_idx += 1
            self.render_page()

    def prev_page(self):
        if self.doc and self.current_page_idx > 0:
            self.current_page_idx -= 1
            self.render_page()

    def go_to_page(self, page_num: int):
        """Ir a una página específica (1-indexed)."""
        if self.doc and 1 <= page_num <= len(self.doc):
            self.current_page_idx = page_num - 1
            self.render_page()

    # ─── ZOOM ─────────────────────────────────────────────────

    def zoom_in(self):
        self.zoom_factor = min(5.0, self.zoom_factor * 1.15)
        self.render_page()

    def zoom_out(self):
        self.zoom_factor = max(0.3, self.zoom_factor / 1.15)
        self.render_page()

    def zoom_fit_width(self):
        """Ajustar zoom para que la página llene el ancho visible."""
        if not self.doc:
            return
        page = self.doc.load_page(self.current_page_idx)
        viewport_w = self.viewport().width() - 40  # margen
        page_w = page.rect.width
        self.zoom_factor = max(0.3, viewport_w / page_w)
        self.render_page()

    def zoom_reset(self):
        """Reset zoom a 100%."""
        self.zoom_factor = 1.0
        self.render_page()

    def wheelEvent(self, event: QWheelEvent):
        """Ctrl+Wheel = zoom, normal = scroll."""
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in()
            else:
                self.zoom_out()
            event.accept()
        else:
            super().wheelEvent(event)

    # ─── ANNOTATION TOOLS ─────────────────────────────────────

    def set_annotation_tool(self, tool_name):
        """Configura herramienta de anotación activa."""
        self._annotation_tool = tool_name

    def set_annotation_color(self, color):
        """Color para anotaciones (r,g,b) normalizado 0-1."""
        self._annotation_color = color

    def set_annotation_width(self, width):
        """Grosor de línea para dibujo libre."""
        self._annotation_width = width

    def apply_annotation_at(self, scene_pos, tool, **kwargs):
        """Aplica una anotación en la posición dada."""
        from ...core.annotations import (
            add_sticky_note, add_stamp, redact_area
        )
        if not self.doc:
            return

        page = self.doc.load_page(self.current_page_idx)

        # Convertir coordenadas de escena a coordenadas de página
        px = scene_pos.x() / self.zoom_factor
        py = scene_pos.y() / self.zoom_factor

        try:
            if tool == "sticky_note":
                text = kwargs.get("text", "Nota")
                add_sticky_note(page, (px, py), text)
                self.status_message.emit("📝 Nota adhesiva agregada")

            elif tool == "stamp":
                text = kwargs.get("stamp_text", "APROBADO")
                # Rectángulo centrado en el click
                rect = fitz.Rect(px - 80, py - 20, px + 80, py + 20)
                add_stamp(page, rect, text, color=self._annotation_color)
                self.status_message.emit(f"📌 Sello '{text}' aplicado")

            elif tool == "redact":
                # Rectángulo de redacción centrado en el click
                rect = fitz.Rect(px - 60, py - 10, px + 60, py + 10)
                redact_area(page, rect)
                self.status_message.emit("██ Área censurada")

            self._has_unsaved_changes = True
            self.render_page()

        except Exception as e:
            self.status_message.emit(f"❌ Error: {e}")

    def apply_text_markup(self, search_text, markup_type):
        """Aplica highlight/underline/strikeout a texto buscado."""
        from ...core.annotations import (
            add_highlight, add_underline, add_strikeout, search_text_quads
        )
        if not self.doc or not search_text.strip():
            return

        page = self.doc.load_page(self.current_page_idx)
        quads = search_text_quads(page, search_text)

        if not quads:
            self.status_message.emit(f"⚠️ Texto '{search_text}' no encontrado")
            return

        color = getattr(self, '_annotation_color', (1, 1, 0))

        if markup_type == "highlight":
            add_highlight(page, quads, color)
        elif markup_type == "underline":
            add_underline(page, quads, color)
        elif markup_type == "strikeout":
            add_strikeout(page, quads, color)

        self._has_unsaved_changes = True
        self.render_page()
        self.status_message.emit(f"🖍 {markup_type.title()} aplicado a '{search_text}'")

    def apply_watermark(self, text, opacity):
        """Aplicar marca de agua a todas las páginas."""
        from ...core.annotations import add_watermark_to_all
        if not self.doc:
            return
        try:
            add_watermark_to_all(self.doc, text, opacity=opacity)
            self._has_unsaved_changes = True
            self.render_page()
            self.status_message.emit(f"💧 Marca de agua '{text}' aplicada a todas las páginas")
        except Exception as e:
            self.status_message.emit(f"❌ Error en marca de agua: {e}")

    def insert_signature(self, image_path):
        """Insertar imagen de firma en el centro de la página."""
        from ...core.annotations import add_signature
        if not self.doc:
            return
        page = self.doc.load_page(self.current_page_idx)
        # Poner firma en la parte inferior-derecha
        pw = page.rect.width
        ph = page.rect.height
        rect = fitz.Rect(pw - 200, ph - 80, pw - 20, ph - 20)
        try:
            add_signature(page, rect, image_path)
            self._has_unsaved_changes = True
            self.render_page()
            self.status_message.emit("✒ Firma insertada")
        except Exception as e:
            self.status_message.emit(f"❌ Error insertando firma: {e}")

    # ─── FREEHAND DRAWING STATE ───────────────────────────────

    def _init_annotation_state(self):
        """Inicializar estado de anotación (llamado en __init__)."""
        self._annotation_tool = "highlight"
        self._annotation_color = (1, 1, 0)
        self._annotation_width = 2
        self._freehand_points = []  # puntos del trazo actual
        self._is_drawing = False

    # ─── MOUSE EVENTS ─────────────────────────────────────────

    def mousePressEvent(self, event):
        """Manejar clicks según modo."""
        if self.mode == EditorMode.ANNOTATE and event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            tool = getattr(self, '_annotation_tool', 'highlight')

            if tool == "freehand":
                self._is_drawing = True
                self._freehand_points = [(scene_pos.x(), scene_pos.y())]
            elif tool in ("sticky_note", "stamp", "redact"):
                self.apply_annotation_at(scene_pos, tool,
                    text=getattr(self, '_note_text', 'Nota'),
                    stamp_text=getattr(self, '_stamp_text', 'APROBADO')
                )
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if getattr(self, '_is_drawing', False):
            scene_pos = self.mapToScene(event.pos())
            self._freehand_points.append((scene_pos.x(), scene_pos.y()))
            # Visual feedback (QGraphicsPathItem en tiempo real se podría añadir)
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if getattr(self, '_is_drawing', False) and len(self._freehand_points) > 2:
            self._is_drawing = False
            # Convertir a coordenadas de página
            page_points = [
                (p[0] / self.zoom_factor, p[1] / self.zoom_factor)
                for p in self._freehand_points
            ]
            from ...core.annotations import add_freehand
            page = self.doc.load_page(self.current_page_idx)
            color = getattr(self, '_annotation_color', (0, 0, 0))
            width = getattr(self, '_annotation_width', 2)
            try:
                add_freehand(page, [page_points], color, width)
                self._has_unsaved_changes = True
                self.render_page()
                self.status_message.emit("✍ Trazo dibujado")
            except Exception as e:
                self.status_message.emit(f"❌ Error en dibujo: {e}")
            self._freehand_points = []
        else:
            self._is_drawing = False
            super().mouseReleaseEvent(event)
