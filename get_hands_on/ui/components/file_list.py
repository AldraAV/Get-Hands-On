
from PyQt6.QtWidgets import QListWidget
from pathlib import Path
from ..style import AURORA

class FileList(QListWidget):
    """Lista de archivos cargados"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {AURORA['bg_surface']};
                border: 1px solid {AURORA['border']};
                border-radius: 6px;
                padding: 6px;
                color: {AURORA['text_primary']};
                font-size: 13px;
                outline: none;
            }}
            QListWidget::item {{
                padding: 5px;
                border-bottom: 1px solid {AURORA['bg_deep']};
            }}
            QListWidget::item:selected {{
                background-color: {AURORA['glow_orange']};
                color: {AURORA['accent_orange']};
                border-radius: 4px;
                border: 1px solid {AURORA['accent_orange']};
            }}
            QListWidget::item:hover:!selected {{
                background-color: {AURORA['bg_elevated']};
            }}
        """)

    def add_file(self, path: Path):
        # Evitar duplicados visuales simples (aunque la lógica de negocio puede manejarlos)
        # Aquí permitimos todo, la lógica de main window controla.
        self.addItem(f"{path.name}  [{self._get_size(path)}]")

    def _get_size(self, path: Path):
        try:
            size = path.stat().st_size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} TB"
        except:
            return "?"
