from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget, QApplication
from PyQt6.QtCore import Qt, pyqtSignal, QMimeData, QPoint
from PyQt6.QtGui import QPixmap, QDrag
from ..style import AURORA

class PageThumbnail(QWidget):
    """Miniatura de una página PDF, seleccionable y arrastrable."""

    clicked = pyqtSignal(int, object)  # (page_num, modifiers)
    double_clicked = pyqtSignal(int)   # (page_num)

    def __init__(self, page_num: int, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.selected = False
        self._pixmap = pixmap # Keep reference for drag preview
        self._drag_start_pos = None
        self._setup_ui(pixmap)

    def _setup_ui(self, pixmap: QPixmap):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Imagen de la página
        self.img_label = QLabel()
        self.img_label.setPixmap(
            pixmap.scaled(120, 160, Qt.AspectRatioMode.KeepAspectRatio,
                         Qt.TransformationMode.SmoothTransformation)
        )
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.img_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {AURORA['border']};
                border-radius: 4px;
                background: {AURORA['bg_surface']};
                padding: 4px;
            }}
        """)

        # Número de página
        self.num_label = QLabel(f"Pág. {self.page_num}")
        self.num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.num_label.setStyleSheet(f"color: {AURORA['text_secondary']}; font-size: 10px;")

        layout.addWidget(self.img_label)
        layout.addWidget(self.num_label)

    def set_selected(self, selected: bool):
        self.selected = selected
        color = AURORA['accent_orange'] if selected else AURORA['border']
        self.img_label.setStyleSheet(f"""
            QLabel {{
                border: 2px solid {color};
                border-radius: 4px;
                background: {AURORA['bg_surface']};
                padding: 4px;
            }}
        """)
        if selected:
            self.num_label.setStyleSheet(
                f"color: {AURORA['accent_orange']}; font-size: 10px; font-weight: bold;"
            )
        else:
            self.num_label.setStyleSheet(f"color: {AURORA['text_secondary']}; font-size: 10px;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.pos()
            self.clicked.emit(self.page_num, event.modifiers())
        else:
            self._drag_start_pos = None

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton):
            return
        if not self._drag_start_pos:
            return

        dist = (event.pos() - self._drag_start_pos).manhattanLength()
        if dist < QApplication.startDragDistance():
            return

        self._start_drag()

    def _start_drag(self):
        drag = QDrag(self)
        mime = QMimeData()
        
        # Usamos texto plano para el número de página, o un formato custom
        mime.setText(str(self.page_num))
        mime.setData("application/x-page-thumbnail", str(self.page_num).encode('utf-8'))
        
        drag.setMimeData(mime)
        
        # Preview visual
        preview = self._pixmap.scaled(100, 140, Qt.AspectRatioMode.KeepAspectRatio)
        drag.setPixmap(preview)
        drag.setHotSpot(QPoint(preview.width() // 2, preview.height() // 2))
        
        drag.exec(Qt.DropAction.MoveAction)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.page_num)
