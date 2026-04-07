import os
import sys
from typing import Callable
import math
import numpy as np

os.environ["QT_API"] = "PyQt6"

from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMainWindow, QStatusBar
from PyQt6.QtCore import QThread, pyqtSignal
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.axes import Axes
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

from RK4 import RK4_Thread


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height))
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Зависимость перода колебаний от амплитуды клебаний маятника')
        self.resize(500, 400)
        layout = QVBoxLayout()
        self.setLayout(layout)

        fig = Figure()
        self.ax = fig.add_subplot()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        layout.addWidget(self.canvas)
        toolbar = NavigationToolbar(self.canvas, self)
        layout.addWidget(toolbar)

        self.calculate_but = QPushButton('Расчитать', self)
        self.calculate_but.setMaximumHeight(50)

        layout.addWidget(self.calculate_but)
        self.statusLab = QLabel()
        self.statusLab.setMaximumHeight(30)
        layout.addWidget(self.statusLab)

        self.calculate_but.clicked.connect(self.draw_plot)

    def _update_plot(self, x, y):
        self.canvas.axes.cla()
        self.canvas.axes.plot(x, y)
        self.canvas.draw()

    def draw_plot(self):
        self.calculate_but.setDisabled(True)
        self.calc_thread = RK4_Thread()
        self.calc_thread.finished.connect(lambda *x: self.calculate_but.setEnabled(True))
        self.calc_thread.finished.connect(self.calc_thread.deleteLater)
        self.calc_thread.error_ocurred.connect(lambda x: print(x))
        self.calc_thread.status_update.connect(self.statusLab.setText)
        self.calc_thread.plot_update.connect(self._update_plot)
        self.calc_thread.set_params(self.canvas, self.statusLab)
        self.calc_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    app.exec()