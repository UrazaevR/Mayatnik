import math
import matplotlib.pyplot as plt
import os
import numpy as np

end_time = 24 * 60 * 60

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


psi = np.array([])
time = np.array([])

time2 = np.array([0])
amp = np.array([PSI0])

h = 0.01
t = 0

print('Начинаем считывать данные...')
if os.path.exists('values.bin'):
    for line in read_floats_numpy('values.bin'):
        yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4 = line
        t += h
        psi = np.append(psi, yi)
        time = np.append(time, t)
        print(f'\r{' ' * 50}\rАктуальное время: {t:.3f} с / {end_time} с', end='')
        if t >= end_time:
            break
    data = open('values.bin', 'ab')
    print('\nДанные прочитаны')
else:
    m1, m2, m3, m4, k1, k2, k3, k4 = 0, 0, 0, 0, 0, 0, 0, 0
    yi = PSI0
    y1i = PSI10
    data = open('values.bin', 'wb')
    print('Данных нет, начинаю расчет')


while t < end_time:
    y1i = y1i + (m1 + 2*m2 + 2*m3 + m4) / 6
    yi = yi + (k1 + 2*k2 + 2*k3 + k4) / 6
    psi = np.append(psi, yi)
    time = np.append(time, t)
    print(f'\rАктуальное время: {t:.3f} с / {end_time} с', end='')
    if len(psi) > 2:
        if (psi[-3] < psi[-2]) and (psi[-2] > psi[-1]):
            amp = np.append(amp, psi[-1])
            time2 = np.append(time2, time[-2])
        elif (psi[-3] > psi[-2]) and (psi[-2] < psi[-1]):
            time2[-1] = time[-2] - time2[-1]
    m1 = h * dfi1dt(y1i, yi, t)
    k1 = h * dfidt(y1i, yi, t)
    m2 = h * dfi1dt(y1i + m1/2, yi + k1/2, t + h/2)
    k2 = h * dfidt(y1i + m1/2, yi + k1/2, t + h/2)
    m3 = h * dfi1dt(y1i + m2/2, yi + k2/2, t + h/2)
    k3 = h * dfidt(y1i + m2/2, yi + k2/2, t + h/2)
    m4 = h * dfi1dt(y1i + m3, yi + k3, t + h)
    k4 = h * dfidt(y1i + m3, yi + k3, t + h)
    np.array([yi, y1i, t, m1, m2, m3, m4, k1, k2, k3, k4], dtype=np.float32).tofile(data)
    t = t + h
print()

plt.plot(time, list(math.degrees(x) for x in psi))
plt.show()