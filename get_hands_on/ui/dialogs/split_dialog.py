from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget, QLabel
from qfluentwidgets import MessageBoxBase, ComboBox, LineEdit, SpinBox, SubtitleLabel
from ...core.pdf_ops import SplitMode

class SplitDialog(MessageBoxBase):
    def __init__(self, parent=None, filename=""):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel(f"🔪 Separar: {filename}", self)
        
        # Añadir márgenes visuales extras al layout de vista interno si es necesario
        self.viewLayout.setSpacing(12)
        
        self.viewLayout.addWidget(self.titleLabel)
        
        self.mode_combo = ComboBox(self)
        self.mode_combo.addItems([
            "Todas las páginas (1 archivo x página)",
            "Rango (ej: 1-5)",
            "Paginas específicas (ej: 1,3,5)",
            "Por bloques (ej: cada 10 págs)"
        ])
        self.mode_combo.currentIndexChanged.connect(self.update_inputs)
        
        self.viewLayout.addWidget(QLabel("Modo de separación:"))
        self.viewLayout.addWidget(self.mode_combo)
        
        # Contenedor dinámico (Inputs)
        self.input_frame = QWidget(self)
        self.input_layout = QVBoxLayout(self.input_frame)
        self.input_layout.setContentsMargins(0, 0, 0, 0)
        
        self.range_input = LineEdit(self)
        self.range_input.setPlaceholderText("Ej: 1-5")
        self.range_input.hide()
        
        self.specific_input = LineEdit(self)
        self.specific_input.setPlaceholderText("Ej: 1,3,5,8")
        self.specific_input.hide()
        
        self.chunk_spin = SpinBox(self)
        self.chunk_spin.setMinimum(1)
        self.chunk_spin.setValue(10)
        self.chunk_spin.setSuffix(" páginas")
        self.chunk_spin.hide()
        
        self.input_layout.addWidget(self.range_input)
        self.input_layout.addWidget(self.specific_input)
        self.input_layout.addWidget(self.chunk_spin)
        
        self.viewLayout.addWidget(self.input_frame)

        self.widget.setMinimumWidth(380)

        # Botones nativos del Box
        self.yesButton.setText("Separar")
        self.cancelButton.setText("Cancelar")

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
