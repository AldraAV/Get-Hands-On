from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QLabel, QWidget, QStackedWidget
from qfluentwidgets import (
    MessageBoxBase, ComboBox, LineEdit, SpinBox, DoubleSpinBox, 
    SubtitleLabel, Pivot
)

class WatermarkDialog(MessageBoxBase):
    """Diálogo unificado para Marca de Agua + Numeración de páginas + Encabezado/Pie construido en Fluent."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.titleLabel = SubtitleLabel("Configuración de Páginas", self)
        self.viewLayout.setSpacing(12)
        self.viewLayout.addWidget(self.titleLabel)

        self.pivot = Pivot(self)
        self.stackedWidget = QStackedWidget(self)

        self._build_watermark_tab()
        self._build_pagenumber_tab()
        self._build_headerfooter_tab()

        self.viewLayout.addWidget(self.pivot)
        self.viewLayout.addWidget(self.stackedWidget)

        self.widget.setMinimumWidth(440)
        self.yesButton.setText("Aplicar")
        self.cancelButton.setText("Cancelar")
        
        self.pivot.setCurrentItem(self.wm_tab.objectName())
        self.stackedWidget.setCurrentWidget(self.wm_tab)
        
        self.pivot.currentItemChanged.connect(
            lambda k: self.stackedWidget.setCurrentWidget(self.findChild(QWidget, k))
        )

    def _add_to_pivot(self, widget, name, text):
        widget.setObjectName(name)
        self.stackedWidget.addWidget(widget)
        self.pivot.addItem(
            routeKey=name,
            text=text,
            onClick=lambda: self.stackedWidget.setCurrentWidget(widget)
        )

    def _build_watermark_tab(self):
        self.wm_tab = QWidget()
        layout = QVBoxLayout(self.wm_tab)
        layout.setContentsMargins(0, 10, 0, 0)

        layout.addWidget(QLabel("Texto de la marca de agua:"))
        self.wm_text = LineEdit()
        self.wm_text.setText("CONFIDENCIAL")
        layout.addWidget(self.wm_text)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Tamaño de fuente:"))
        self.wm_font_size = SpinBox()
        self.wm_font_size.setRange(20, 200)
        self.wm_font_size.setValue(60)
        row1.addWidget(self.wm_font_size)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Ángulo (°):"))
        self.wm_angle = SpinBox()
        self.wm_angle.setRange(0, 360)
        self.wm_angle.setValue(45)
        row2.addWidget(self.wm_angle)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Opacidad (0.0 – 1.0):"))
        self.wm_opacity = DoubleSpinBox()
        self.wm_opacity.setRange(0.05, 1.0)
        self.wm_opacity.setSingleStep(0.05)
        self.wm_opacity.setValue(0.15)
        row3.addWidget(self.wm_opacity)
        layout.addLayout(row3)

        self._add_to_pivot(self.wm_tab, "watermark", "🔒 Marca de agua")

    def _build_pagenumber_tab(self):
        self.pn_tab = QWidget()
        layout = QVBoxLayout(self.pn_tab)
        layout.setContentsMargins(0, 10, 0, 0)

        layout.addWidget(QLabel("Posición:"))
        self.pn_position = ComboBox()
        self.pn_position.addItems([
            "bottom-center", "bottom-left", "bottom-right",
            "top-center", "top-left", "top-right"
        ])
        layout.addWidget(self.pn_position)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Prefijo:"))
        self.pn_prefix = LineEdit()
        self.pn_prefix.setText("Pág. ")
        row1.addWidget(self.pn_prefix)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Sufijo:"))
        self.pn_suffix = LineEdit()
        row2.addWidget(self.pn_suffix)
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Empezar en:"))
        self.pn_start = SpinBox()
        self.pn_start.setRange(0, 9999)
        self.pn_start.setValue(1)
        row3.addWidget(self.pn_start)
        layout.addLayout(row3)

        self._add_to_pivot(self.pn_tab, "pagenumber", "🔢 Numeración")

    def _build_headerfooter_tab(self):
        self.hf_tab = QWidget()
        layout = QVBoxLayout(self.hf_tab)
        layout.setContentsMargins(0, 10, 0, 0)

        layout.addWidget(QLabel("Encabezado (vacío = no usar):"))
        self.hf_header = LineEdit()
        self.hf_header.setPlaceholderText("ej. Proyecto Clasificado")
        layout.addWidget(self.hf_header)

        layout.addWidget(QLabel("Pie de página (usa {page} y {total}):"))
        self.hf_footer = LineEdit()
        self.hf_footer.setText("Página {page} de {total}")
        layout.addWidget(self.hf_footer)

        self._add_to_pivot(self.hf_tab, "headerfooter", "📄 Encabezado/Pie")

    @property
    def tabs(self):
        # Wrapper for backward compatibility with main_window.py
        class DummyTabs:
            @staticmethod
            def setCurrentIndex(index):
                keys = ["watermark", "pagenumber", "headerfooter"]
                if 0 <= index < len(keys):
                    self.pivot.setCurrentItem(keys[index])
        return DummyTabs()

    def get_mode(self) -> str:
        """Retorna la pestaña activa."""
        return self.pivot.currentItem().routeKey()

    def get_watermark_params(self) -> dict:
        return {
            "text": self.wm_text.text() or "CONFIDENCIAL",
            "opacity": self.wm_opacity.value(),
            "angle": self.wm_angle.value(),
            "font_size": self.wm_font_size.value(),
        }

    def get_pagenumber_params(self) -> dict:
        return {
            "position": self.pn_position.currentText(),
            "prefix": self.pn_prefix.text(),
            "suffix": self.pn_suffix.text(),
            "start_page": self.pn_start.value(),
        }

    def get_headerfooter_params(self) -> dict:
        return {
            "header_text": self.hf_header.text(),
            "footer_text": self.hf_footer.text(),
        }
