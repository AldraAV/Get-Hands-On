
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtCore import Qt
import datetime
from ..style import AURORA, FONTS

class LogPanel(QTextEdit):
    """Panel de logs con soporte para estilos Aurora y Easter Egg"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumHeight(150)
        self.setStyleSheet(f"""
            QTextEdit {{
                background-color: {AURORA['bg_surface']};
                border: 1px solid {AURORA['border']};
                border-radius: 6px;
                padding: 8px;
                color: {AURORA['text_primary']};
                font-family: 'Consolas', monospace;
                font-size: 11px;
            }}
        """)
    
    def append_msg(self, msg: str):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.append(f"<span style='color:{AURORA['text_secondary']};'>[{timestamp}]</span> {msg}")
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())

    def append_special(self, msg: str):
        """Para mensajes importantes o Easter Eggs"""
        self.append(f"<div style='color:{AURORA['accent_orange']}; font-weight:bold; margin-top:5px; margin-bottom:5px;'>{msg}</div>")
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
