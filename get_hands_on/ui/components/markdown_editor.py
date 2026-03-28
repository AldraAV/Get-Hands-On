import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, 
    QPlainTextEdit, QTextBrowser, QPushButton, QLabel, 
    QFileDialog, QMessageBox, QFrame, QSizePolicy
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QTextDocument

from ..style import AURORA
from ...core.markdown_ops import parse_pdf_to_md, export_html_to_pdf

class MarkdownEditor(QWidget):
    """
    Componente Estilo Obsidian (Split-View)
    Panel Izquierdo: Editor Texto crudo (Markdown)
    Panel Derecho: Renderizado en vivo HTML/CSS
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_filename = "Sin Titulo"
        self.init_ui()
        self.connect_signals()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # --- TOPBAR ---
        toolbar = QWidget()
        toolbar.setFixedHeight(48)
        toolbar.setStyleSheet(f"""
            QWidget {{
                background: {AURORA['bg_elevated']};
                border-bottom: 1px solid {AURORA['border']};
            }}
            QPushButton {{
                padding: 6px 14px;
                font-weight: 600;
                font-size: 11px;
                border-radius: 4px;
                background: {AURORA['bg_deep']};
                border: 1px solid {AURORA['border']};
                color: {AURORA['text_primary']};
            }}
            QPushButton:hover {{
                border: 1px solid {AURORA['accent_orange']};
                color: {AURORA['accent_orange']};
            }}
        """)
        h_layout = QHBoxLayout(toolbar)
        h_layout.setContentsMargins(10, 5, 10, 5)
        
        # Etiqueta Archivo
        self.lbl_file = QLabel(self.current_filename)
        self.lbl_file.setStyleSheet(f"color: {AURORA['accent_amber']}; font-weight: bold;")
        
        # Acciones
        self.btn_back = QPushButton("⬅ Volver")
        self.btn_back.clicked.connect(self._go_back)
        self.btn_back.setStyleSheet(f"background: transparent; color: {AURORA['accent_orange']}; font-weight: bold; border: none; font-size: 13px;")
        
        self.btn_load_md = QPushButton("📂 Abrir .MD")
        self.btn_extract_pdf = QPushButton("🪄 Extraer desde PDF")
        self.btn_save_md = QPushButton("💾 Guardar .MD")
        self.btn_export_pdf = QPushButton("⬇️ Exportar a PDF")
        self.btn_export_pdf.setStyleSheet(f"""
            background: {AURORA['accent_orange']}; 
            color: #111; border: none; font-weight: bold;
        """)
        
        h_layout.addWidget(self.btn_back)
        h_layout.addSpacing(10)
        h_layout.addWidget(self.btn_load_md)
        h_layout.addWidget(self.btn_extract_pdf)
        h_layout.addWidget(self.btn_save_md)
        
        # Spacer
        h_layout.addStretch()
        h_layout.addWidget(self.lbl_file)
        h_layout.addStretch()
        
        h_layout.addWidget(self.btn_export_pdf)
        
        main_layout.addWidget(toolbar)
        
        # --- SPLITTER AREA ---
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {AURORA['border']};
                width: 2px;
            }}
        """)
        
        # PANEL IZQ: Raw Markdown
        self.editor = QPlainTextEdit()
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.editor.setFont(font)
        self.editor.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {AURORA['bg_deep']};
                color: {AURORA['text_primary']};
                border: none;
                padding: 10px;
                selection-background-color: {AURORA['accent_orange']};
            }}
        """)
        self.editor.setPlaceholderText("# Escribe o pega tu Markdown aquí...\nO presiona el botón de 'Extraer desde PDF'.")
        
        # PANEL DER: HTML Preview
        self.preview = QTextBrowser()
        self.preview.setStyleSheet(f"""
            QTextBrowser {{
                background: {AURORA['bg_surface']};
                color: {AURORA['text_primary']};
                border: none;
                padding: 15px;
            }}
        """)
        self.preview.setOpenExternalLinks(True)
        
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.preview)
        self.splitter.setSizes([500, 500])
        
        main_layout.addWidget(self.splitter)
        
    def connect_signals(self):
        self.editor.textChanged.connect(self.update_preview)
        
        self.btn_load_md.clicked.connect(self.load_markdown)
        self.btn_save_md.clicked.connect(self.save_markdown)
        self.btn_extract_pdf.clicked.connect(self.extract_pdf)
        self.btn_export_pdf.clicked.connect(self.export_to_pdf)
        
    def _generate_styled_html(self, text: str) -> str:
        # QTextDocument internamente procesa Markdown a HTML pero a veces no pone CSS Global
        # Aquí forzamos nuestro theme básico
        doc = QTextDocument()
        doc.setDefaultFont(QFont("Segoe UI", 11))
        doc.setMarkdown(text)
        raw_html = doc.toHtml()
        
        # Inyectar CSS
        css = f"""
        <style>
            body {{
                font-family: 'Segoe UI', system-ui, sans-serif;
                color: {AURORA['text_primary']};
                line-height: 1.6;
                margin: 0;
            }}
            h1, h2, h3 {{ color: {AURORA['accent_orange']}; font-weight: bold; border-bottom: 1px solid {AURORA['border']}; padding-bottom: 5px; }}
            h1 {{ font-size: 24pt; }}
            h2 {{ font-size: 20pt; }}
            h3 {{ font-size: 16pt; }}
            a {{ color: {AURORA['accent_amber']}; text-decoration: none; }}
            code {{ background-color: #333; padding: 2px 4px; border-radius: 3px; font-family: Consolas, monospace; }}
            pre {{ background-color: #222; padding: 10px; border-radius: 5px; overflow-x: auto; }}
            blockquote {{ border-left: 4px solid {AURORA['accent_orange']}; margin: 0; padding-left: 10px; color: #aaa; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid {AURORA['border']}; padding: 8px; }}
            th {{ background-color: #333; }}
        </style>
        """
        # Insertar style en head o antes del body
        if "<head>" in raw_html:
            return raw_html.replace("<head>", f"<head>\n{css}")
        else:
            return f"<html><head>{css}</head><body>{raw_html}</body></html>"
            
    def _go_back(self):
        main = self.window()
        if hasattr(main, "stack"):
            main.stack.setCurrentIndex(0)

    def update_preview(self):
        text = self.editor.toPlainText()
        html = self._generate_styled_html(text)
        self.preview.setHtml(html)
        
    def load_markdown(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Abrir archivo Markdown o Texto", "", 
            "Text Files (*.md *.txt);;All Files (*.*)"
        )
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.editor.setPlainText(content)
                self.current_filename = os.path.basename(file_path)
                self.lbl_file.setText(self.current_filename)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Fallo al leer archivo:\n{e}")

    def save_markdown(self):
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Sin contenido", "El editor está vacío.")
            return

        default_name = self.current_filename.rsplit('.', 1)[0] + ".md"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como Markdown", default_name,
            "Markdown Files (*.md);;Text Files (*.txt);;All Files (*.*)"
        )
        if save_path:
            try:
                with open(save_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                self.current_filename = os.path.basename(save_path)
                self.lbl_file.setText(self.current_filename)
                QMessageBox.information(self, "Guardado", f"Archivo guardado:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error al guardar", f"No se pudo escribir el archivo:\n{e}")

    def extract_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Extraer texto de un PDF a Markdown", "", 
            "PDF Files (*.pdf)"
        )
        if file_path:
            self.editor.setPlainText("Procesando PDF con PyMuPDF (Leyendo geometría de fuentes)...")
            self.lbl_file.setText(f"Extracción de: {os.path.basename(file_path)}")
            # Realizar extraction síncrona (es rápida) o worker (mejor asíncrono para docs grandes)
            # Como es un MVP, bloquearemos brevemente
            md_content = parse_pdf_to_md(file_path)
            self.editor.setPlainText(md_content)

    def export_to_pdf(self):
        text = self.editor.toPlainText()
        if not text.strip():
            QMessageBox.warning(self, "Documento Vacío", "No hay nada para exportar.")
            return
            
        default_name = self.current_filename.rsplit('.', 1)[0] + "_Estilizado.pdf"
        save_path, _ = QFileDialog.getSaveFileName(
            self, "Guardar como PDF Estilizado", default_name,
            "PDF Files (*.pdf)"
        )
        
        if save_path:
            html = self._generate_styled_html(text)
            try:
                success = export_html_to_pdf(html, save_path)
                if success:
                    QMessageBox.information(self, "Éxito", "PDF guardado y renderizado con CSS.")
            except Exception as e:
                QMessageBox.critical(self, "Error de Exportación", f"El motor falló:\n{e}")
