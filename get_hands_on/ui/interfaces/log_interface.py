from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt
from ..components.log_panel import LogPanel
from ..style import AURORA

class LogInterface(QWidget):
    """Interfaz de historial y log de actividad."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Título
        self.title = QLabel("Historial de Actividad", self)
        self.title.setStyleSheet(f"font-size: 24px; font-weight: bold; color: {AURORA['accent_orange']}; margin-bottom: 10px;")
        self.layout.addWidget(self.title)
        
        # Log Panel
        self.log_panel = LogPanel(self)
        self.log_panel.setMaximumHeight(10000) # Dejar que ocupe todo el espacio
        self.layout.addWidget(self.log_panel)
        
        self.layout.addStretch(1)
        
        # Estilo
        self.setObjectName("LogInterface")

    def append_msg(self, msg):
        self.log_panel.append_msg(msg)

    def append_special(self, msg):
        self.log_panel.append_special(msg)
