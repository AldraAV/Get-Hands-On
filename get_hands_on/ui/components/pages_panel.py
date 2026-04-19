
from PyQt6.QtWidgets import (
    QWidget, QScrollArea, QGridLayout,
    QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QMessageBox
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
from pathlib import Path
from ..style import AURORA
from .page_thumbnail import PageThumbnail

class PagesPanel(QWidget):
    """Panel de miniaturas de páginas con selección múltiple."""

    pages_selected = pyqtSignal(list)  # Lista de páginas seleccionadas
    page_double_clicked = pyqtSignal(int) # Página doble clickeada
    action_requested = pyqtSignal(str, list) # action_name, pages
    reorder_requested = pyqtSignal(list) # Nueva lista de orden de páginas (1-based)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.thumbnails = {}   # {page_num: PageThumbnail}
        self.selected_pages = set()
        self._setup_ui()
        self.setAcceptDrops(True)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QHBoxLayout()
        title = QLabel("PÁGINAS")
        title.setStyleSheet(f"color: {AURORA['accent_orange']}; font-weight: bold; font-size: 11px; letter-spacing: 1px;")
        
        self.sel_label = QLabel("0 seleccionadas")
        self.sel_label.setStyleSheet(f"color: {AURORA['text_secondary']}; font-size: 10px;")

        btn_all = QPushButton("Todas")
        btn_all.setFixedWidth(60)
        btn_all.clicked.connect(self.select_all)
        
        btn_none = QPushButton("Ninguna")
        btn_none.setFixedWidth(70)
        btn_none.clicked.connect(self.select_none)

        header.addWidget(title)
        header.addWidget(self.sel_label)
        header.addStretch()
        header.addWidget(btn_all)
        header.addWidget(btn_none)

        # Scroll area con grid de miniaturas
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {AURORA['bg_deep']}; }}")

        self.grid_widget = QWidget()
        self.grid = QGridLayout(self.grid_widget)
        self.grid.setSpacing(8)
        self.scroll.setWidget(self.grid_widget)

        layout.addLayout(header)
        layout.addWidget(self.scroll)

    def load_pdf(self, pdf_path: Path):
        """Renderiza miniaturas del PDF usando PyMuPDF (fitz) en segundo plano."""
        self.clear()
        
        # Iniciar worker
        try:
            from ...workers.thumbnail_worker import ThumbnailWorker
            
            # Matar worker anterior si existe
            if hasattr(self, 'worker') and self.worker.isRunning():
                self.worker.stop()
                self.worker.wait()
            
            self.worker = ThumbnailWorker(pdf_path, thumbnail_width=140)
            self.worker.page_ready.connect(self._add_thumbnail)
            self.worker.error.connect(lambda e: print(f"Thumbnail error: {e}"))
            self.worker.start()
            
        except Exception as e:
             print(f"Error starting thumbnail worker: {e}")
             self.grid.addWidget(QLabel(f"Error: {e}"), 0, 0)
    
    def _add_thumbnail(self, page_num: int, qimage: QImage):
        # Crear QPixmap en el hilo principal
        qpixmap = QPixmap.fromImage(qimage)
        
        thumb = PageThumbnail(page_num, qpixmap)
        thumb.clicked.connect(self._on_page_clicked)
        thumb.double_clicked.connect(self.page_double_clicked.emit)
        
        # Context Menu Policy
        thumb.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        thumb.customContextMenuRequested.connect(lambda pos, t=thumb: self._show_context_menu(pos, t))
        
        self.thumbnails[page_num] = thumb
        
        # Grid logic: 4 columns
        cols = 4
        idx = page_num - 1
        self.grid.addWidget(thumb, idx // cols, idx % cols)

    def _show_context_menu(self, pos, thumbnail):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction
        
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {AURORA['bg_elevated']}; border: 1px solid {AURORA['border']}; }}
            QMenu::item {{ color: {AURORA['text_primary']}; padding: 5px 20px; }}
            QMenu::item:selected {{ background: {AURORA['accent_orange']}; color: black; }}
        """)
        
        # Actions
        act_move_left = QAction("⬅ Mover Atrás", self)
        act_move_right = QAction("➡ Mover Adelante", self)
        act_rotate = QAction("↻ Rotar Derecha", self)
        act_dup = QAction("📑 Duplicar", self)
        act_blank = QAction("⬜ Insertar en Blanco", self)
        act_extract = QAction("📄 Extraer", self)
        act_delete = QAction("🗑️ Eliminar", self)
        
        # Connect actions
        act_move_left.triggered.connect(lambda: self.action_requested.emit("move_left", [thumbnail.page_num]))
        act_move_right.triggered.connect(lambda: self.action_requested.emit("move_right", [thumbnail.page_num]))
        act_rotate.triggered.connect(lambda: self.action_requested.emit("rotate", [thumbnail.page_num]))
        act_dup.triggered.connect(lambda: self.action_requested.emit("duplicate", [thumbnail.page_num]))
        act_blank.triggered.connect(lambda: self.action_requested.emit("insert_blank", [thumbnail.page_num]))
        act_extract.triggered.connect(lambda: self.action_requested.emit("extract", [thumbnail.page_num]))
        act_delete.triggered.connect(lambda: self.action_requested.emit("delete", [thumbnail.page_num]))
        
        menu.addAction(act_move_left)
        menu.addAction(act_move_right)
        menu.addSeparator()
        menu.addAction(act_rotate)
        menu.addAction(act_dup)
        menu.addAction(act_blank)
        menu.addSeparator()
        menu.addAction(act_extract)
        menu.addAction(act_delete)
        
        menu.exec(thumbnail.mapToGlobal(pos))


    def _on_page_clicked(self, page_num: int, modifiers):
        """Maneja la selección con lógica de Shift (rango) y Ctrl (toggle)."""
        
        # Estado actual de la tecla Shift/Ctrl
        is_shift = modifiers & Qt.KeyboardModifier.ShiftModifier
        is_ctrl = modifiers & Qt.KeyboardModifier.ControlModifier
        
        # Determinar nueva selección
        new_selection = set()
        
        if is_shift and self.selected_pages:
            # RANGO
            start = sorted(list(self.selected_pages))[-1] 
            if hasattr(self, 'last_clicked_page') and self.last_clicked_page:
                start = self.last_clicked_page
            
            low, high = min(start, page_num), max(start, page_num)
            
            if is_ctrl:
                new_selection = self.selected_pages.copy()
            
            for i in range(low, high + 1):
                new_selection.add(i)
                
        elif is_ctrl:
            # TOGGLE
            new_selection = self.selected_pages.copy()
            if page_num in new_selection:
                new_selection.remove(page_num)
            else:
                new_selection.add(page_num)
                
        else:
            # NORMAL
            new_selection = {page_num}

        self._update_selection_visuals(new_selection)
        self.last_clicked_page = page_num
        self.pages_selected.emit(sorted(list(self.selected_pages)))

    def _update_selection_visuals(self, new_selection: set):
        to_deselect = self.selected_pages - new_selection
        for p in to_deselect:
            if p in self.thumbnails:
                self.thumbnails[p].set_selected(False)
                
        to_select = new_selection - self.selected_pages
        for p in to_select:
            if p in self.thumbnails:
                self.thumbnails[p].set_selected(True)
                
        self.selected_pages = new_selection
        
        n = len(self.selected_pages)
        self.sel_label.setText(f"{n} seleccionada{'s' if n != 1 else ''}")

    def select_all(self):
        self.selected_pages.clear()
        for num, thumb in self.thumbnails.items():
            thumb.set_selected(True)
            self.selected_pages.add(num)
        
        n = len(self.selected_pages)
        self.sel_label.setText(f"{n} seleccionadas")
        self.pages_selected.emit(sorted(list(self.selected_pages)))

    def select_none(self):
        for thumb in self.thumbnails.values():
            thumb.set_selected(False)
        self.selected_pages.clear()
        self.sel_label.setText("0 seleccionadas")
        self.pages_selected.emit([])

    def clear(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        self.thumbnails.clear()
        self.selected_pages.clear()
        self.sel_label.setText("0 seleccionadas")
        self.pages_selected.emit([])

    def _get_drop_index(self, pos):
        # simplified 4-column logic
        closest_dist = float('inf')
        target_idx = 0
        
        sorted_thumbs = sorted(self.thumbnails.values(), key=lambda t: t.page_num)
        if not sorted_thumbs:
            return 0

        # Mapeamos pos (que viene de PagesPanel) a coordenadas del grid_widget
        # self.scroll contains self.grid_widget
        # Event pos is relative to PagesPanel
        # We need to consider scroll offset?
        # pos is typically relative to the widget receiving the drop, which is PagesPanel (self)
        
        # Actually, since widget is inside scroll area, maybe we should accept drops on the scroll area viewport?
        # But we set setAcceptDrops on self (PagesPanel).
        
        # Let's check where the mouse is relative to the grid items.
        # We can map everything to global then back to local
        
        global_pos = self.mapToGlobal(pos)
        grid_pos = self.grid_widget.mapFromGlobal(global_pos)
        
        for i, thumb in enumerate(sorted_thumbs):
            rect = thumb.geometry()
            center = rect.center()
            
            # If inside rect
            if rect.contains(grid_pos):
                if grid_pos.x() < center.x():
                    return i
                else:
                    return i + 1
            
            dist = (grid_pos - center).manhattanLength()
            if dist < closest_dist:
                closest_dist = dist
                target_idx = i
                
        # If past the last one
        last = sorted_thumbs[-1]
        last_rect = last.geometry()
        if grid_pos.y() > last_rect.bottom():
             return len(sorted_thumbs)
        
        # Default roughly closest
        # If mouse is to the right of closest, +1
        closest_widget = sorted_thumbs[target_idx]
        if grid_pos.x() > closest_widget.geometry().center().x():
            return target_idx + 1
            
        return target_idx

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("application/x-page-thumbnail"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat("application/x-page-thumbnail"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if not event.mimeData().hasFormat("application/x-page-thumbnail"):
            return
            
        src_page = int(event.mimeData().text())
        drop_idx = self._get_drop_index(event.position().toPoint())
        
        current_order = list(range(1, len(self.thumbnails) + 1))
        
        try:
            src_idx = current_order.index(src_page)
        except ValueError:
            return
            
        if src_idx == drop_idx or src_idx + 1 == drop_idx:
            return
            
        current_order.pop(src_idx)
        if src_idx < drop_idx:
            drop_idx -= 1
        current_order.insert(drop_idx, src_page)
        
        self.reorder_requested.emit(current_order)
        event.acceptProposedAction()
