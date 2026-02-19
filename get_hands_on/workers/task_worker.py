
from PyQt6.QtCore import QThread, pyqtSignal
from typing import Callable

class TaskWorker(QThread):
    """
    Worker genérico para cualquier operación de PDF.
    Emite señales hacia la UI sin bloquearla.
    """
    progress = pyqtSignal(int)        # 0-100
    log = pyqtSignal(str)             # Mensaje para el log
    finished = pyqtSignal(list)       # Lista de archivos generados
    error = pyqtSignal(str)           # Error si algo falla

    def __init__(self, task_fn: Callable, **kwargs):
        super().__init__()
        self.task_fn = task_fn
        self.kwargs = kwargs

    def run(self):
        try:
            # Inyectamos callbacks de progreso y log
            self.kwargs['progress_cb'] = lambda p: self.progress.emit(p)
            self.kwargs['log_cb'] = lambda m: self.log.emit(m)
            result = self.task_fn(**self.kwargs)
            self.finished.emit(result if isinstance(result, list) else [result])
        except Exception as e:
            self.error.emit(str(e))
