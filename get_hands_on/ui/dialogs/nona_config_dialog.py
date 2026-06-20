from PyQt6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QLabel, QLineEdit
)
from PyQt6.QtCore import Qt, QSettings
from qfluentwidgets import MessageBoxBase, SubtitleLabel, PushButton

class NonaConfigDialog(MessageBoxBase):
    """Diálogo para configurar el GROQ_API_KEY persistentemente usando QSettings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel('Configuración de Nona (Groq)', self)
        self.yesButton.setText('Guardar')
        self.cancelButton.setText('Cancelar')

        self.api_key_input = QLineEdit(self)
        self.api_key_input.setPlaceholderText("gsk_...")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setMinimumWidth(300)

        # Cargar llave guardada
        self.settings = QSettings("Aldra", "MeterMano")
        saved_key = self.settings.value("GROQ_API_KEY", "")
        if saved_key:
            self.api_key_input.setText(saved_key)

        # Añadir al layout
        self.viewLayout.addWidget(self.titleLabel)
        
        info = QLabel("El API Key de Groq es necesario para que Nona procese tus instrucciones.")
        info.setWordWrap(True)
        self.viewLayout.addWidget(info)
        
        self.viewLayout.addWidget(self.api_key_input)

    def get_api_key(self):
        return self.api_key_input.text().strip()

    def validate(self) -> bool:
        """Llamado cuando el usuario hace clic en Aceptar."""
        key = self.get_api_key()
        if not key:
            self.api_key_input.setStyleSheet("border: 1px solid red;")
            return False
        
        # Guardar en QSettings
        self.settings.setValue("GROQ_API_KEY", key)
        return True
