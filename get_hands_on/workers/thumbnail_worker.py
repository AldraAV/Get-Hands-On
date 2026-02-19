
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QImage, QPixmap
import fitz  # PyMuPDF
from pathlib import Path

class ThumbnailWorker(QThread):
    """
    Worker para generar miniaturas de PDF en segundo plano usando PyMuPDF.
    Emite señal por cada página renderizada.
    """
    page_ready = pyqtSignal(int, QImage)  # (page_num, qimage)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, pdf_path: Path, thumbnail_width: int = 150):
        super().__init__()
        self.pdf_path = pdf_path
        self.thumbnail_width = thumbnail_width
        self._is_running = True

    def run(self):
        try:
            doc = fitz.open(self.pdf_path)
            total_pages = len(doc)
            
            for i in range(total_pages):
                if not self._is_running:
                    break
                
                page = doc.load_page(i)
                
                # Calcular zoom para ancho deseado
                # get_pixmap devuelve imagen a 72 DPI por defecto (scale=1)
                # width original en puntos (1/72 inch)
                zoom = self.thumbnail_width / page.rect.width
                mat = fitz.Matrix(zoom, zoom)
                
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                # Convertir a QImage
                # Formato RGB888
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                
                # Emitir copia para que sea thread-safe
                self.page_ready.emit(i + 1, img.copy())
                
                # Pequeña pausa para no congelar la UI si es muy rápido? 
                # QThread ya corre separado, pero yield to event loop es bueno.
                # self.msleep(1) 
            
            doc.close()
            self.finished.emit()
            
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False
