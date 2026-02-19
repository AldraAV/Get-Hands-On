
from PyQt6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from ..style import AURORA

class PageThumbnail(QWidget):
    """Miniatura de una página PDF, seleccionable."""

    clicked = pyqtSignal(int, object)  # (page_num, modifiers)
    double_clicked = pyqtSignal(int)   # (page_num)

    def __init__(self, page_num: int, pixmap: QPixmap, parent=None):
        super().__init__(parent)
        self.page_num = page_num
        self.selected = False
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
            self.clicked.emit(self.page_num, event.modifiers())

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.double_clicked.emit(self.page_num)
