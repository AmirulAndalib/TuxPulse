#!/usr/bin/env python3
# app/main.py - wrapper simplu
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

from ui_main import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName('TuxPulse')
    app.setStyle('Fusion')

    window = MainWindow()
    window.show()

    if hasattr(window, 'update_monitoring'):
        timer = QTimer()
        timer.timeout.connect(window.update_monitoring)
        timer.start(1000)

    sys.exit(app.exec_())

if __name__ == '__main__':
    main()