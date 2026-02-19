import sys
from PyQt6.QtWidgets import QApplication
from get_hands_on.ui.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Get Hands-On")
    app.setOrganizationName("Aldra's Team")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
