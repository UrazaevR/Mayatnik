from PyQt6.QtCore import pyqtSignal, QThread
from PyQt6.QtWidgets import QLabel
import numpy as np
import math
from time import time as current_time


class RK4_Thread(QThread):
    error_ocurred = pyqtSignal(Exception)
    status_update = pyqtSignal(str)
    plot_update = pyqtSignal(np.ndarray, np.ndarray, np.ndarray, np.ndarray)

    def read_floats_numpy(self, filename):
        """Чтение групп с помощью numpy"""
        all_values = np.fromfile(filename, dtype=np.float32)

        if len(all_values) % 11 != 0:
            print(
                f"Предупреждение: количество значений ({len(all_values)}) не кратно 11"
            )

        for i in range(0, len(all_values), 11):
            yield all_values[i : i + 11]

    def dfi1dt(self, fi1, fi, t):
        w0_2 = self.g / self.d
        beta = self.b / self.I if self.real_beta else 0.04
        return -w0_2 * math.sin(fi) - beta * fi1
        # return -w0_2 * fi - beta * fi1

    def dfidt(self, fi1, fi, t):
        return fi1

    def set_params(
        self,
        canvas: "FigureCanvas",
        stB: QLabel,
        END_TIME=24 * 60 * 60,
        h=0.001,
        g=9.81,
        m=2.4,
        d=0.95,
        R=0.05,
        PSI0=math.radians(30),
        PSI10=0,
        real_beta: bool = False,
    ):
        self.canvas1 = canvas
        self.stB = stB

        self.END_TIME = END_TIME
        self.h = h
        self.g = g
        self.m = m
        self.d = d
        self.I = m * d**2
        self.R = R
        self.PSI0 = PSI0
        self.PSI10 = PSI10
        self.b = 6 * math.pi * (1.81 * 10**-5) * R * d**2
        self.real_beta = real_beta
        self.stop_flag = False

    def stop_calc(self):
        self.stop_flag = True

    def run(self):
        try:
            self.status_update.emit("Поток вычислений запущен...")
            step_count = int(self.END_TIME * (1 / self.h))
            # last_plot_update_time = 0

            # psi = np.array([self.PSI0])
            psi = np.zeros(step_count)
            psi[0] = self.PSI0

            # time = np.array([0])
            time = np.zeros(step_count)
            time[0] = 0

            time2 = np.array([])
            T = np.array([])
            amp = np.array([])

            i = 0

            m1, m2, m3, m4, k1, k2, k3, k4 = 0, 0, 0, 0, 0, 0, 0, 0
            yi = self.PSI0
            y1i = self.PSI10
            t = 0
            self.status_update.emit("Данных нет, начинаю расчет")

            while i < (step_count - 1) and not self.stop_flag:
                i += 1
                y1i = y1i + (m1 + 2 * m2 + 2 * m3 + m4) / 6
                yi = yi + (k1 + 2 * k2 + 2 * k3 + k4) / 6
                t = t + self.h

                # psi = np.append(psi, yi)
                psi[i] = yi

                # time = np.append(time, t)
                time[i] = t
                self.status_update.emit(
                    f"Актуальное время: {t:.3f} с / {self.END_TIME} с"
                )
                if i > 2:
                    if (psi[i-3] <= psi[i-2]) and (psi[i-2] >= psi[i-1]):
                        amp = np.append(amp, math.degrees(psi[i-2]))
                        time2 = np.append(time2, time[i-2])
                        if len(time2) > 1:
                            T = np.append(T, time2[-1] - time2[-2])
                if i % (step_count // 100) == 0:
                    self.plot_update.emit(time2, amp, amp[1:], T)
                    # last_plot_update_time = current_time()
                    # self.plot_update.emit(time2, amp)
                m1 = self.h * self.dfi1dt(y1i, yi, t)
                k1 = self.h * self.dfidt(y1i, yi, t)
                m2 = self.h * self.dfi1dt(y1i + m1 / 2, yi + k1 / 2, t + self.h / 2)
                k2 = self.h * self.dfidt(y1i + m1 / 2, yi + k1 / 2, t + self.h / 2)
                m3 = self.h * self.dfi1dt(y1i + m2 / 2, yi + k2 / 2, t + self.h / 2)
                k3 = self.h * self.dfidt(y1i + m2 / 2, yi + k2 / 2, t + self.h / 2)
                m4 = self.h * self.dfi1dt(y1i + m3, yi + k3, t + self.h)
                k4 = self.h * self.dfidt(y1i + m3, yi + k3, t + self.h)
            self.plot_update.emit(time2, amp, amp[1:], T)
            self.status_update.emit(
                "Вычисления остановлены"
            ) if self.stop_flag else self.status_update.emit("Вычисления завершены")
            # self.terminate()
            return super().run()
        except Exception as e:
            self.error_ocurred.emit(e)
