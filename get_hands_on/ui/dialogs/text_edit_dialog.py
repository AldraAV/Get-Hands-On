"""
text_edit_dialog.py — Diálogo avanzado de edición de texto PDF.
Soporta selección de fuente, tamaño, color y preview en tiempo real.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QPlainTextEdit, QComboBox, QSpinBox, QColorDialog, QFrame,
    QGroupBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QTextCharFormat
from ..style import AURORA


# Fuentes built-in de PyMuPDF que siempre funcionan
PYMUPDF_FONTS = {
    "Helvetica": "helv",
    "Helvetica Bold": "hebo",
    "Helvetica Italic": "heit",
    "Helvetica Bold Italic": "hebi",
    "Courier": "cour",
    "Courier Bold": "cobo",
    "Courier Italic": "coit",
    "Courier Bold Italic": "cobi",
    "Times Roman": "tiro",
    "Times Bold": "tibo",
    "Times Italic": "tiit",
    "Times Bold Italic": "tibi",
    "Symbol": "symb",
    "ZapfDingbats": "zadb",
}


class TextEditDialog(QDialog):
    """Diálogo de edición de texto avanzado con fuente, tamaño y color."""

    def __init__(self, current_text, font_info=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️ Editar Texto")
        self.setMinimumSize(600, 450)
        self.new_text = None
        self.font_name = "helv"
        self.font_size = 11
        self.text_color = (0, 0, 0)

        # Aplicar info de fuente detectada
        if font_info:
            self.font_name = font_info.get("font", "helv")
            self.font_size = font_info.get("size", 11)
            c = font_info.get("color", (0, 0, 0))
            self.text_color = (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))

        self._setup_style()
        self._setup_ui(current_text)

    def _setup_style(self):
        self.setStyleSheet(f"""
            QDialog {{
                background: {AURORA['bg_surface']};
                border: 1px solid {AURORA['border']};
            }}
            QLabel {{
                color: {AURORA['text_primary']};
                font-size: 11px;
            }}
            QPlainTextEdit {{
                background: {AURORA['bg_deep']};
                color: {AURORA['text_primary']};
                border: 1px solid {AURORA['border']};
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
            }}
            QPushButton {{
                background: {AURORA['bg_elevated']};
                color: {AURORA['text_primary']};
                border: 1px solid {AURORA['border']};
                border-radius: 4px;
                padding: 6px 14px;
                font-size: 11px;
            }}
            QPushButton:hover {{
                border-color: {AURORA['accent_orange']};
            }}
            QComboBox, QSpinBox {{
                background: {AURORA['bg_deep']};
                color: {AURORA['text_primary']};
                border: 1px solid {AURORA['border']};
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 11px;
                min-height: 24px;
            }}
            QGroupBox {{
                color: {AURORA['accent_orange']};
                font-weight: bold;
                font-size: 11px;
                border: 1px solid {AURORA['border']};
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 16px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }}
        """)

    def _setup_ui(self, text):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # ── FONT CONTROLS GROUP ────────────────────────
        font_group = QGroupBox("Tipografía")
        font_layout = QHBoxLayout(font_group)
        font_layout.setSpacing(8)

        # Fuente
        font_layout.addWidget(QLabel("Fuente:"))
        self.combo_font = QComboBox()
        self.combo_font.addItems(PYMUPDF_FONTS.keys())
        # Seleccionar fuente detectada
        detected_display = self._find_font_display(self.font_name)
        if detected_display:
            self.combo_font.setCurrentText(detected_display)
        self.combo_font.setMinimumWidth(160)
        self.combo_font.currentTextChanged.connect(self._on_font_changed)
        font_layout.addWidget(self.combo_font)

        # Tamaño
        font_layout.addWidget(QLabel("Tamaño:"))
        self.spin_size = QSpinBox()
        self.spin_size.setRange(6, 72)
        self.spin_size.setValue(int(self.font_size))
        self.spin_size.setFixedWidth(65)
        self.spin_size.valueChanged.connect(self._on_size_changed)
        font_layout.addWidget(self.spin_size)

        # Color
        font_layout.addWidget(QLabel("Color:"))
        self.btn_color = QPushButton()
        self.btn_color.setFixedSize(28, 28)
        self._update_color_button()
        self.btn_color.clicked.connect(self._pick_color)
        font_layout.addWidget(self.btn_color)

        font_layout.addStretch()
        layout.addWidget(font_group)

        # ── INFO LABEL ─────────────────────────────────
        self.lbl_info = QLabel("")
        self.lbl_info.setStyleSheet(f"color: {AURORA['text_secondary']}; font-size: 10px;")
        self._update_info()
        layout.addWidget(self.lbl_info)

        # ── TEXT EDITOR ────────────────────────────────
        self.editor = QPlainTextEdit()
        self.editor.setPlainText(text)
        self._apply_editor_font()
        layout.addWidget(self.editor, stretch=1)

        # ── BUTTONS ────────────────────────────────────
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        btn_cancel = QPushButton("Cancelar")
        btn_cancel.clicked.connect(self.reject)

        btn_reset = QPushButton("↺ Reset")
        btn_reset.setToolTip("Restaurar texto original")
        btn_reset.clicked.connect(lambda: self.editor.setPlainText(text))

        btn_save = QPushButton("💾 Aplicar Cambios")
        btn_save.setStyleSheet(
            f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;"
        )
        btn_save.clicked.connect(self.accept_changes)

        btn_layout.addStretch()
        btn_layout.addWidget(btn_cancel)
        btn_layout.addWidget(btn_reset)
        btn_layout.addWidget(btn_save)

        layout.addLayout(btn_layout)

    def _find_font_display(self, internal_name):
        """Buscar nombre de display para fuente interna."""
        for display, internal in PYMUPDF_FONTS.items():
            if internal == internal_name:
                return display
        return None

    def _on_font_changed(self, display_name):
        self.font_name = PYMUPDF_FONTS.get(display_name, "helv")
        self._apply_editor_font()
        self._update_info()

    def _on_size_changed(self, size):
        self.font_size = size
        self._apply_editor_font()
        self._update_info()

    def _pick_color(self):
        color = QColorDialog.getColor(QColor(*self.text_color), self, "Color del Texto")
        if color.isValid():
            self.text_color = (color.red(), color.green(), color.blue())
            self._update_color_button()
            self._update_info()

    def _update_color_button(self):
        r, g, b = self.text_color
        self.btn_color.setStyleSheet(f"""
            QPushButton {{
                background: rgb({r},{g},{b});
                border: 2px solid {AURORA['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {AURORA['accent_orange']};
            }}
        """)

    def _apply_editor_font(self):
        """Actualizar fuente del editor para preview."""
        display_name = self.combo_font.currentText()

        # Mapear a fuentes del sistema para preview
        family_map = {
            "Helvetica": "Arial",
            "Courier": "Courier New",
            "Times Roman": "Times New Roman",
            "Symbol": "Symbol",
            "ZapfDingbats": "Wingdings",
        }

        base = display_name.split(" ")[0] if " " in display_name else display_name
        family = family_map.get(base, "Arial")

        font = QFont(family, self.spin_size.value())
        if "Bold" in display_name:
            font.setBold(True)
        if "Italic" in display_name:
            font.setItalic(True)

        self.editor.setFont(font)

        # Color del texto
        r, g, b = self.text_color
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {AURORA['bg_deep']};
                color: rgb({r},{g},{b});
                border: 1px solid {AURORA['border']};
                border-radius: 4px;
                padding: 8px;
            }}
        """)

    def _update_info(self):
        display = self.combo_font.currentText()
        self.lbl_info.setText(
            f"→ PyMuPDF: {self.font_name} | {self.font_size}pt | "
            f"RGB({self.text_color[0]},{self.text_color[1]},{self.text_color[2]})")

    def accept_changes(self):
        self.new_text = self.editor.toPlainText()
        self.font_size = self.spin_size.value()
        self.accept()

    def get_color_normalized(self):
        """Color normalizado 0-1 para PyMuPDF."""
        return (self.text_color[0] / 255, self.text_color[1] / 255, self.text_color[2] / 255)
