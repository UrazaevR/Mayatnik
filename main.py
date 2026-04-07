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



END_TIME = 24*60*60
h = 0.01

g = 9.8
m = 2
d = 1
I = 0.8
R = 0.05
b = 6 * math.pi * 1.81 * 10 ** -5 * R * d

PSI0 = math.radians(30)
PSI10 = 0
w0_2 = m*g*d / I
beta = b / I

def read_floats_numpy(filename):
    """Чтение групп с помощью numpy"""
    all_values = np.fromfile(filename, dtype=np.float32)

    if len(all_values) % 11 != 0:
        print(f"Предупреждение: количество значений ({len(all_values)}) не кратно 11")

    for i in range(0, len(all_values), 11):
        yield all_values[i:i+11]

def dfi1dt(fi1, fi, t):
    return -w0_2 * math.sin(fi) - beta * fi1

def dfidt(fi1, fi, t):
    return fi1


class MplCanvas(FigureCanvas):

    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height))
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class RK4_Thread(QThread):
    error_ocurred = pyqtSignal(Exception)
    def set_params(self, canvas: FigureCanvas, stB: QLabel):
        self.canvas1 = canvas
        self.stB = stB

    def run(self):
        try:
            self.stB.setText('Поток вычислений запущен...')
            psi = np.array([])
            time = np.array([])
            
            i = 0
            for line in read_floats_numpy('values.bin'):
                i += 1
                yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4 = line
                if t > END_TIME: break
                time = np.append(time, t)
                psi = np.append(psi, yi)
                self.stB.setText(f'Текущее время: {t:.2f} cекунд')
                if i % 2000 == 0:
                    self.canvas1.axes.cla()
                    self.canvas1.axes.plot(time, psi)
                    self.canvas1.draw()
            
            self.canvas1.axes.cla()
            self.canvas1.axes.plot(time, psi)
            self.canvas1.draw()
            '''m1, m2, m3, m4, k1, k2, k3, k4 = 0, 0, 0, 0, 0, 0, 0, 0
            yi = PSI0
            y1i = PSI10
            i = 0
            t = 0
            time2 = np.array([0])
            amp = np.array([PSI0])
            while t < END_TIME:
                i += 1
                y1i = y1i + (m1 + 2*m2 + 2*m3 + m4) / 6
                yi = yi + (k1 + 2*k2 + 2*k3 + k4) / 6
                psi = np.append(psi, yi)
                time = np.append(time, t)
                print(f'\rАктуальное время: {t:.3f} с / {END_TIME} с', end='')
                if len(psi) > 2:
                    if (psi[-3] < psi[-2]) and (psi[-2] > psi[-1]):
                        amp = np.append(amp, psi[-1])
                        time2 = np.append(time2, time[-2])
                    elif (psi[-3] > psi[-2]) and (psi[-2] < psi[-1]):
                        time2[-1] = time[-2] - time2[-1]
                if i % 100 == 0:
                    self.canvas1.axes.cla()
                    self.canvas1.axes.plot(time, psi)
                    self.canvas1.draw()
                m1 = h * dfi1dt(y1i, yi, t)
                k1 = h * dfidt(y1i, yi, t)
                m2 = h * dfi1dt(y1i + m1/2, yi + k1/2, t + h/2)
                k2 = h * dfidt(y1i + m1/2, yi + k1/2, t + h/2)
                m3 = h * dfi1dt(y1i + m2/2, yi + k2/2, t + h/2)
                k3 = h * dfidt(y1i + m2/2, yi + k2/2, t + h/2)
                m4 = h * dfi1dt(y1i + m3, yi + k3, t + h)
                k4 = h * dfidt(y1i + m3, yi + k3, t + h)
                # np.array([yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4], dtype=np.float32).tofile(data)
                t = t + h
            self.canvas1.axes.cla()
            self.canvas1.axes.plot(time, psi)
            self.canvas1.draw()'''
            self.stB.setText('Вычисления завершены')
            return super().run()
        except Exception as e:
            self.error_ocurred.emit(e)


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

    def draw_plot(self):
        self.calculate_but.setDisabled(True)
        self.calc_thread = RK4_Thread()
        self.calc_thread.finished.connect(lambda *x: self.calculate_but.setEnabled(True))
        self.calc_thread.finished.connect(self.calc_thread.deleteLater)
        self.calc_thread.error_ocurred.connect(lambda x: print(x))
        self.calc_thread.set_params(self.canvas, self.statusLab)
        self.calc_thread.start()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    app.exec()