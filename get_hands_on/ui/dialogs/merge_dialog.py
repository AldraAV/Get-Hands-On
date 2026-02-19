
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QLineEdit, QListWidget, QAbstractItemView)
from pathlib import Path
from ..style import AURORA

class MergeDialog(QDialog):
    def __init__(self, parent=None, files=[]):
        super().__init__(parent)
        self.setWindowTitle(f"🔗 Unir PDFs")
        self.setMinimumSize(400, 500)
        self.setStyleSheet(f"""
            QDialog {{ background-color: {AURORA['bg_deep']}; color: {AURORA['text_primary']}; }}
            QLabel {{ color: {AURORA['text_primary']}; }}
        """)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Orden de unión (arrastra para reordenar):"))
        
        self.file_list = QListWidget()
        self.file_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        for f in files:
            self.file_list.addItem(f.name)
        
        # Guardar lista original para mapear nombres a paths si hay duplicados
        # (Para MVP asumimos nombres únicos o mapeamos por índice si no se borra)
        self.original_files = files 
        
        layout.addWidget(self.file_list)
        
        layout.addWidget(QLabel("Nombre del archivo de salida:"))
        self.output_name = QLineEdit("unido.pdf")
        layout.addWidget(self.output_name)
        
        # Botones
        btn_layout = QHBoxLayout()
        self.btn_cancel = QPushButton("Cancelar")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_ok = QPushButton("Unir")
        self.btn_ok.setProperty("class", "primary")
        self.btn_ok.clicked.connect(self.accept)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_ok)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def get_data(self):
        # Reconstruir orden basado en la lista visual
        ordered_files = []
        for i in range(self.file_list.count()):
            name = self.file_list.item(i).text()
            # Buscar el path correspondiente (simple match por nombre para MVP)
            for f in self.original_files:
                if f.name == name:
                    ordered_files.append(f)
                    break
        
        return {
            'files': ordered_files,
            'filename': self.output_name.text()
        }
