
AURORA = {
    "bg_deep":      "#0D0D0D",
    "bg_surface":   "#1A1A1A",
    "bg_elevated":  "#242424",
    "accent_orange":"#FF7A18",
    "accent_amber": "#F59E0B",
    "accent_red":   "#B91C1C",
    "text_primary": "#F8F8F8",
    "text_secondary":"#A8A29E",
    "border":       "#2E2E2E",
    "success":      "#22C55E",
    "glow_orange":  "rgba(255, 122, 24, 0.15)",
}

FONTS = {
    "display":  "Segoe UI",
    "body":     "Segoe UI",
    "mono":     "Consolas",
    "size_xs":  9,
    "size_sm":  10,
    "size_md":  12,
    "size_lg":  14,
    "size_xl":  18,
    "size_xxl": 24,
}

GLOBAL_STYLE = """
    QMainWindow, QDialog, QWidget {
        background-color: #0D0D0D;
        color: #F8F8F8;
        font-family: 'Segoe UI';
        font-size: 12px;
    }
    QPushButton {
        background-color: #1A1A1A;
        color: #F8F8F8;
        border: 1px solid #2E2E2E;
        border-radius: 6px;
        padding: 8px 16px;
        font-size: 12px;
    }
    QPushButton:hover {
        background-color: #242424;
        border-color: #FF7A18;
        color: #FF7A18;
    }
    QPushButton.primary {
        background-color: #FF7A18;
        color: #0D0D0D;
        border: none;
        font-weight: bold;
    }
    QPushButton.primary:hover {
        background-color: #e86d10;
    }
    QPushButton:disabled {
        background-color: #151515;
        color: #555555;
        border-color: #2E2E2E;
    }
    QPushButton.danger {
        border-color: #B91C1C;
        color: #B91C1C;
    }
    QListWidget, QTextEdit, QLineEdit {
        background-color: #1A1A1A;
        border: 1px solid #2E2E2E;
        border-radius: 6px;
        padding: 6px;
        color: #F8F8F8;
    }
    QListWidget::item:selected {
        background-color: rgba(255, 122, 24, 0.2);
        color: #FF7A18;
    }
    QScrollBar:vertical {
        background: #1A1A1A;
        width: 6px;
        border-radius: 3px;
    }
    QScrollBar::handle:vertical {
        background: #FF7A18;
        border-radius: 3px;
    }
    QLabel.section-title {
        color: #FF7A18;
        font-weight: bold;
        font-size: 11px;
        letter-spacing: 1px;
    }
    QProgressBar {
        background-color: #1A1A1A;
        border: 1px solid #2E2E2E;
        border-radius: 4px;
        height: 6px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #FF7A18;
        border-radius: 4px;
    }
"""
