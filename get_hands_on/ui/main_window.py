
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QFileDialog, QMessageBox,
    QSplitter, QStackedWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pathlib import Path
import sys

from qfluentwidgets import (
    FluentWindow, FluentIcon as FIF,
    NavigationItemPosition,
    PushButton, PrimaryPushButton, TransparentPushButton,
)

from .style import AURORA, GLOBAL_STYLE, FONTS
from .components.drop_area import DropArea
from .components.file_list import FileList
from .components.log_panel import LogPanel
from .components.pages_panel import PagesPanel
from .components.markdown_editor import MarkdownEditor
from .components.document_canvas import DocumentCanvas
from .components.annotation_toolbar import AnnotationToolbar
from .dialogs.split_dialog import SplitDialog
from .dialogs.merge_dialog import MergeDialog
from .dialogs.watermark_dialog import WatermarkDialog
from .interfaces.log_interface import LogInterface
from ..workers.task_worker import TaskWorker
from ..core.pdf_ops import split_pdf, merge_pdfs, rotate_pages, extract_pages, delete_pages, duplicate_pages, insert_blank_page, move_page, reorder_pages
from ..core.converters import pdf_to_word, pdf_to_images, images_to_pdf, compress_pdf, ocr_pdf
from ..core.security import encrypt_pdf, decrypt_pdf
from ..core.batch import batch_apply, BatchOp
from ..core.table_export import extract_tables_to_csv, extract_tables_to_xlsx
from ..core.watermark import add_watermark_clean, add_page_numbers, add_header_footer


class MainWindow(FluentWindow):
    """Ventana principal de Get Hands-On — Fluent Design Aurora."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Get Hands-On")
        self.resize(1200, 780)

        import tempfile
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_files = {} # Dict[Path, Path] mapping file->temp buffer

        # Icono
        icon_path = Path(__file__).parent.parent / 'resources' / 'icon.png'
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Estado
        self.loaded_files = []
        self.worker = None
        self.selected_pages = []

        # Crear widgets de contenido
        self.dashboard = QWidget()
        self.dashboard.setObjectName("dashboardInterface")

        self.editor = QWidget()
        self.editor.setObjectName("editorInterface")

        self.md_editor = MarkdownEditor(self)
        self.md_editor.setObjectName("mdEditorInterface")

        self.log_interface = LogInterface(self)
        self.log_interface.setObjectName("logInterface")
        
        # Redirigir self.log_panel para mensajes de sistema (retrocompatibilidad)
        self.log = self.log_interface

        self.init_ui()
        self._connect_signals()
    
    def init_ui(self):
        # Dashboard: Editor PDF principal
        self._setup_dashboard()
        self.addSubInterface(self.dashboard, FIF.DOCUMENT, "Editor PDF")

        # Editor: Canvas de anotaciones
        self._setup_editor()
        self.addSubInterface(self.editor, FIF.EDIT, "Anotar / Ver")

        # MD Editor: Markdown <-> PDF
        self.addSubInterface(self.md_editor, FIF.BOOK_SHELF, "Markdown")

        # Log de Actividad (Nuevos logs irán aquí)
        self.addSubInterface(self.log_interface, FIF.HISTORY, "Historial")

        # Herramientas de Documentación (Integradas en Sidebar)
        self.navigationInterface.addSeparator()
        
        self.navigationInterface.addItem(
            routeKey="watermark",
            icon=FIF.TAG,
            text="Marca de Agua",
            onClick=self.run_watermark,
            selectable=False
        )
        self.navigationInterface.addItem(
            routeKey="numbering",
            icon=FIF.SEND,
            text="Numeración / Footer",
            onClick=self.run_page_numbers,
            selectable=False
        )
        self.navigationInterface.addItem(
            routeKey="tables",
            icon=FIF.TILES,
            text="Exportar Tablas",
            onClick=self.run_export_tables,
            selectable=False
        )

        # Ítem inferior: Acerca de
        self.navigationInterface.addItem(
            routeKey="about",
            icon=FIF.INFO,
            text="Acerca de",
            onClick=self._show_about,
            selectable=False,
            position=NavigationItemPosition.BOTTOM,
        )

        # Navegar al dashboard al inicio
        self.switchTo(self.dashboard)

    def _setup_dashboard(self):
        # Layout principal del dashboard
        main_layout = QHBoxLayout(self.dashboard)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- PANEL IZQUIERDO (Archivos + Páginas + Log) ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(10, 10, 10, 10)
        
        # Drop area (fija arriba)
        self.drop_area = DropArea(self)
        self.drop_area.files_dropped.connect(self.add_files)
        left_layout.addWidget(self.drop_area)
              # Splitter vertical para lista de archivos y visor de páginas
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setHandleWidth(2)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {AURORA['border']}; }}")
        
        # 1. Lista de Archivos
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(0,0,0,0)
        list_label = QLabel("ARCHIVOS CARGADOS")
        list_label.setProperty("class", "section-title")
        files_layout.addWidget(list_label)
        self.file_list = FileList(self)
        files_layout.addWidget(self.file_list)
        splitter.addWidget(files_widget)
        
        # 2. Panel de Páginas (Vista previa)
        pages_widget = QWidget()
        pages_layout = QVBoxLayout(pages_widget)
        pages_layout.setContentsMargins(0,0,0,0)
        self.pages_panel = PagesPanel(self)
        pages_layout.addWidget(self.pages_panel)
        splitter.addWidget(pages_widget)

        splitter.setSizes([300, 450])
        left_layout.addWidget(splitter)
        
        main_layout.addWidget(left_widget, stretch=6)
        
        # Separador vertical
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.VLine)
        sep.setStyleSheet(f"color: {AURORA['border']};")
        main_layout.addWidget(sep)
        
        # --- PANEL DERECHO (Operaciones) ---
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(20, 20, 20, 20)
        
        ops_title = QLabel("OPERACIONES")
        ops_title.setProperty("class", "section-title")
        ops_title.setStyleSheet("font-size: 14px; margin-bottom: 10px;")
        right_panel.addWidget(ops_title)
        
        # Botones Principales (Operaciones)
        self.btn_split = PushButton("🔪 Separar páginas")
        self.btn_split.clicked.connect(self.open_split_dialog)
        
        self.btn_merge = PrimaryPushButton("🔗 Unir PDFs (Merge)")
        self.btn_merge.clicked.connect(self.open_merge_dialog)
        
        self.btn_rotate = PushButton("↻  Rotar páginas")
        self.btn_rotate.clicked.connect(self.run_rotate)
        self.btn_rotate.setEnabled(False) 
        
        self.btn_extract = PushButton("📄 Extraer páginas")
        self.btn_extract.clicked.connect(self.run_extract)
        self.btn_extract.setEnabled(False) 
        
        self.btn_delete = PushButton("🗑️  Eliminar páginas")
        self.btn_delete.clicked.connect(self.run_delete)
        self.btn_delete.setEnabled(False) 
        
        self.btn_edit = PrimaryPushButton("✏️ Editor")
        self.btn_edit.clicked.connect(self.open_editor)
        self.btn_edit.setEnabled(False)
        
        self.btn_save_mem = PrimaryPushButton("💾 Guardar Cambios")
        self.btn_save_mem.clicked.connect(self.run_save_memory)
        self.btn_save_mem.setEnabled(False)
        self.btn_save_mem.setStyleSheet(f"background: #059669; color: white; border: none; font-weight: bold;") # Green

        for btn in [self.btn_split, self.btn_merge, self.btn_rotate, self.btn_extract, self.btn_delete, self.btn_edit, self.btn_save_mem]:
            right_panel.addWidget(btn)
            right_panel.addSpacing(5)

        # ── SECCIÓN: CONVERSIONES ──────────────────────────
        conv_sep = QFrame()
        conv_sep.setFrameShape(QFrame.Shape.HLine)
        conv_sep.setStyleSheet(f"color: {AURORA['border']};")
        right_panel.addWidget(conv_sep)
        right_panel.addSpacing(5)

        conv_title = QLabel("CONVERSIONES")
        conv_title.setProperty("class", "section-title")
        conv_title.setStyleSheet("font-size: 13px; margin-bottom: 6px;")
        right_panel.addWidget(conv_title)

        self.btn_to_word = PushButton("📝 PDF → Word")
        self.btn_to_word.clicked.connect(self.run_pdf_to_word)

        self.btn_to_images = PushButton("🖼️ PDF → Imágenes")
        self.btn_to_images.clicked.connect(self.run_pdf_to_images)

        self.btn_from_images = PushButton("📸 Imágenes → PDF")
        self.btn_from_images.clicked.connect(self.run_images_to_pdf)

        self.btn_compress = PushButton("🗜️ Comprimir PDF")
        self.btn_compress.clicked.connect(self.run_compress)

        self.btn_md_editor = PushButton("📝 Editor Markdown")
        self.btn_md_editor.clicked.connect(self.open_md_editor)
        self.btn_md_editor.setStyleSheet(f"background: {AURORA['bg_elevated']}; color: {AURORA['accent_orange']}; font-weight: bold;")

        for btn in [self.btn_to_word, self.btn_to_images, self.btn_from_images, self.btn_compress, self.btn_md_editor]:
            right_panel.addWidget(btn)
            right_panel.addSpacing(4)

        self.btn_ocr = PushButton("\U0001f50d Texto Seleccionable (OCR)")
        self.btn_ocr.clicked.connect(self.run_ocr)
        right_panel.addWidget(self.btn_ocr)
        right_panel.addSpacing(4)

        # \u2500\u2500 SECCI\u00d3N: SEGURIDAD \u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500\u2500
        sec_sep = QFrame()
        sec_sep.setFrameShape(QFrame.Shape.HLine)
        sec_sep.setStyleSheet(f"color: {AURORA['border']};")
        right_panel.addWidget(sec_sep)
        right_panel.addSpacing(5)

        sec_title = QLabel("SEGURIDAD")
        sec_title.setProperty("class", "section-title")
        sec_title.setStyleSheet("font-size: 13px; margin-bottom: 6px;")
        right_panel.addWidget(sec_title)

        self.btn_encrypt = PushButton(FIF.IOT, "Proteger con password")
        self.btn_encrypt.setMinimumHeight(40)
        self.btn_encrypt.clicked.connect(self.run_encrypt)
        self.btn_encrypt.setToolTip("Cifra el PDF con AES-256")

        self.btn_decrypt = PushButton(FIF.VIEW, "Desbloquear PDF")
        self.btn_decrypt.setMinimumHeight(40)
        self.btn_decrypt.clicked.connect(self.run_decrypt)
        self.btn_decrypt.setToolTip("Remueve la protección por password")

        for btn in [self.btn_encrypt, self.btn_decrypt]:
            right_panel.addWidget(btn)
            right_panel.addSpacing(4)

        # ── SECCIÓN: BATCH ───────────────────────────────────────────────────
        batch_sep = QFrame()
        batch_sep.setFrameShape(QFrame.Shape.HLine)
        batch_sep.setStyleSheet(f"color: {AURORA['border']};")
        right_panel.addWidget(batch_sep)
        right_panel.addSpacing(5)

        self.btn_batch = PushButton(FIF.COMMAND_PROMPT, "Procesamiento por lotes")
        self.btn_batch.setMinimumHeight(45)
        self.btn_batch.clicked.connect(self.run_batch)
        self.btn_batch.setStyleSheet(f"background: {AURORA['bg_surface']}; border: 1px solid {AURORA['accent_orange']}; color: {AURORA['accent_orange']}; font-weight: bold;")
        self.btn_batch.setToolTip("Aplica la misma operación a múltiples PDFs de un jalón")
        right_panel.addWidget(self.btn_batch)

        right_panel.addStretch()
        
        footer = QLabel("☀️ Por Aldra\nLe meto mano a tus PDFs 🔧")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setWordWrap(False)
        footer.setMinimumWidth(220)
        footer.setStyleSheet(f"color: {AURORA['accent_orange']}; font-style: italic; opacity: 0.8;")
        right_panel.addWidget(footer)
        
        main_layout.addLayout(right_panel, stretch=4)

    def _setup_editor(self):
        # Initialize Canvas first
        from .components.document_canvas import EditorMode
        self.canvas = DocumentCanvas(self)

        layout = QVBoxLayout(self.editor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # ── TOOLBAR PRINCIPAL ──────────────────────────────
        toolbar_widget = QWidget()
        toolbar_widget.setFixedHeight(48)
        toolbar_widget.setStyleSheet(f"""
            QWidget {{
                background: {AURORA['bg_elevated']};
                border-bottom: 1px solid {AURORA['border']};
            }}
            PushButton, PrimaryPushButton {{
                padding: 4px 10px;
                font-size: 11px;
                min-height: 28px;
                border-radius: 4px;
            }}
            QLabel {{
                font-size: 11px;
            }}
        """)
        toolbar = QHBoxLayout(toolbar_widget)
        toolbar.setContentsMargins(8, 4, 8, 4)
        toolbar.setSpacing(4)

        # Volver
        btn_back = PushButton(FIF.LEFT_ARROW, "Volver")
        btn_back.clicked.connect(self.close_editor)
        btn_back.setFixedWidth(100)
        toolbar.addWidget(btn_back)

        # Separador
        self._add_separator(toolbar)

        # Nombre del archivo
        self.lbl_editor_file = QLabel("Sin archivo")
        self.lbl_editor_file.setStyleSheet(f"color: {AURORA['text_primary']}; font-weight: bold; padding: 0 8px;")
        toolbar.addWidget(self.lbl_editor_file)

        # Separador
        self._add_separator(toolbar)

        # ── NAVEGACIÓN DE PÁGINA ───────────────────────────
        btn_prev = PushButton(FIF.LEFT_ARROW, "")
        btn_prev.setFixedWidth(40)
        btn_prev.setToolTip("Página anterior")
        btn_prev.clicked.connect(self.canvas.prev_page)
        toolbar.addWidget(btn_prev)

        self.lbl_page = QLabel("1 / 1")
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_page.setFixedWidth(80)
        self.lbl_page.setStyleSheet(f"color: {AURORA['text_secondary']}; font-weight: bold;")
        toolbar.addWidget(self.lbl_page)

        btn_next = PushButton(FIF.RIGHT_ARROW, "")
        btn_next.setFixedWidth(40)
        btn_next.setToolTip("Página siguiente")
        btn_next.clicked.connect(self.canvas.next_page)
        toolbar.addWidget(btn_next)

        # Separador
        self._add_separator(toolbar)

        # ── ZOOM ───────────────────────────────────────────
        btn_zoom_out = PushButton(FIF.ZOOM_OUT, "")
        btn_zoom_out.setFixedWidth(40)
        btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        toolbar.addWidget(btn_zoom_out)

        self.lbl_zoom = QLabel("150%")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setFixedWidth(60)
        self.lbl_zoom.setStyleSheet(f"color: {AURORA['text_secondary']};")
        toolbar.addWidget(self.lbl_zoom)

        btn_zoom_in = PushButton(FIF.ZOOM_IN, "")
        btn_zoom_in.setFixedWidth(40)
        btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        toolbar.addWidget(btn_zoom_in)

        btn_fit = PushButton(FIF.FULL_SCREEN, "Ajustar Ancho")
        btn_fit.setFixedWidth(100)
        btn_fit.clicked.connect(self.canvas.zoom_fit_width)
        toolbar.addWidget(btn_fit)

        # Separador
        self._add_separator(toolbar)

        # ── MODOS ──────────────────────────────────────────
        self.btn_mode_view = PushButton(FIF.VIEW, "Ver")
        self.btn_mode_view.clicked.connect(lambda: self._set_editor_mode(EditorMode.VIEW))
        toolbar.addWidget(self.btn_mode_view)

        self.btn_mode_edit = PushButton(FIF.EDIT, "Editar Texto")
        self.btn_mode_edit.clicked.connect(lambda: self._set_editor_mode(EditorMode.EDIT_TEXT))
        toolbar.addWidget(self.btn_mode_edit)

        self.btn_mode_annotate = PushButton(FIF.PENCIL_INK, "Anotar")
        self.btn_mode_annotate.clicked.connect(lambda: self._set_editor_mode(EditorMode.ANNOTATE))
        toolbar.addWidget(self.btn_mode_annotate)

        toolbar.addStretch()

        # ── GUARDAR ────────────────────────────────────────
        btn_save_as = PushButton(FIF.SAVE_AS, "Guardar Como")
        btn_save_as.clicked.connect(lambda: self.canvas.save_as())
        toolbar.addWidget(btn_save_as)

        btn_save = PrimaryPushButton(FIF.SAVE, "Guardar")
        btn_save.setFixedWidth(100)
        btn_save.clicked.connect(self.save_editor_changes)
        toolbar.addWidget(btn_save)

        layout.addWidget(toolbar_widget)

        # ── STATUS BAR ─────────────────────────────────────
        self.editor_status = QLabel("Listo")
        self.editor_status.setFixedHeight(22)
        self.editor_status.setStyleSheet(f"""
            QLabel {{
                background: {AURORA['bg_surface']};
                color: {AURORA['text_secondary']};
                padding: 2px 10px;
                font-size: 10px;
                border-top: 1px solid {AURORA['border']};
            }}
        """)

        # ── ANNOTATION TOOLBAR (sidebar) ─────────────────────
        self.annotation_toolbar = AnnotationToolbar(self)
        self.annotation_toolbar.setVisible(False)  # Solo visible en modo ANNOTATE

        # Conectar señales del toolbar de anotaciones
        self.annotation_toolbar.tool_selected.connect(self.canvas.set_annotation_tool)
        self.annotation_toolbar.color_selected.connect(self.canvas.set_annotation_color)
        self.annotation_toolbar.line_width_changed.connect(self.canvas.set_annotation_width)
        self.annotation_toolbar.watermark_requested.connect(self.canvas.apply_watermark)
        self.annotation_toolbar.signature_requested.connect(self._on_signature_requested)
        self.annotation_toolbar.stamp_text_selected.connect(
            lambda t: setattr(self.canvas, '_stamp_text', t)
        )

        # ── CANVAS + ANNOTATION SIDEBAR ────────────────────
        editor_body = QHBoxLayout()
        editor_body.setSpacing(0)
        editor_body.addWidget(self.annotation_toolbar)
        editor_body.addWidget(self.canvas, stretch=1)

        layout.addLayout(editor_body, stretch=1)
        layout.addWidget(self.editor_status)

        # ── Connect canvas signals ─────────────────────────
        self.canvas.page_changed.connect(self._on_editor_page_changed)
        self.canvas.zoom_changed.connect(self._on_editor_zoom_changed)
        self.canvas.status_message.connect(self._on_editor_status)

    def _add_separator(self, layout):
        sep = QLabel("|")
        sep.setStyleSheet(f"color: {AURORA['border']}; padding: 0 2px;")
        layout.addWidget(sep)

    def _set_editor_mode(self, mode):
        from .components.document_canvas import EditorMode
        self.canvas.set_mode(mode)

        # Mostrar/ocultar toolbar de anotaciones
        self.annotation_toolbar.setVisible(mode == EditorMode.ANNOTATE)

        # Actualizar visual de botones de modo
        normal_style = ""
        active_style = f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;"

        self.btn_mode_view.setStyleSheet(active_style if mode == EditorMode.VIEW else normal_style)
        self.btn_mode_edit.setStyleSheet(active_style if mode == EditorMode.EDIT_TEXT else normal_style)
        self.btn_mode_annotate.setStyleSheet(active_style if mode == EditorMode.ANNOTATE else normal_style)

    def _on_editor_page_changed(self, current, total):
        self.lbl_page.setText(f"{current} / {total}")

    def _on_editor_zoom_changed(self, percent):
        self.lbl_zoom.setText(f"{percent}%")

    def _on_editor_status(self, msg):
        self.editor_status.setText(msg)

    def _on_signature_requested(self):
        """Abrir diálogo para seleccionar imagen de firma."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar imagen de firma", "",
            "Imágenes (*.png *.jpg *.jpeg *.bmp)"
        )
        if file_path:
            self.canvas.insert_signature(file_path)
            self.log.append_msg("✒ Firma insertada en el documento.")

    def _connect_signals(self):
        # Selección de archivo -> Cargar miniaturas
        self.file_list.currentItemChanged.connect(self._on_file_selected)
        self.file_list.itemDoubleClicked.connect(self.open_editor) # Doble clic abre editor
        
        # Selección de páginas -> Actualizar botones
        self.pages_panel.pages_selected.connect(self._on_pages_selected)
        self.pages_panel.page_double_clicked.connect(self.open_editor_at_page)
        
        # Acciones de contexto
        self.pages_panel.action_requested.connect(self._on_context_action)
        self.pages_panel.reorder_requested.connect(self.run_reorder)

    def _on_file_selected(self, current, previous):
        if not current:
            self.pages_panel.clear()
            self.btn_edit.setEnabled(False)
            self.btn_save_mem.setEnabled(False)
            return
            
        self.btn_edit.setEnabled(True)
        self.btn_save_mem.setEnabled(True)
        idx = self.file_list.row(current)
        if idx < len(self.loaded_files):
            file_path = self.loaded_files[idx]
            temp_path = self.temp_files.get(file_path, file_path)
            self.log.append_msg(f"Renderizando vista previa en caché: {file_path.name}...")
            self.pages_panel.load_pdf(temp_path)

    def open_editor(self):
        file = self._get_current_real_file()
        if not file: return

        self.log.append_msg(f"Abriendo editor para: {file.name}")
        self.lbl_editor_file.setText(f"Editando: {file.name}")

        temp_path = self.temp_files.get(file, file)
        self.canvas.load_document(temp_path)
        self.switchTo(self.editor)

    def open_editor_at_page(self, page_num):
        self.open_editor()
        self.canvas.go_to_page(page_num)

    def close_editor(self):
        self.switchTo(self.dashboard)

    def open_md_editor(self):
        self.switchTo(self.md_editor)

    def _show_about(self):
        QMessageBox.information(
            self, "Get Hands-On",
            "<h3 style='color:#EA580C'>🖐️ Get Hands-On (MeterMano)</h3>"
            "<p>Suite local de manipulación de PDFs.<br>"
            "Sin nube. Sin suscripción. Sin excusas.</p>"
            "<p style='color:#A8A29E'>Por Aldra &bull; v1.2.0</p>"
        )

    def save_editor_changes(self):
        if self.canvas.save_changes():
            self.log.append_msg("✅ Cambios guardados correctamente en el PDF.")
        else:
            self.log.append_msg("❌ Error al guardar cambios.")


    def _on_pages_selected(self, pages: list):
        self.selected_pages = pages
        has_pages = len(pages) > 0
        
        # Habilitar botones contextuales
        self.btn_rotate.setEnabled(has_pages)
        self.btn_extract.setEnabled(has_pages)
        self.btn_delete.setEnabled(has_pages)
        
        # Actualizar texto
        cnt = len(pages)
        if has_pages:
            self.btn_extract.setText(f"📄 Extraer {cnt} pág{'s' if cnt!=1 else ''}")
            self.btn_delete.setText(f"🗑️ Eliminar {cnt} pág{'s' if cnt!=1 else ''}")
            self.btn_rotate.setText(f"↻ Rotar {cnt} pág{'s' if cnt!=1 else ''}")
        else:
            self.btn_extract.setText("📄 Extraer páginas")
            self.btn_delete.setText("🗑️ Eliminar páginas")
            self.btn_rotate.setText("↻ Rotar páginas")

    def add_files(self, files):
        import shutil
        for f in files:
            # Evitar duplicados exactos
            if f not in self.loaded_files:
                self.loaded_files.append(f)
                
                # In-Memory Buffer architecture
                temp_path = Path(self.temp_dir.name) / f.name
                shutil.copy(f, temp_path)
                self.temp_files[f] = temp_path
                
                self.file_list.add_file(f)
                self.log.append_msg(f"Cargado al buffer: {f.name}")
                
                # Easter Egg
                if f.stem.lower() == 'cerezas':
                    self.log.append_special("🍒 \"Porque lo bueno siempre se comparte.\" — ☀️")

    def open_split_dialog(self):
        items = self.file_list.selectedItems()
        if not items:
            self.log.append_msg("⚠️ Selecciona un archivo de la lista para separar.")
            return
            
        idx = self.file_list.row(items[0])
        target_file = self.loaded_files[idx]
        
        dialog = SplitDialog(self, target_file.name)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.run_split(target_file, data)

    def run_split(self, file_path, params):
        output_dir = file_path.parent / f"{file_path.stem}_split"
        
        self.log.append_msg(f"Iniciando separación de {file_path.name}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=split_pdf,
            input_file=file_path,
            output_dir=output_dir,
            **params
        )
        self.worker.log.connect(self.log.append_msg)
        self.worker.finished.connect(lambda res: self.on_task_finished(res, "Separación"))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def open_merge_dialog(self):
        if len(self.loaded_files) < 2:
            self.log.append_msg("⚠️ Necesitas cargar al menos 2 archivos para unir.")
            return
            
        dialog = MergeDialog(self, self.loaded_files)
        if dialog.exec():
            data = dialog.get_data()
            if data:
                self.run_merge(data['files'], data['filename'])

    def run_merge(self, files, filename):
        if not files: return
        output_file = files[0].parent / filename
        
        self.log.append_msg(f"Uniendo {len(files)} archivos...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=merge_pdfs,
            input_files=files,
            output_file=output_file
        )
        self.worker.log.connect(self.log.append_msg)
        self.worker.finished.connect(lambda res: self.on_task_finished(res, "Unión"))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def set_ui_busy(self, busy):
        self.btn_split.setEnabled(not busy)
        self.btn_merge.setEnabled(not busy)
        self.drop_area.setEnabled(not busy)
        # Disable aesthetic buttons too
        self.btn_rotate.setEnabled(not busy and len(self.selected_pages) > 0)
        self.btn_extract.setEnabled(not busy and len(self.selected_pages) > 0)
        self.btn_delete.setEnabled(not busy and len(self.selected_pages) > 0)
        # Conversion buttons
        self.btn_to_word.setEnabled(not busy)
        self.btn_to_images.setEnabled(not busy)
        self.btn_from_images.setEnabled(not busy)
        self.btn_compress.setEnabled(not busy)
        self.btn_ocr.setEnabled(not busy)
        # Security buttons
        self.btn_encrypt.setEnabled(not busy)
        self.btn_decrypt.setEnabled(not busy)
        # Batch
        self.btn_batch.setEnabled(not busy)

    def on_task_finished(self, results, task_name):
        self.set_ui_busy(False)
        self.log.append_msg(f"✅ {task_name} completada con éxito.")
        QMessageBox.information(self, "Listo", f"{task_name} finalizada.\nArchivos generados: {len(results)}")

    def on_task_error(self, err_msg):
        self.set_ui_busy(False)
        self.log.append_msg(f"❌ Error: {err_msg}")
        QMessageBox.critical(self, "Error", f"Ocurrió un error:\n{err_msg}")

    def _on_context_action(self, action: str, pages: list):
        self.selected_pages = pages # Ensure operation applies to context target
        
        if action == "rotate":
            self.run_rotate()
        elif action == "delete":
            self.run_delete()
        elif action == "extract":
            self.run_extract()
        elif action == "duplicate":
            self.run_duplicate()
        elif action == "insert_blank":
            self.run_insert_blank()
        elif action == "move_left":
            self.run_move("left")
        elif action == "move_right":
            self.run_move("right")

    def run_reorder(self, new_order: list):
        self._mutate_temp_file("Reordenamiento", reorder_pages, new_order=new_order)

    def run_move(self, direction):
        if not self.selected_pages: return
        target_page = self.selected_pages[0]
        self._mutate_temp_file("Movimiento de página", move_page, page_num=target_page, direction=direction)

    def run_duplicate(self):
        if not self.selected_pages: return
        self._mutate_temp_file("Duplicar", duplicate_pages, pages_to_duplicate=self.selected_pages)

    def run_insert_blank(self):
        if not self.selected_pages: return
        target_page = sorted(self.selected_pages)[-1]
        self._mutate_temp_file("Insertar página en blanco", insert_blank_page, after_page=target_page)

    def _get_current_real_file(self):
        items = self.file_list.selectedItems()
        if not items: return None
        idx = self.file_list.row(items[0])
        if idx < len(self.loaded_files):
            return self.loaded_files[idx]
        return None

    def _mutate_temp_file(self, task_name, task_fn, **kwargs):
        real_file = self._get_current_real_file()
        if not real_file: return
        
        temp_path = self.temp_files.get(real_file)
        if not temp_path: return
        output_temp = Path(self.temp_dir.name) / f"mut_{temp_path.name}"
        
        self.log.append_msg(f"{task_name} en memoria: {real_file.name}...")
        self.set_ui_busy(True)
        
        kwargs['input_file'] = temp_path
        kwargs['output_file'] = output_temp
        if 'log_cb' not in kwargs:
            kwargs['log_cb'] = self.log.append_msg
            
        self.worker = TaskWorker(task_fn=task_fn, **kwargs)
        self.worker.finished.connect(lambda res: self._on_mutate_finished(res, real_file, temp_path, output_temp))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def _on_mutate_finished(self, results, real_file, temp_path, output_temp):
        self.set_ui_busy(False)
        import shutil
        if results and output_temp.exists():
            shutil.move(str(output_temp), str(temp_path))
            self.log.append_msg("✅ Operación completada en memoria temporal. Aplica 'Guardar' para exportar.")
            self.pages_panel.load_pdf(temp_path)
            if self.canvas.doc:
                self.canvas.load_document(temp_path)

    def run_rotate(self):
        if not self.selected_pages: return
        self._mutate_temp_file("Rotación a 90°", rotate_pages, pages=self.selected_pages, angle=90)

    def run_delete(self):
        if not self.selected_pages: return
        reply = QMessageBox.question(self, 'Confirmar eliminación', 
            f"¿Seguro que quieres eliminar {len(self.selected_pages)} páginas de la memoria?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self._mutate_temp_file("Eliminación", delete_pages, pages_to_delete=self.selected_pages)

    def run_extract(self):
        token = self._get_current_real_file()
        if not token or not self.selected_pages: return
        
        output_file, _ = QFileDialog.getSaveFileName(self, "Guardar Extracción", str(token.parent / f"{token.stem}_extracted.pdf"), "PDF (*.pdf)")
        if not output_file: return
        
        self.log.append_msg(f"Extrayendo {len(self.selected_pages)} páginas de {token.name}...")
        self.set_ui_busy(True)
        self.worker = TaskWorker(task_fn=extract_pages, input_file=self.temp_files.get(token, token), output_file=Path(output_file), pages=self.selected_pages)
        self.worker.log.connect(self.log.append_msg)
        self.worker.finished.connect(lambda res: self.on_task_finished(res, "Extracción"))
        self.worker.error.connect(self.on_task_error)
        self.worker.start()

    def run_save_memory(self):
        real_file = self._get_current_real_file()
        if not real_file: return
        temp_path = self.temp_files.get(real_file)
        if not temp_path: return
        
        save_path, _ = QFileDialog.getSaveFileName(self, "Exportar Archivo Editado", str(real_file.parent / f"{real_file.stem}_editado.pdf"), "PDF (*.pdf)")
        if save_path:
            import shutil
            shutil.copy(temp_path, save_path)
            self.log.append_msg(f"✅ Documento exportado exitosamente a: {save_path}")
            QMessageBox.information(self, "Listo", "Archivo guardado exitosamente.")



    # ── CONVERSION HANDLERS ────────────────────────────────

    def run_pdf_to_word(self):
        """Convert selected PDF to Word (.docx)."""
        token = self._get_current_file()
        if not token:
            self.log.append_msg("⚠️ Selecciona un PDF de la lista para convertir.")
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar como Word",
            str(token.parent / f"{token.stem}.docx"),
            "Word Document (*.docx)"
        )
        if not output_file:
            return

        self.log.append_msg(f"Convirtiendo {token.name} → Word...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=pdf_to_word,
            input_file=token,
            output_file=Path(output_file)
        )
        self._connect_worker(self.worker, "Conversión PDF → Word")

    def run_pdf_to_images(self):
        """Convert selected PDF pages to images."""
        token = self._get_current_file()
        if not token:
            self.log.append_msg("Selecciona un PDF de la lista para exportar.")
            return

        from PyQt6.QtWidgets import QInputDialog
        fmt, ok = QInputDialog.getItem(
            self, "Formato de imagen",
            "Selecciona el formato:",
            ["PNG (sin perdida)", "JPG (mas liviano)"],
            0, False
        )
        if not ok:
            return

        ext = "png" if "PNG" in fmt else "jpg"

        dpi_options = ["150 DPI (rapido)", "300 DPI (estandar)", "600 DPI (alta calidad)"]
        dpi_str, ok = QInputDialog.getItem(
            self, "Resolucion",
            "Selecciona la resolucion:",
            dpi_options, 1, False
        )
        if not ok:
            return

        dpi = int(dpi_str.split()[0])

        output_dir = QFileDialog.getExistingDirectory(
            self, "Carpeta de salida",
            str(token.parent)
        )
        if not output_dir:
            return

        self.log.append_msg(f"Exportando {token.name} -> {ext.upper()} ({dpi} DPI)...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=pdf_to_images,
            input_file=token,
            output_dir=Path(output_dir),
            fmt=ext,
            dpi=dpi
        )
        self._connect_worker(self.worker, "Exportacion PDF -> Imagenes")

    def run_images_to_pdf(self):
        """Combine multiple images into a PDF."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar imagenes", "",
            "Imagenes (*.png *.jpg *.jpeg *.bmp *.tiff *.webp);;Todos (*)"
        )
        if not files:
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF",
            str(Path(files[0]).parent / "imagenes_combinadas.pdf"),
            "PDF (*.pdf)"
        )
        if not output_file:
            return

        image_paths = [Path(f) for f in files]
        self.log.append_msg(f"Combinando {len(image_paths)} imagenes -> PDF...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=images_to_pdf,
            image_files=image_paths,
            output_file=Path(output_file)
        )
        self._connect_worker(self.worker, "Conversion Imagenes -> PDF")

    def run_compress(self):
        """Compress the selected PDF."""
        token = self._get_current_file()
        if not token:
            self.log.append_msg("Selecciona un PDF de la lista para comprimir.")
            return

        from PyQt6.QtWidgets import QInputDialog
        quality_options = [
            "Alta (preserva calidad)",
            "Media (balance recomendado)",
            "Baja (maxima compresion)"
        ]
        quality_str, ok = QInputDialog.getItem(
            self, "Nivel de compresion",
            "Selecciona la calidad:",
            quality_options, 1, False
        )
        if not ok:
            return

        quality_map = {"Alta": "high", "Media": "medium", "Baja": "low"}
        quality = quality_map.get(quality_str.split()[0], "medium")

        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF comprimido",
            str(token.parent / f"{token.stem}_compressed.pdf"),
            "PDF (*.pdf)"
        )
        if not output_file:
            return

        orig_kb = token.stat().st_size / 1024
        self.log.append_msg(f"Comprimiendo {token.name} ({orig_kb:.0f} KB, calidad: {quality})...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=compress_pdf,
            input_file=token,
            output_file=Path(output_file),
            quality=quality
        )
        self._connect_worker(self.worker, "Compresion PDF")

    # -- OCR HANDLER --

    def run_ocr(self):
        """Apply OCR to make a scanned PDF searchable."""
        token = self._get_current_file()
        if not token:
            self.log.append_msg("Selecciona un PDF para aplicar OCR.")
            return

        from PyQt6.QtWidgets import QInputDialog
        lang_options = [
            "Espanol + Ingles (spa+eng)",
            "Espanol (spa)",
            "Ingles (eng)",
            "Frances (fra)",
            "Portugues (por)"
        ]
        lang_str, ok = QInputDialog.getItem(
            self, "Idioma del documento",
            "Selecciona el idioma para OCR:",
            lang_options, 0, False
        )
        if not ok:
            return

        lang = lang_str.split("(")[-1].rstrip(")")

        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF con OCR",
            str(token.parent / f"{token.stem}_ocr.pdf"),
            "PDF (*.pdf)"
        )
        if not output_file:
            return

        self.log.append_msg(f"Aplicando OCR a {token.name} (idioma: {lang})...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=ocr_pdf,
            input_file=token,
            output_file=Path(output_file),
            lang=lang
        )
        self._connect_worker(self.worker, "OCR")

    # -- SECURITY HANDLERS --

    def run_encrypt(self):
        """Encrypt the selected PDF with a password."""
        token = self._get_current_file()
        if not token:
            self.log.append_msg("Selecciona un PDF para proteger.")
            return

        from PyQt6.QtWidgets import QInputDialog
        password, ok = QInputDialog.getText(
            self, "Proteger PDF",
            "Ingresa el password de proteccion:",
            QInputDialog.InputMode.TextInput
        )
        if not ok or not password:
            return

        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF protegido",
            str(token.parent / f"{token.stem}_protected.pdf"),
            "PDF (*.pdf)"
        )
        if not output_file:
            return

        self.log.append_msg(f"Protegiendo {token.name} con AES-256...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=encrypt_pdf,
            input_file=token,
            output_file=Path(output_file),
            user_password=password
        )
        self._connect_worker(self.worker, "Cifrado PDF")

    def run_decrypt(self):
        """Remove password protection from a PDF."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar PDF protegido", "",
            "PDF (*.pdf)"
        )
        if not file_path:
            return

        from PyQt6.QtWidgets import QInputDialog
        password, ok = QInputDialog.getText(
            self, "Desbloquear PDF",
            "Ingresa el password:",
            QInputDialog.InputMode.TextInput
        )
        if not ok:
            return

        source = Path(file_path)
        output_file, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF desbloqueado",
            str(source.parent / f"{source.stem}_unlocked.pdf"),
            "PDF (*.pdf)"
        )
        if not output_file:
            return

        self.log.append_msg(f"Desbloqueando {source.name}...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=decrypt_pdf,
            input_file=source,
            output_file=Path(output_file),
            password=password
        )
        self._connect_worker(self.worker, "Descifrado PDF")

    # -- BATCH HANDLER --

    def run_batch(self):
        """Apply an operation to multiple PDFs at once."""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Seleccionar PDFs para procesamiento por lotes", "",
            "PDF (*.pdf)"
        )
        if not files or len(files) < 1:
            return

        from PyQt6.QtWidgets import QInputDialog
        op_options = [
            "Comprimir",
            "Convertir a Word",
            "Convertir a Imagenes",
            "Rotar todas las paginas",
            "OCR (texto seleccionable)",
            "Proteger con password"
        ]
        op_str, ok = QInputDialog.getItem(
            self, "Operacion por lotes",
            f"Selecciona la operacion para {len(files)} archivos:",
            op_options, 0, False
        )
        if not ok:
            return

        op_map = {
            "Comprimir": BatchOp.COMPRESS,
            "Convertir a Word": BatchOp.TO_WORD,
            "Convertir a Imagenes": BatchOp.TO_IMAGES,
            "Rotar todas las paginas": BatchOp.ROTATE_ALL,
            "OCR (texto seleccionable)": BatchOp.OCR,
            "Proteger con password": BatchOp.ENCRYPT
        }
        operation = op_map.get(op_str, BatchOp.COMPRESS)

        params = {}
        if operation == BatchOp.COMPRESS:
            q_opts = ["Media (recomendado)", "Baja (maxima compresion)", "Alta (minima compresion)"]
            q_str, ok = QInputDialog.getItem(self, "Calidad", "Nivel:", q_opts, 0, False)
            if not ok:
                return
            params["quality"] = {"Media": "medium", "Baja": "low", "Alta": "high"}.get(q_str.split()[0], "medium")

        elif operation == BatchOp.ENCRYPT:
            pw, ok = QInputDialog.getText(self, "Password", "Password para todos los archivos:")
            if not ok or not pw:
                return
            params["password"] = pw

        elif operation == BatchOp.ROTATE_ALL:
            a_opts = ["90 grados (derecha)", "180 grados", "270 grados (izquierda)"]
            a_str, ok = QInputDialog.getItem(self, "Angulo", "Rotar:", a_opts, 0, False)
            if not ok:
                return
            angle_map = {"90": 90, "180": 180, "270": 270}
            params["angle"] = angle_map.get(a_str.split()[0], 90)

        output_dir = QFileDialog.getExistingDirectory(
            self, "Carpeta de salida para los resultados",
            str(Path(files[0]).parent)
        )
        if not output_dir:
            return

        input_paths = [Path(f) for f in files]
        self.log.append_msg(f"BATCH: {op_str} en {len(files)} archivos...")
        self.set_ui_busy(True)

        self.worker = TaskWorker(
            task_fn=batch_apply,
            input_files=input_paths,
            operation=operation,
            output_dir=Path(output_dir),
            params=params
        )
        self._connect_worker(self.worker, f"Batch {op_str}")

    # ─────────────────────────────────────────────────────────────────────────
    # DOCUMENTAR — Exportar tablas, Marca de agua, Numeración
    # ─────────────────────────────────────────────────────────────────────────

    def run_export_tables(self):
        """Detecta y exporta tablas del PDF seleccionado a CSV o XLSX."""
        pdf_path_obj = self._get_current_file()
        if not pdf_path_obj:
            QMessageBox.warning(self, "Sin selección", "Selecciona un PDF en la lista primero.")
            return
        pdf_path = str(pdf_path_obj)

        # Preguntar formato
        from PyQt6.QtWidgets import QInputDialog
        fmt, ok = QInputDialog.getItem(
            self, "Formato de exportación", "Exportar tablas como:",
            ["Excel (.xlsx) — una hoja por tabla", "CSV — un archivo por tabla"],
            0, False
        )
        if not ok:
            return

        if "xlsx" in fmt.lower():
            out_path, _ = QFileDialog.getSaveFileName(
                self, "Guardar Excel", str(Path(pdf_path).stem) + "_tablas.xlsx",
                "Excel Files (*.xlsx)"
            )
            if not out_path:
                return
            try:
                count = extract_tables_to_xlsx(pdf_path, out_path)
                if count == 0:
                    QMessageBox.information(self, "Sin tablas", "No se encontraron tablas detectables en este PDF.")
                else:
                    QMessageBox.information(self, "Exportado", f"✅ {count} tabla(s) exportadas a:\n{out_path}")
                    self.log.append_msg(f"Tablas exportadas → {out_path} ({count} tablas)")
            except ImportError as e:
                QMessageBox.critical(self, "Dependencia faltante", str(e))
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            out_dir = QFileDialog.getExistingDirectory(
                self, "Carpeta de salida para los CSV",
                str(Path(pdf_path).parent)
            )
            if not out_dir:
                return
            try:
                created = extract_tables_to_csv(pdf_path, out_dir)
                if not created:
                    QMessageBox.information(self, "Sin tablas", "No se encontraron tablas detectables en este PDF.")
                else:
                    QMessageBox.information(self, "Exportado", f"✅ {len(created)} archivo(s) CSV creados en:\n{out_dir}")
                    self.log.append_msg(f"Tablas CSV exportadas → {out_dir} ({len(created)} archivos)")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def run_watermark(self):
        """Abre diálogo de marca de agua y aplica al PDF seleccionado in-memory."""
        if not self._get_current_real_file():
            QMessageBox.warning(self, "Sin selección", "Selecciona un PDF en la lista primero.")
            return
            
        dlg = WatermarkDialog(self)
        dlg.tabs.setCurrentIndex(0)
        if dlg.exec() != WatermarkDialog.DialogCode.Accepted:
            return

        params = dlg.get_watermark_params()
        self._mutate_temp_file("Marca de Agua", add_watermark_clean, **params)

    def run_page_numbers(self):
        """Abre diálogo de numeración/encabezado-pie y aplica al PDF seleccionado in-memory."""
        if not self._get_current_real_file():
            QMessageBox.warning(self, "Sin selección", "Selecciona un PDF en la lista primero.")
            return
            
        dlg = WatermarkDialog(self)
        dlg.tabs.setCurrentIndex(1)
        if dlg.exec() != WatermarkDialog.DialogCode.Accepted:
            return

        mode = dlg.get_mode()
        if mode == "pagenumber":
            params = dlg.get_pagenumber_params()
            self._mutate_temp_file("Numeración", add_page_numbers, **params)
        elif mode == "headerfooter":
            params = dlg.get_headerfooter_params()
            self._mutate_temp_file("Encabezado/Pie", add_header_footer, **params)
        else:
            params = dlg.get_watermark_params()
            self._mutate_temp_file("Marca de Agua", add_watermark_clean, **params)

