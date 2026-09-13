import sys

from PyQt5.QtWidgets import QApplication

from nextnote.ui.main_window import MainWindow


def main() -> int:
    """Application entry point: creates the Qt application and main window,
    runs the event loop, and returns its exit code."""
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(900, 700)
    window.show()
    return app.exec_()


if __name__ == "__main__":
    raise SystemExit(main())
