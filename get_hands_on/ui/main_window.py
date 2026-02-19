
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFrame, QFileDialog, QMessageBox, 
                             QSplitter, QStackedWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from pathlib import Path
import sys

from .style import AURORA, GLOBAL_STYLE, FONTS
from .components.drop_area import DropArea
from .components.file_list import FileList
from .components.log_panel import LogPanel
from .components.pages_panel import PagesPanel
from .components.document_canvas import DocumentCanvas
from .components.annotation_toolbar import AnnotationToolbar
from .dialogs.split_dialog import SplitDialog
from .dialogs.merge_dialog import MergeDialog
from ..workers.task_worker import TaskWorker
from ..core.pdf_ops import split_pdf, merge_pdfs, rotate_pages, extract_pages, delete_pages, duplicate_pages, insert_blank_page, move_page

class MainWindow(QMainWindow):
    """Ventana principal de Get Hands-On"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("[🖐️] Get Hands-On")
        self.resize(1100, 750)
        self.setStyleSheet(GLOBAL_STYLE)
        
        # Estado
        self.loaded_files = []
        self.worker = None
        self.selected_pages = []
        
        # UI Components
        self.stack = QStackedWidget()
        self.dashboard = QWidget() # Vista principal
        self.editor = QWidget()    # Vista editor (Fase 3)
        
        self.init_ui()
        self._connect_signals()
    
    def init_ui(self):
        self.setCentralWidget(self.stack)
        
        # --- VISTA 1: DASHBOARD ---
        self._setup_dashboard()
        self.stack.addWidget(self.dashboard)
        
        # --- VISTA 2: EDITOR (Canvas) ---
        self._setup_editor()
        self.stack.addWidget(self.editor)
        
        # Iniciar en dashboard
        self.stack.setCurrentIndex(0)

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
        
        # Splitter vertical para listas y log
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet(f"QSplitter::handle {{ background: {AURORA['bg_elevated']}; height: 2px; }}")
        
        # 1. Lista de Archivos
        files_widget = QWidget()
        files_layout = QVBoxLayout(files_widget)
        files_layout.setContentsMargins(0,0,0,0)
        list_label = QLabel("ARCHIVOS CARGADOS (Doble clic para editar)")
        list_label.setProperty("class", "section-title")
        files_layout.addWidget(list_label)
        self.file_list = FileList(self)
        files_layout.addWidget(self.file_list)
        splitter.addWidget(files_widget)
        
        # 2. Panel de Páginas
        pages_widget = QWidget()
        pages_layout = QVBoxLayout(pages_widget)
        pages_layout.setContentsMargins(0,0,0,0)
        self.pages_panel = PagesPanel(self)
        pages_layout.addWidget(self.pages_panel)
        splitter.addWidget(pages_widget)

        # 3. Log
        log_widget = QWidget()
        log_layout = QVBoxLayout(log_widget)
        log_layout.setContentsMargins(0,0,0,0)
        log_label = QLabel("LOG DE ACTIVIDAD")
        log_label.setProperty("class", "section-title")
        log_layout.addWidget(log_label)
        self.log = LogPanel(self)
        self.log.append_msg("Sistema iniciado. Listo para meter mano.")
        log_layout.addWidget(self.log)
        splitter.addWidget(log_widget)
        
        splitter.setSizes([150, 300, 100])
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
        
        # Botones
        self.btn_split = QPushButton("🔪 Separar páginas")
        self.btn_split.setMinimumHeight(45)
        self.btn_split.clicked.connect(self.open_split_dialog)
        self.btn_split.setToolTip("Separa el archivo seleccionado en varios PDFs.")
        
        self.btn_merge = QPushButton("🔗 Unir PDFs")
        self.btn_merge.setMinimumHeight(45)
        self.btn_merge.clicked.connect(self.open_merge_dialog)
        self.btn_merge.setToolTip("Une todos los archivos cargados en uno solo.")
        
        self.btn_rotate = QPushButton("↻  Rotar páginas")
        self.btn_rotate.setMinimumHeight(45)
        self.btn_rotate.clicked.connect(self.run_rotate)
        self.btn_rotate.setEnabled(False) 
        self.btn_rotate.setToolTip("Gira 90° las páginas seleccionadas (derecha).")
        
        self.btn_extract = QPushButton("📄 Extraer páginas")
        self.btn_extract.setMinimumHeight(45)
        self.btn_extract.clicked.connect(self.run_extract)
        self.btn_extract.setEnabled(False) 
        self.btn_extract.setToolTip("Crea un nuevo PDF solo con las páginas seleccionadas.")
        
        self.btn_delete = QPushButton("🗑️  Eliminar páginas")
        self.btn_delete.setMinimumHeight(45)
        self.btn_delete.clicked.connect(self.run_delete)
        self.btn_delete.setProperty("class", "danger")
        self.btn_delete.setEnabled(False) 
        self.btn_delete.setToolTip("Elimina las páginas seleccionadas del archivo.")
        
        self.btn_edit = QPushButton("✏️  Editar (Beta)")
        self.btn_edit.setMinimumHeight(45)
        self.btn_edit.clicked.connect(self.open_editor)
        self.btn_edit.setEnabled(False)
        self.btn_edit.setStyleSheet(f"background: {AURORA['bg_surface']}; border: 1px solid {AURORA['accent_orange']}; color: {AURORA['accent_orange']};")

        for btn in [self.btn_split, self.btn_merge, self.btn_rotate, self.btn_extract, self.btn_delete, self.btn_edit]:
            right_panel.addWidget(btn)
            right_panel.addSpacing(5)
            
        right_panel.addStretch()
        
        footer = QLabel("☀️ Por Aldra\nLe meto mano a tus PDFs 🔧")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            QPushButton {{
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
        btn_back = QPushButton("⬅ Volver")
        btn_back.clicked.connect(self.close_editor)
        btn_back.setFixedWidth(80)
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
        btn_prev = QPushButton("◀")
        btn_prev.setFixedWidth(30)
        btn_prev.setToolTip("Página anterior")
        btn_prev.clicked.connect(self.canvas.prev_page)
        toolbar.addWidget(btn_prev)

        self.lbl_page = QLabel("1 / 1")
        self.lbl_page.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_page.setFixedWidth(60)
        self.lbl_page.setStyleSheet(f"color: {AURORA['text_secondary']};")
        toolbar.addWidget(self.lbl_page)

        btn_next = QPushButton("▶")
        btn_next.setFixedWidth(30)
        btn_next.setToolTip("Página siguiente")
        btn_next.clicked.connect(self.canvas.next_page)
        toolbar.addWidget(btn_next)

        # Separador
        self._add_separator(toolbar)

        # ── ZOOM ───────────────────────────────────────────
        btn_zoom_out = QPushButton("−")
        btn_zoom_out.setFixedWidth(28)
        btn_zoom_out.setToolTip("Reducir zoom")
        btn_zoom_out.clicked.connect(self.canvas.zoom_out)
        toolbar.addWidget(btn_zoom_out)

        self.lbl_zoom = QLabel("150%")
        self.lbl_zoom.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_zoom.setFixedWidth(45)
        self.lbl_zoom.setStyleSheet(f"color: {AURORA['text_secondary']};")
        toolbar.addWidget(self.lbl_zoom)

        btn_zoom_in = QPushButton("+")
        btn_zoom_in.setFixedWidth(28)
        btn_zoom_in.setToolTip("Aumentar zoom")
        btn_zoom_in.clicked.connect(self.canvas.zoom_in)
        toolbar.addWidget(btn_zoom_in)

        btn_fit = QPushButton("⬚ Fit")
        btn_fit.setFixedWidth(50)
        btn_fit.setToolTip("Ajustar al ancho")
        btn_fit.clicked.connect(self.canvas.zoom_fit_width)
        toolbar.addWidget(btn_fit)

        # Separador
        self._add_separator(toolbar)

        # ── MODOS ──────────────────────────────────────────
        self.btn_mode_view = QPushButton("👁 Ver")
        self.btn_mode_view.setFixedWidth(60)
        self.btn_mode_view.setToolTip("Modo visualización (arrastrar para mover)")
        self.btn_mode_view.setStyleSheet(f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;")
        self.btn_mode_view.clicked.connect(lambda: self._set_editor_mode(EditorMode.VIEW))
        toolbar.addWidget(self.btn_mode_view)

        self.btn_mode_edit = QPushButton("✏️ Editar")
        self.btn_mode_edit.setFixedWidth(70)
        self.btn_mode_edit.setToolTip("Modo edición de texto (click en un bloque)")
        self.btn_mode_edit.clicked.connect(lambda: self._set_editor_mode(EditorMode.EDIT_TEXT))
        toolbar.addWidget(self.btn_mode_edit)

        self.btn_mode_annotate = QPushButton("🖊️ Anotar")
        self.btn_mode_annotate.setFixedWidth(75)
        self.btn_mode_annotate.setToolTip("Modo anotaciones")
        self.btn_mode_annotate.clicked.connect(lambda: self._set_editor_mode(EditorMode.ANNOTATE))
        toolbar.addWidget(self.btn_mode_annotate)

        toolbar.addStretch()

        # ── GUARDAR ────────────────────────────────────────
        btn_save_as = QPushButton("📥 Guardar Como")
        btn_save_as.setFixedWidth(120)
        btn_save_as.clicked.connect(lambda: self.canvas.save_as())
        toolbar.addWidget(btn_save_as)

        btn_save = QPushButton("💾 Guardar")
        btn_save.setFixedWidth(90)
        btn_save.setStyleSheet(f"background: {AURORA['accent_orange']}; color: black; font-weight: bold;")
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

    def _on_file_selected(self, current, previous):
        if not current:
            self.pages_panel.clear()
            self.btn_edit.setEnabled(False)
            return
            
        self.btn_edit.setEnabled(True)
        idx = self.file_list.row(current)
        if idx < len(self.loaded_files):
            file_path = self.loaded_files[idx]
            self.log.append_msg(f"Renderizando vista previa: {file_path.name}...")
            self.pages_panel.load_pdf(file_path)

    def open_editor(self):
        file = self._get_current_file()
        if not file: return
        
        self.log.append_msg(f"Abriendo editor para: {file.name}")
        self.lbl_editor_file.setText(f"Editando: {file.name}")
        
        self.canvas.load_document(file)
        self.stack.setCurrentIndex(1) # Switch to editor

    def open_editor_at_page(self, page_num):
        self.open_editor()
        self.canvas.go_to_page(page_num)

    def close_editor(self):
        self.stack.setCurrentIndex(0) # Switch to dashboard

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
        for f in files:
            # Evitar duplicados exactos
            if f not in self.loaded_files:
                self.loaded_files.append(f)
                self.file_list.add_file(f)
                self.log.append_msg(f"Cargado: {f.name}")
                
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

    def run_move(self, direction):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        # Move only the first selected page for now to avoid complexity in logic
        target_page = self.selected_pages[0]
        
        output_file = token.parent / f"{token.stem}_moved.pdf"
        self.log.append_msg(f"Moviendo página {target_page} hacia {direction}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=move_page,
            input_file=token,
            output_file=output_file,
            page_num=target_page,
            direction=direction,
            log_cb=self.log.append_msg
        )
        self._connect_worker()
        self.worker.start()

    def run_duplicate(self):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        output_file = token.parent / f"{token.stem}_dup.pdf"
        self.log.append_msg(f"Duplicando páginas {self.selected_pages}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=duplicate_pages,
            input_file=token,
            output_file=output_file,
            pages_to_duplicate=self.selected_pages,
            log_cb=self.log.append_msg
        )
        self._connect_worker()
        self.worker.start()

    def run_insert_blank(self):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        # Insert after the last selected page
        target_page = sorted(self.selected_pages)[-1]
        output_file = token.parent / f"{token.stem}_blank.pdf"
        
        self.log.append_msg(f"Insertando página en blanco después de la {target_page}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=insert_blank_page,
            input_file=token,
            output_file=output_file,
            after_page=target_page,
            log_cb=self.log.append_msg
        )
        self._connect_worker()
        self.worker.start()

    def _get_current_file(self):
        items = self.file_list.selectedItems()
        if not items: return None
        idx = self.file_list.row(items[0])
        if idx < len(self.loaded_files):
            return self.loaded_files[idx]
        return None

    def run_rotate(self):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        output_file = token.parent / f"{token.stem}_rotated.pdf"
        self.log.append_msg(f"Rotando {len(self.selected_pages)} páginas de {token.name}...")
        self.set_ui_busy(True)
        
        # Need to capture worker to prevent gc? self.worker is class attr
        self.worker = TaskWorker(
            task_fn=rotate_pages,
            input_file=token,
            output_file=output_file,
            pages=self.selected_pages,
            angle=90
        )
        self._connect_worker(self.worker, "Rotación")

    def run_extract(self):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        output_file = token.parent / f"{token.stem}_extracted.pdf"
        self.log.append_msg(f"Extrayendo {len(self.selected_pages)} páginas de {token.name}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=extract_pages,
            input_file=token,
            output_file=output_file,
            pages=self.selected_pages
        )
        self._connect_worker(self.worker, "Extracción")

    def run_delete(self):
        token = self._get_current_file()
        if not token or not self.selected_pages: return
        
        output_file = token.parent / f"{token.stem}_reduced.pdf"
        
        # Confirmación
        reply = QMessageBox.question(self, 'Confirmar eliminación', 
            f"¿Seguro que quieres eliminar {len(self.selected_pages)} páginas?\nEsta acción creará un nuevo archivo '{output_file.name}'.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
            
        if reply == QMessageBox.StandardButton.No:
            return

        self.log.append_msg(f"Eliminando páginas de {token.name}...")
        self.set_ui_busy(True)
        
        self.worker = TaskWorker(
            task_fn=delete_pages,
            input_file=token,
            output_file=output_file,
            pages_to_delete=self.selected_pages
        )
        self._connect_worker(self.worker, "Eliminación")

    def _connect_worker(self, worker, action_name):
        worker.log.connect(self.log.append_msg)
        # Using a default arg for lambda to capture variable correctly if needed, though here action_name is local
        # lambda res, name=action_name: self.on_task_finished(res, name)
        worker.finished.connect(lambda res, name=action_name: self.on_task_finished(res, name))
        worker.error.connect(self.on_task_error)
        worker.start()
