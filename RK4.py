from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import QLabel
import numpy as np
import math
import os


class RK4_Thread(QThread):
    error_ocurred = pyqtSignal(Exception)
    status_update = pyqtSignal(str)
    plot_update = pyqtSignal(np.ndarray, np.ndarray)

    def read_floats_numpy(self, filename):
        """Чтение групп с помощью numpy"""
        all_values = np.fromfile(filename, dtype=np.float32)

        if len(all_values) % 11 != 0:
            print(f"Предупреждение: количество значений ({len(all_values)}) не кратно 11")

        for i in range(0, len(all_values), 11):
            yield all_values[i:i+11]

    def dfi1dt(self, fi1, fi, t):
        w0_2 = self.m * self.g * self.d / self.I
        beta = self.b / self.I
        return -w0_2 * math.sin(fi) - beta * fi1
    
    def dfidt(self, fi1, fi, t):
        return fi1

    def set_params(self, canvas: 'FigureCanvas', stB: QLabel, END_TIME=24*60*60, h=0.01, g=9.8, m=2, d=1, I=0.8, R=0.05, PSI0=math.radians(30), PSI10=0):
        self.canvas1 = canvas
        self.stB = stB

        self.END_TIME = END_TIME
        self.h = h
        self.g = g
        self.m = m
        self.d = d
        self.I = I
        self.R = R
        self.PSI0 = PSI0
        self.PSI01 = PSI10
        self.b = 6 * math.pi * 1.81 * 10 ** -5 * R * d

    def run(self):
        try:
            self.status_update.emit('Поток вычислений запущен...')
            
            psi = np.array([])
            time = np.array([])

            time2 = np.array([0])
            amp = np.array([self.PSI0])

            self.status_update.emit('Начинаем считывать данные...')
            i = 0
            if os.path.exists('values.bin'):
                for line in self.read_floats_numpy('values.bin'):
                    i += 1
                    yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4 = line
                    t += self.h
                    psi = np.append(psi, yi)
                    time = np.append(time, t)
                    self.status_update.emit(f'Актуальное время: {t:.3f} с / {self.END_TIME} с')
                    if i % 1000 == 0:
                        self.plot_update.emit(time, psi)
                    if t >= self.END_TIME:
                        break
                data = open('values.bin', 'ab')
                self.status_update.emit('Данные прочитаны')
            else:
                m1, m2, m3, m4, k1, k2, k3, k4 = 0, 0, 0, 0, 0, 0, 0, 0
                yi = self.PSI0
                y1i = self.PSI10
                data = open('values.bin', 'wb')
                self.status_update.emit('Данных нет, начинаю расчет')
            
            while t < self.END_TIME:
                i += 1
                y1i = y1i + (m1 + 2*m2 + 2*m3 + m4) / 6
                yi = yi + (k1 + 2*k2 + 2*k3 + k4) / 6
                psi = np.append(psi, yi)
                time = np.append(time, t)
                self.status_update.emit(f'Актуальное время: {t:.3f} с / {self.END_TIME} с')
                if len(psi) > 2:
                    if (psi[-3] < psi[-2]) and (psi[-2] > psi[-1]):
                        amp = np.append(amp, psi[-1])
                        time2 = np.append(time2, time[-2])
                    elif (psi[-3] > psi[-2]) and (psi[-2] < psi[-1]):
                        time2[-1] = time[-2] - time2[-1]
                m1 = self.h * self.dfi1dt(y1i, yi, t)
                k1 = self.h * self.dfidt(y1i, yi, t)
                m2 = self.h * self.dfi1dt(y1i + m1/2, yi + k1/2, t + self.h/2)
                k2 = self.h * self.dfidt(y1i + m1/2, yi + k1/2, t + self.h/2)
                m3 = self.h * self.dfi1dt(y1i + m2/2, yi + k2/2, t + self.h/2)
                k3 = self.h * self.dfidt(y1i + m2/2, yi + k2/2, t + self.h/2)
                m4 = self.h * self.dfi1dt(y1i + m3, yi + k3, t + self.h)
                k4 = self.h * self.dfidt(y1i + m3, yi + k3, t + self.h)
                np.array([yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4], dtype=np.float32).tofile(data)
                if i % 1000 == 0:
                    self.plot_update.emit(time, psi)
                t = t + self.h
            self.status_update.emit('Вычисления завершены')
            return super().run()
        except Exception as e:
            self.error_ocurred.emit(e)