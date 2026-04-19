from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QAbstractItemView
from qfluentwidgets import MessageBoxBase, LineEdit, SubtitleLabel, ListWidget
from pathlib import Path

class MergeDialog(MessageBoxBase):
    def __init__(self, parent=None, files=[]):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("🔗 Unir PDFs", self)
        
        self.viewLayout.setSpacing(12)
        self.viewLayout.addWidget(self.titleLabel)
        
        self.viewLayout.addWidget(QLabel("Orden de unión (arrastra para reordenar):"))
        
        self.file_list = ListWidget(self)
        self.file_list.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        for f in files:
            self.file_list.addItem(f.name)
        
        self.original_files = files 
        
        self.viewLayout.addWidget(self.file_list)
        
        self.viewLayout.addWidget(QLabel("Nombre del archivo de salida:"))
        self.output_name = LineEdit(self)
        self.output_name.setText("unido.pdf")
        self.viewLayout.addWidget(self.output_name)
        
        self.widget.setMinimumWidth(380)
        
        self.yesButton.setText("Unir")
        self.cancelButton.setText("Cancelar")

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
