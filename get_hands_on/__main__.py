import os
import sys

# 1. Configurar backend ANTES de cualquier importación de Qt o qfluentwidgets
os.environ["PYQTWIDGETS_BACKEND"] = "PyQt6"

# FIX CRÍTICO: Importar pikepdf ANTES de Qt/qfluentwidgets para evitar
# conflictos de C++ y crashes (Access Violation) de DLLs en Windows.
import pikepdf

import os
import sys
import traceback

# 1. Configurar backend ANTES de cualquier importación de Qt o qfluentwidgets
os.environ["PYQTWIDGETS_BACKEND"] = "PyQt6"

try:
    from PyQt6.QtWidgets import QApplication
    import pikepdf
    from qfluentwidgets import setTheme, Theme, setThemeColor
    from get_hands_on.ui.main_window import MainWindow

    def main():
        # 2. Crear QApplication primero
        app = QApplication(sys.argv)
        app.setApplicationName("Get Hands-On")
        app.setOrganizationName("Aldra's Team")

        # 3. Importar qfluentwidgets después de crear la app
        setTheme(Theme.DARK)
        setThemeColor("#EA580C")  # Aurora naranja

        # 4. Importar MainWindow después de configurar el tema
        window = MainWindow()
        window.show()

        sys.exit(app.exec())

    if __name__ == "__main__":
        main()

except Exception as e:
    with open("crash.log", "w") as f:
        f.write("CRASH OCURRIDO:\n")
        traceback.print_exc(file=f)
    sys.exit(1)
