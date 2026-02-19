"""
annotation_toolbar.py — Panel lateral de herramientas de anotación.
Aparece cuando el editor está en modo ANNOTATE.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLabel, QComboBox, QSpinBox, QColorDialog, QFrame,
    QSlider, QLineEdit
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from ..style import AURORA


class ColorButton(QPushButton):
    """Botón que muestra un color y abre un picker al hacer clic."""
    color_changed = pyqtSignal(tuple)

    def __init__(self, initial_color=(255, 255, 0), parent=None):
        super().__init__(parent)
        self.setFixedSize(28, 28)
        self._color = initial_color
        self._update_style()

    def _update_style(self):
        r, g, b = self._color
        self.setStyleSheet(f"""
            QPushButton {{
                background: rgb({r},{g},{b});
                border: 2px solid {AURORA['border']};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border-color: {AURORA['accent_orange']};
            }}
        """)

    def mousePressEvent(self, event):
        color = QColorDialog.getColor(QColor(*self._color), self, "Elegir Color")
        if color.isValid():
            self._color = (color.red(), color.green(), color.blue())
            self._update_style()
            self.color_changed.emit(self._color)

    @property
    def color_tuple(self):
        """Color normalizado 0-1 para PyMuPDF."""
        return (self._color[0] / 255.0, self._color[1] / 255.0, self._color[2] / 255.0)

    @property
    def color_rgb(self):
        return self._color


class AnnotationToolbar(QWidget):
    """Panel lateral con herramientas de anotación."""

    tool_selected = pyqtSignal(str)          # nombre de herramienta
    color_selected = pyqtSignal(tuple)       # (r, g, b) normalizado 0-1
    stamp_text_selected = pyqtSignal(str)    # texto del sello
    line_width_changed = pyqtSignal(int)     # grosor de línea
    watermark_requested = pyqtSignal(str, float)  # texto, opacidad
    signature_requested = pyqtSignal()
    note_text_entered = pyqtSignal(str)      # texto de nota

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(220)
        self.current_tool = "highlight"
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.setStyleSheet(f"""
            QWidget {{
                background: {AURORA['bg_elevated']};
                color: {AURORA['text_primary']};
            }}
            QPushButton {{
                text-align: left;
                padding: 6px 10px;
                border-radius: 4px;
                border: 1px solid transparent;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background: {AURORA['bg_surface']};
                border-color: {AURORA['border']};
            }}
            QLabel {{
                font-size: 10px;
                color: {AURORA['text_secondary']};
            }}
            QComboBox, QSpinBox, QLineEdit {{
                background: {AURORA['bg_surface']};
                border: 1px solid {AURORA['border']};
                border-radius: 4px;
                padding: 4px;
                color: {AURORA['text_primary']};
                font-size: 11px;
            }}
        """)

        # ── TÍTULO ─────────────────────────────────────
        title = QLabel("HERRAMIENTAS")
        title.setStyleSheet(f"""
            color: {AURORA['accent_orange']};
            font-weight: bold;
            font-size: 11px;
            letter-spacing: 2px;
            padding: 4px 0;
        """)
        layout.addWidget(title)

        # ── MARKUP TOOLS ───────────────────────────────
        self._add_section_label(layout, "Marcado de Texto")

        self.btn_highlight = self._add_tool_button(layout, "🖍 Resaltar", "highlight")
        self.btn_underline = self._add_tool_button(layout, "__ Subrayar", "underline")
        self.btn_strikeout = self._add_tool_button(layout, "~~ Tachar", "strikeout")

        # Color picker para marcado
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Color:"))
        self.markup_color = ColorButton((255, 255, 0))
        self.markup_color.color_changed.connect(
            lambda c: self.color_selected.emit(self.markup_color.color_tuple)
        )
        color_row.addWidget(self.markup_color)

        # Colores rápidos
        for rgb, name in [((255, 255, 0), "Amarillo"), ((0, 255, 0), "Verde"),
                          ((0, 200, 255), "Azul"), ((255, 150, 200), "Rosa")]:
            btn = QPushButton()
            btn.setFixedSize(22, 22)
            r, g, b = rgb
            btn.setStyleSheet(f"background: rgb({r},{g},{b}); border-radius: 3px; border: 1px solid {AURORA['border']};")
            btn.setToolTip(name)
            btn.clicked.connect(lambda checked, c=rgb: self._quick_color(c))
            color_row.addWidget(btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        # Separador
        self._add_separator(layout)

        # ── NOTES ──────────────────────────────────────
        self._add_section_label(layout, "Notas")
        self.btn_sticky = self._add_tool_button(layout, "📝 Nota adhesiva", "sticky_note")

        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Texto de la nota...")
        self.note_input.setFixedHeight(28)
        layout.addWidget(self.note_input)

        # Separador
        self._add_separator(layout)

        # ── DRAWING ────────────────────────────────────
        self._add_section_label(layout, "Dibujo")
        self.btn_freehand = self._add_tool_button(layout, "✍ Dibujo libre", "freehand")

        width_row = QHBoxLayout()
        width_row.addWidget(QLabel("Grosor:"))
        self.line_width = QSpinBox()
        self.line_width.setRange(1, 10)
        self.line_width.setValue(2)
        self.line_width.setFixedWidth(60)
        self.line_width.valueChanged.connect(self.line_width_changed.emit)
        width_row.addWidget(self.line_width)
        width_row.addStretch()
        layout.addLayout(width_row)

        # Separador
        self._add_separator(layout)

        # ── STAMPS ─────────────────────────────────────
        self._add_section_label(layout, "Sellos")
        self.btn_stamp = self._add_tool_button(layout, "📌 Sello", "stamp")

        self.stamp_combo = QComboBox()
        self.stamp_combo.addItems([
            "APROBADO", "RECHAZADO", "CONFIDENCIAL",
            "BORRADOR", "FINAL", "COPIA", "REVISADO", "URGENTE"
        ])
        self.stamp_combo.currentTextChanged.connect(self.stamp_text_selected.emit)
        layout.addWidget(self.stamp_combo)

        # Separador
        self._add_separator(layout)

        # ── SIGNATURE ──────────────────────────────────
        self._add_section_label(layout, "Firma")
        btn_sig = QPushButton("✒ Insertar firma (imagen)")
        btn_sig.clicked.connect(self.signature_requested.emit)
        layout.addWidget(btn_sig)

        # Separador
        self._add_separator(layout)

        # ── WATERMARK ──────────────────────────────────
        self._add_section_label(layout, "Marca de Agua")

        self.wm_input = QLineEdit()
        self.wm_input.setPlaceholderText("Texto...")
        self.wm_input.setText("CONFIDENCIAL")
        layout.addWidget(self.wm_input)

        wm_row = QHBoxLayout()
        wm_row.addWidget(QLabel("Opacidad:"))
        self.wm_opacity = QSlider(Qt.Orientation.Horizontal)
        self.wm_opacity.setRange(10, 90)
        self.wm_opacity.setValue(30)
        self.wm_opacity.setFixedWidth(80)
        wm_row.addWidget(self.wm_opacity)
        self.wm_label = QLabel("30%")
        self.wm_opacity.valueChanged.connect(lambda v: self.wm_label.setText(f"{v}%"))
        wm_row.addWidget(self.wm_label)
        layout.addLayout(wm_row)

        btn_wm = QPushButton("💧 Aplicar Marca de Agua")
        btn_wm.setStyleSheet(f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;")
        btn_wm.clicked.connect(lambda: self.watermark_requested.emit(
            self.wm_input.text(), self.wm_opacity.value() / 100.0
        ))
        layout.addWidget(btn_wm)

        # Separador
        self._add_separator(layout)

        # ── REDACTION ──────────────────────────────────
        self._add_section_label(layout, "Redacción")
        self.btn_redact = self._add_tool_button(layout, "██ Censurar área", "redact")

        layout.addStretch()

        # Seleccionar highlight por defecto
        self._select_tool("highlight")

    def _add_section_label(self, layout, text):
        lbl = QLabel(text.upper())
        lbl.setStyleSheet(f"""
            color: {AURORA['text_secondary']};
            font-size: 9px;
            font-weight: bold;
            letter-spacing: 1px;
            padding-top: 4px;
        """)
        layout.addWidget(lbl)

    def _add_separator(self, layout):
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"border: 1px solid {AURORA['border']};")
        sep.setFixedHeight(1)
        layout.addWidget(sep)

    def _add_tool_button(self, layout, text, tool_name):
        btn = QPushButton(text)
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self._select_tool(tool_name))
        layout.addWidget(btn)
        return btn

    def _select_tool(self, tool_name):
        self.current_tool = tool_name

        # Deseleccionar todos
        for btn in [self.btn_highlight, self.btn_underline, self.btn_strikeout,
                     self.btn_sticky, self.btn_freehand, self.btn_stamp, self.btn_redact]:
            btn.setChecked(False)
            btn.setStyleSheet("")

        # Seleccionar activo
        active_style = f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;"
        tool_map = {
            "highlight": self.btn_highlight,
            "underline": self.btn_underline,
            "strikeout": self.btn_strikeout,
            "sticky_note": self.btn_sticky,
            "freehand": self.btn_freehand,
            "stamp": self.btn_stamp,
            "redact": self.btn_redact,
        }
        if tool_name in tool_map:
            tool_map[tool_name].setChecked(True)
            tool_map[tool_name].setStyleSheet(active_style)

        self.tool_selected.emit(tool_name)

    def _quick_color(self, rgb):
        self.markup_color._color = rgb
        self.markup_color._update_style()
        self.color_selected.emit(self.markup_color.color_tuple)

    def get_note_text(self):
        return self.note_input.text() or "Nota"

    def get_stamp_text(self):
        return self.stamp_combo.currentText()

    def get_line_width(self):
        return self.line_width.value()

    def get_markup_color(self):
        return self.markup_color.color_tuple
