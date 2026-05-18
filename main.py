import os
import sys
import math

# os.environ["QT_API"] = "PyQt6"

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QMessageBox,
)
from matplotlib.backends.backend_qtagg import FigureCanvas
from matplotlib.backends.backend_qtagg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure

# from RK4 import RK4_Thread
from RK4_not_file import RK4_Thread


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height))
        self.axes = fig.add_subplot(111)
        super().__init__(fig)


class Window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(
            "Зависимость периода колебаний от амплитуды колебаний маятника"
        )
        self.resize(1000, 500)
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()
        plot_layout = QHBoxLayout()
        left_plot = QVBoxLayout()
        right_plot = QVBoxLayout()
        self.setLayout(layout)

        # создание графика 1
        fig = Figure()
        self.ax = fig.add_subplot()
        self.canvas = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas.axes.set_xlim(0, 500)
        self.canvas.axes.set_ylim(0, 60)
        self.canvas.axes.set_autoscale_on(False)
        self.canvas.axes.set_xlabel("Время, с")
        self.canvas.axes.set_ylabel("Амплитуда, град")
        left_plot.addWidget(self.canvas)
        toolbar = NavigationToolbar(self.canvas, self)
        left_plot.addWidget(toolbar)

        # создание графика 2
        fig2 = Figure()
        self.ax2 = fig2.add_subplot()
        self.canvas2 = MplCanvas(self, width=5, height=4, dpi=100)
        self.canvas2.axes.set_xlim(0, 60)
        self.canvas2.axes.set_ylim(0, 3)
        self.canvas2.axes.set_autoscale_on(False)
        self.canvas2.axes.set_xlabel("Амплитуда, град")
        self.canvas2.axes.set_ylabel("Период, с")
        right_plot.addWidget(self.canvas2)
        toolbar = NavigationToolbar(self.canvas2, self)
        right_plot.addWidget(toolbar)

        # создание панели переменных
        value_box = QWidget()
        value_box.setMaximumWidth(400)
        value_layout = QVBoxLayout(value_box)
        
        value_layout.addWidget(QLabel("Время окончания эксперимента:"))
        self.END_TIME_edit = QLineEdit()
        self.END_TIME_edit.setText("86400")
        value_layout.addWidget(self.END_TIME_edit)
        
        self.g_label = QLabel("Ускорение свободного падения g:")
        self.g_edit = QLineEdit()
        self.g_edit.setText("9.81")
        self.g_label.setVisible(False)
        self.g_edit.setVisible(False)
        value_layout.addWidget(self.g_label)
        value_layout.addWidget(self.g_edit)
        
        value_layout.addWidget(QLabel("Шаг по времени h:"))
        self.h_edit = QLineEdit()
        self.h_edit.setText("0.001")
        value_layout.addWidget(self.h_edit)
        
        value_layout.addWidget(QLabel("Масса маятника m:"))
        self.m_edit = QLineEdit()
        self.m_edit.setText("2.4")
        value_layout.addWidget(self.m_edit)
        
        value_layout.addWidget(QLabel("Длина маятника:"))
        self.d_edit = QLineEdit()
        self.d_edit.setText("0.95")
        value_layout.addWidget(self.d_edit)
        
        value_layout.addWidget(QLabel("Радиус маятника R:"))
        self.R_edit = QLineEdit()
        self.R_edit.setText("0.05")
        value_layout.addWidget(self.R_edit)
        
        value_layout.addWidget(QLabel("Начальный угол отклонения PSI0:"))
        self.PSI0_edit = QLineEdit()
        self.PSI0_edit.setText("30")
        value_layout.addWidget(self.PSI0_edit)
        
        # Скрываем начальную скорость, но оставляем для проверок
        self.PSI10_label = QLabel("Начальная скорость PSI10:")
        self.PSI10_edit = QLineEdit()
        self.PSI10_edit.setText("0")
        self.PSI10_label.setVisible(False)
        self.PSI10_edit.setVisible(False)
        value_layout.addWidget(self.PSI10_label)
        value_layout.addWidget(self.PSI10_edit)
        
        # Чекбокс по умолчанию True
        self.real_beta_check = QCheckBox(text="Использовать реальную beta")
        self.real_beta_check.setChecked(True)
        self.real_beta_check.setVisible(False)
        value_layout.addWidget(self.real_beta_check)

        plot_layout.addLayout(left_plot)
        plot_layout.addLayout(right_plot)
        plot_layout.addWidget(value_box)
        layout.addLayout(plot_layout)

        self.calculate_but = QPushButton("Рассчитать", self)
        self.calculate_but.setMaximumHeight(50)
        self.stop_but = QPushButton("Стоп", self)
        self.stop_but.setDisabled(True)

        button_layout.addWidget(self.calculate_but)
        button_layout.addWidget(self.stop_but)
        self.statusLab = QLabel()
        self.statusLab.setMaximumHeight(30)
        layout.addLayout(button_layout)
        layout.addWidget(self.statusLab)

        self.calculate_but.clicked.connect(self.draw_plot)
        self.stop_but.clicked.connect(self.stop_calulation)

    def stop_calulation(self):
        self.calc_thread.stop_calc()
        self.calculate_but.setEnabled(True)
        self.stop_but.setDisabled(True)
        # self.calc_thread.wait()

    def _update_plot(self, x1, y1, x2, y2):
        self.canvas.axes.cla()
        self.canvas.axes.plot(x1, y1)
        self.canvas2.axes.cla()
        # Проверка на пустые массивы
        if len(y2) > 0:
            self.canvas2.axes.plot([-100, 1000], [y2[0], y2[0]], color='red')
        self.canvas2.axes.plot(x2, y2)
        if len(x2) > 0:
            self.canvas2.axes.set_xlim(x2[-1], x2[0])
        # Используем фиксированное значение g=9.81 для расчета предела
        self.canvas2.axes.set_ylim(0, round(2 * 3.14 * float(self.d_edit.text()) ** 0.5 / 9.81 ** 0.5) + 1)
        self.canvas.axes.set_xlim(
            0, round(float(self.END_TIME_edit.text()) / 100, 1) * 100
        )
        self.canvas.axes.set_ylim(0, float(self.PSI0_edit.text()) + 10)
        self.canvas.axes.set_xlabel("Время, с")
        self.canvas.axes.set_title("Зависимость амплитуды от времени")
        self.canvas.axes.set_ylabel("Амплитуда, град")
        self.canvas2.axes.set_xlabel("Амплитуда, град")
        self.canvas2.axes.set_ylabel("Период, с")
        self.canvas2.axes.set_title("Зависимость периода от амплитуды")
        self.canvas.draw()
        self.canvas2.draw()

    def check_input(self) -> tuple[bool, str]:
        # Сохраняем все значения, включая скрытые поля
        values = [self.END_TIME_edit.text().strip(),
                self.g_edit.text().strip(),  # Сохраняем проверку g
                self.h_edit.text().strip(), 
                self.m_edit.text().strip(), 
                self.d_edit.text().strip(), 
                self.R_edit.text().strip(), 
                self.PSI0_edit.text().strip(),
                self.PSI10_edit.text().strip()]  # Сохраняем проверку начальной скорости
        
        # проверка на то, что все значения не пустые
        if not all(values):
            return False, 'Все значения должны быть заполнены'
        try:
            values = list(map(float, values))
        except ValueError:
            return False, 'Все значения должны быть числами'
        
        # Проверки для всех полей (включая скрытые)
        if values[0] < 100:
            return False, 'Время должно быть больше 100'
        if values[1] <= 0:
            return False, 'Ускорение свободного падения должно быть больше 0'
        if values[2] <= 0:
            return False, 'Шаг должен быть больше 0'
        if values[0] <= values[2]:
            return False, 'Шаг должен быть меньше конечного времени'
        if 0.01 < values[2]:
            return False, 'Шаг нельзя задать больше чем 0.01 с'
        if values[3] <= 0:
            return False, 'Масса должна быть больше 0'
        if values[3] > 300:
            return False, 'Масса маятника не может превышать 300 кг'
        if values[4] <= 0:
            return False, 'Длина маятника должна быть больше 0'
        if values[4] > 4:
            return False, 'Длина маятника не может превышать 4 метра'
        if values[5] <= 0:
            return False, 'Радиус маятника должен быть больше 0'
        if values[5] > values[4] / 3:
            return False, 'Радиус маятника должен быть более чем в 3 раза меньше его длины'
        if not (-90 <= values[6] <= 90):
            return False, 'Начальный угол должен лежать в диапазоне от -90 до 90 градусов'
        # Проверка для начальной скорости (любое число допустимо, но оставляем на всякий случай)
        if not (-100 < values[7] < 100):
            return False, 'Начальная скорость должна быть в разумных пределах'
        
        # Проверка плотности маятника
        # Объем сферического маятника (шар)
        volume = (4/3) * math.pi * (values[5] ** 3) / 2  # объем шара радиуса R пополам
        density = values[3] / volume  # плотность = масса / объем
        
        # Плотность осмия (самого плотного материала на Земле) - 22600 кг/м³
        max_density = 22600
        
        if density > max_density:
            return False, f'Слишком большая плотность маятника: {density:.0f} кг/м³ (максимально допустимая {max_density} кг/м³). Уменьшите массу или увеличьте радиус.'
        
        # Дополнительная проверка на слишком маленькую плотность (менее плотности пенопласта ~10 кг/м³)
        min_density = 10
        if density < min_density:
            return False, f'Слишком маленькая плотность маятника: {density:.0f} кг/м³ (минимально допустимая {min_density} кг/м³). Увеличьте массу или уменьшите радиус.'
        
        return True, 'OK'

    def draw_plot(self):
        ok, error = self.check_input()
        if ok:
            self.calculate_but.setDisabled(True)
            self.stop_but.setEnabled(True)
            self.calc_thread = RK4_Thread()
            self.calc_thread.finished.connect(
                lambda *x: (
                    self.calculate_but.setEnabled(True) == self.stop_but.setDisabled(True)
                )
            )
            # self.calc_thread.finished.connect(self.calc_thread.deleteLater)
            self.calc_thread.error_ocurred.connect(lambda x: print(x))
            self.calc_thread.status_update.connect(self.statusLab.setText)
            self.calc_thread.plot_update.connect(self._update_plot)
            kwargs = {
                "END_TIME": float(self.END_TIME_edit.text()),
                "h": float(self.h_edit.text()),
                "g": float(self.g_edit.text()),
                "m": float(self.m_edit.text()),
                "d": float(self.d_edit.text()),
                "R": float(self.R_edit.text()),
                "PSI0": math.radians(float(self.PSI0_edit.text())),
                "PSI10": math.radians(float(self.PSI10_edit.text())),
                "real_beta": self.real_beta_check.isChecked(),
            }
            self.calc_thread.set_params(self.canvas, self.statusLab, **kwargs)
            self.calc_thread.start()
        else:
            QMessageBox.warning(self, 'Ошибка ввода', error)
            


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Загрузка QSS стиля
    try:
        with open("style.qss", "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except FileNotFoundError:
        print("Файл style.qss не найден, использую стиль по умолчанию")
    
    win = Window()
    win.show()
    app.exec()