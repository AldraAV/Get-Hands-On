from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
from qfluentwidgets import PushButton, PrimaryPushButton, FluentIcon as FIF
from .log_panel import LogPanel
from ...workers.nona_worker import NonaWorker
import os

class NonaSurgeonWidget(QWidget):
    """Panel de interacción con Nona (Groq) y el MCP del Cirujano."""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.worker = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Título
        title_lbl = QLabel("🍒 Nona - Cirugía Autónoma (MCP)")
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #EA580C;")
        layout.addWidget(title_lbl)

        # Instrucciones
        info_lbl = QLabel(
            "Escribe qué deseas hacer con el documento actual.\n"
            "Ejemplo: 'Dime qué imágenes tiene este documento' o 'Cambia el estilo del título a color rojo'."
        )
        info_lbl.setStyleSheet("color: #A8A29E;")
        layout.addWidget(info_lbl)

        # Área de input
        input_layout = QHBoxLayout()
        self.prompt_input = QLineEdit()
        self.prompt_input.setPlaceholderText("Escribe tu instrucción para Nona...")
        self.prompt_input.setMinimumHeight(40)
        
        self.btn_send = PrimaryPushButton(FIF.SEND, "Ejecutar")
        self.btn_send.setMinimumHeight(40)
        self.btn_send.clicked.connect(self.run_nona)
        
        input_layout.addWidget(self.prompt_input, stretch=1)
        input_layout.addWidget(self.btn_send)
        
        layout.addLayout(input_layout)

        # Área de Log
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet(
            "background-color: #1E1E1E; color: #E5E7EB; "
            "font-family: Consolas, monospace; font-size: 13px; "
            "border: 1px solid #374151; border-radius: 5px; padding: 10px;"
        )
        layout.addWidget(self.log_area, stretch=1)

    def append_log(self, text: str):
        self.log_area.append(text)

    def append_error(self, text: str):
        self.log_area.append(f"<span style='color: #EF4444;'>❌ ERROR: {text}</span>")

    def run_nona(self):
        prompt = self.prompt_input.text().strip()
        if not prompt:
            return
            
        doc_path = self.main_window._get_current_real_file()
        if not doc_path:
            self.append_error("No hay un documento PDF o DOCX seleccionado en el Dashboard.")
            return

        self.prompt_input.clear()
        self.append_log(f"\n<span style='color: #3B82F6;'>Usuario:</span> {prompt}")
        
        # Iniciar Worker
        self.btn_send.setEnabled(False)
        self.worker = NonaWorker(document_path=str(doc_path), user_prompt=prompt)
        
        # Conectar señales
        self.worker.log_signal.connect(self.append_log)
        self.worker.error_signal.connect(self.append_error)
        self.worker.finished_signal.connect(self.on_worker_finished)
        
        self.worker.start()

    def on_worker_finished(self):
        self.btn_send.setEnabled(True)
        self.append_log("--- Fin de la operación ---")
