# style.py

# Paleta "Adobe Killer" Premium
AURORA = {
    "bg_deep":      "#0F0F11",   # Fondo de la aplicación (muy oscuro, no negro puro)
    "bg_surface":   "#18181A",   # Fondo de las tarjetas/paneles (ligeramente elevado)
    "bg_elevated":  "#27272A",   # Botones y elementos activos
    "accent_orange":"#FF6B00",   # Naranja vibrante y profesional
    "accent_amber": "#F59E0B",
    "accent_red":   "#EF4444",   # Rojo moderno para peligro/eliminar
    "text_primary": "#F4F4F5",   # Texto principal (blanco suave)
    "text_secondary":"#A1A1AA",  # Texto secundario (gris)
    "border":       "#323238",   # Bordes sutiles
    "success":      "#10B981",
    "glow_orange":  "rgba(255, 107, 0, 0.12)",
}

FONTS = {
    "display":  "Segoe UI Variable Display, Segoe UI, sans-serif",
    "body":     "Segoe UI Variable Text, Segoe UI, sans-serif",
    "mono":     "Consolas",
    "size_xs":  10,
    "size_sm":  11,
    "size_md":  13,
    "size_lg":  15,
    "size_xl":  18,
    "size_xxl": 24,
}

GLOBAL_STYLE = f"""
    QMainWindow, QDialog, QWidget {{
        background-color: {AURORA['bg_deep']};
        color: {AURORA['text_primary']};
        font-family: 'Segoe UI Variable Text', 'Segoe UI';
        font-size: 13px;
    }}
    
    /* Scrollbars elegantes */
    QScrollBar:vertical {{
        background: {AURORA['bg_deep']};
        width: 8px;
        margin: 0px 0px 0px 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {AURORA['bg_elevated']};
        min-height: 20px;
        border-radius: 4px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {AURORA['border']};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    
    QScrollBar:horizontal {{
        background: {AURORA['bg_deep']};
        height: 8px;
        margin: 0px 0px 0px 0px;
        border-radius: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {AURORA['bg_elevated']};
        min-width: 20px;
        border-radius: 4px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* Botones Base */
    QPushButton {{
        background-color: {AURORA['bg_surface']};
        color: {AURORA['text_primary']};
        border: 1px solid {AURORA['border']};
        border-radius: 6px;
        padding: 8px 16px;
        font-weight: 500;
    }}
    QPushButton:hover {{
        background-color: {AURORA['bg_elevated']};
        border-color: {AURORA['accent_orange']};
        color: {AURORA['accent_orange']};
    }}
    QPushButton:pressed {{
        background-color: {AURORA['bg_surface']};
        border-color: {AURORA['accent_orange']};
    }}
    QPushButton:disabled {{
        background-color: {AURORA['bg_surface']};
        color: #52525B; /* gray-600 */
        border-color: {AURORA['bg_surface']};
    }}
    
    /* Boton Primario (Destacado) */
    QPushButton.primary {{
        background-color: {AURORA['accent_orange']};
        color: #FFFFFF;
        border: none;
        font-weight: bold;
    }}
    QPushButton.primary:hover {{
        background-color: #E85E00;
    }}
    QPushButton.primary:pressed {{
        background-color: #CC5300;
    }}
    
    /* Botones Peligro (Eliminar) */
    QPushButton.danger {{
        border-color: {AURORA['border']};
        color: {AURORA['accent_red']};
    }}
    QPushButton.danger:hover {{
        background-color: rgba(239, 68, 68, 0.1);
        border-color: {AURORA['accent_red']};
    }}
    
    /* Boton "Batch" Especial */
    QPushButton.batch {{
        background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {AURORA['bg_surface']}, stop:1 {AURORA['bg_elevated']});
        border-color: {AURORA['accent_amber']};
        color: {AURORA['accent_amber']};
    }}
    QPushButton.batch:hover {{
        background-color: rgba(245, 158, 11, 0.15);
    }}

    /* Inputs y Listas */
    QListWidget, QTextEdit, QLineEdit {{
        background-color: {AURORA['bg_surface']};
        border: 1px solid {AURORA['border']};
        border-radius: 6px;
        padding: 8px;
        color: {AURORA['text_primary']};
        outline: none;
    }}
    QLineEdit:focus, QTextEdit:focus, QListWidget:focus {{
        border: 1px solid {AURORA['accent_orange']};
    }}
    QListWidget::item {{
        border-radius: 4px;
        padding: 4px;
        margin: 2px 0px;
    }}
    QListWidget::item:hover {{
        background-color: {AURORA['bg_elevated']};
    }}
    QListWidget::item:selected {{
        background-color: {AURORA['glow_orange']};
        color: {AURORA['accent_orange']};
        font-weight: bold;
    }}

    /* Títulos de sección */
    QLabel.section-title {{
        color: {AURORA['text_secondary']};
        font-weight: 600;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}
    
    /* Título destacado (como en operaciones) */
    QLabel.section-title-accent {{
        color: {AURORA['accent_orange']};
        font-weight: bold;
        font-size: 11px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 4px;
    }}

    /* Progress Bar */
    QProgressBar {{
        background-color: {AURORA['bg_surface']};
        border: 1px solid {AURORA['border']};
        border-radius: 4px;
        height: 6px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {AURORA['accent_orange']};
        border-radius: 4px;
    }}
    
    /* Componentes de Grupo */
    QGroupBox {{
        border: 1px solid {AURORA['border']};
        border-radius: 6px;
        margin-top: 1ex;
        padding-top: 10px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top center;
        padding: 0 5px;
        color: {AURORA['text_secondary']};
        font-size: 12px;
    }}
"""
