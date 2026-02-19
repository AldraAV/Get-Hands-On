
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from pathlib import Path
from ..style import AURORA, FONTS

class DropArea(QWidget):
    """Widget para drag & drop de archivos con estilo Aurora"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setMinimumSize(300, 180)
        
        layout = QVBoxLayout()
        self.label = QLabel("🖐️ Arrastra PDFs aquí\no haz clic para seleccionar")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label.setFont(parent.font() if parent else None)
        
        # Estilo inicial
        self.reset_style()
        
        layout.addWidget(self.label)
        self.setLayout(layout)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.select_files()
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.label.setStyleSheet(f"""
                QLabel {{
                    border: 2px solid {AURORA['accent_orange']};
                    background-color: {AURORA['bg_elevated']};
                    color: {AURORA['accent_orange']};
                    border-radius: 10px;
                    padding: 20px;
                    font-size: 14pt;
                }}
            """)
    
    def dragLeaveEvent(self, event):
        self.reset_style()
        
    def dropEvent(self, event: QDropEvent):
        files = [Path(url.toLocalFile()) for url in event.mimeData().urls()]
        pdf_files = [f for f in files if f.suffix.lower() == '.pdf']
        
        if pdf_files:
            self.files_dropped.emit(pdf_files)
        
        self.reset_style()
    
    def reset_style(self):
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.label.setStyleSheet(f"""
            QLabel {{
                border: 2px dashed #666;
                border-radius: 10px;
                background-color: {AURORA['bg_surface']};
                padding: 20px;
                font-size: 14pt;
                color: #888;
            }}
            QLabel:hover {{
                background-color: {AURORA['bg_elevated']};
                border-color: {AURORA['accent_orange']};
                color: {AURORA['text_primary']};
            }}
        """)
    
    def select_files(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Seleccionar PDFs",
            "",
            "PDF Files (*.pdf)"
        )
        if files:
            self.files_dropped.emit([Path(f) for f in files])
