
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QComboBox, QLineEdit, QSpinBox)
from ..style import AURORA
from ...core.pdf_ops import SplitMode

class SplitDialog(QDialog):
    def __init__(self, parent=None, filename=""):
        super().__init__(parent)
        self.setWindowTitle(f"🔪 Separar: {filename}")
        self.setMinimumWidth(400)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {AURORA['bg_deep']}; color: {AURORA['text_primary']}; }}
            QLabel {{ color: {AURORA['text_primary']}; }}
        """)
        
        layout = QVBoxLayout()
        
        # Modo
        layout.addWidget(QLabel("Modo de separación:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Todas las páginas (1 archivo x página)",
            "Rango (ej: 1-5)",
            "Paginas específicas (ej: 1,3,5)",
            "Por bloques (ej: cada 10 págs)"
        ])
        self.mode_combo.currentIndexChanged.connect(self.update_inputs)
        layout.addWidget(self.mode_combo)
        
        # Inputs dinámicos
        self.input_frame = QVBoxLayout()
        
        # Rango
        self.range_input = QLineEdit()
        self.range_input.setPlaceholderText("Ej: 1-5")
        self.range_input.hide()
        
        # Específico
        self.specific_input = QLineEdit()
        self.specific_input.setPlaceholderText("Ej: 1,3,5,8")
        self.specific_input.hide()
        
        # Chunks
        self.chunk_spin = QSpinBox()
        self.chunk_spin.setMinimum(1)
        self.chunk_spin.setValue(10)
        self.chunk_spin.setSuffix(" páginas")
        self.chunk_spin.hide()
        
        layout.addLayout(self.input_frame)
        layout.addWidget(self.range_input)
        layout.addWidget(self.specific_input)
        layout.addWidget(self.chunk_spin)
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("Separar")
        self.btn_ok.setProperty("class", "primary")
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def update_inputs(self, index):
        self.range_input.hide()
        self.specific_input.hide()
        self.chunk_spin.hide()
        
        if index == 1: # Range
            self.range_input.show()
        elif index == 2: # Specific
            self.specific_input.show()
        elif index == 3: # Chunks
            self.chunk_spin.show()

    def get_data(self):
        idx = self.mode_combo.currentIndex()
        if idx == 0: return {'mode': SplitMode.ALL}
        if idx == 1:
            try:
                start, end = map(int, self.range_input.text().split('-'))
                return {'mode': SplitMode.RANGE, 'range': (start, end)}
            except: return None
        if idx == 2:
            try:
                pages = [int(p.strip()) for p in self.specific_input.text().split(',')]
                return {'mode': SplitMode.SPECIFIC, 'pages': pages}
            except: return None
        if idx == 3:
            return {'mode': SplitMode.CHUNKS, 'chunk_size': self.chunk_spin.value()}
        return None
