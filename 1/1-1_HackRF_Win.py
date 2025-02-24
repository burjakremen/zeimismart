import numpy as np
import pylibhackrf
import time
from struct import pack

# Параметры сигнала (в микросекундах, как в скриншоте)
SHORT_PULSE = 423  # Короткий импульс (HIGH)
LONG_PULSE = 632   # Длинный импульс (HIGH)
SHORT_GAP = 18546  # Короткая пауза (LOW, бит 0)
LONG_GAP = 55638   # Длинная пауза (LOW, бит 1, примерное значение)
PAUSE_BETWEEN_REPEATS = 175000  # Пауза между повторениями пакета (175 мс)
SAMPLE_RATE = 8e6  # Частота семплирования HackRF (8 МГц)
FREQUENCY = 433.906e6  # Частота передачи (433.906 МГц)

# Функция для генерации одного бита в виде IQ-данных
def generate_bit(bit, sample_rate=SAMPLE_RATE):
    duration_samples = int(sample_rate * (SHORT_PULSE + (LONG_GAP if bit == '1' else SHORT_GAP)) / 1e6)
    pulse_samples = int(sample_rate * (LONG_PULSE if bit == '1' else SHORT_PULSE) / 1e6)
    
    # Генерация сигнала: 1 (HIGH) — полный сигнал, 0 (LOW) — нули
    iq_data = np.zeros(2 * duration_samples, dtype=np.complex64)
    iq_data[:2 * pulse_samples] = 1.0 + 0j  # Импульс (полный сигнал для OOK)
    
    return iq_data

# Функция для генерации пакета
def generate_packet(packet, sample_rate=SAMPLE_RATE):
    binary_packet = ''.join(format(byte, '08b') for byte in packet)
    iq_data = np.array([], dtype=np.complex64)
    
    for bit in binary_packet:
        iq_data = np.concatenate((iq_data, generate_bit(bit, sample_rate)))
    
    return iq_data

# Функция для передачи через HackRF One
def transmit_hackrf(iq_data, frequency=FREQUENCY, sample_rate=SAMPLE_RATE):
    # Инициализация HackRF
    hackrf = pylibhackrf.HackRF()
    hackrf.open()
    
    # Настройка параметров
    hackrf.set_freq(frequency)
    hackrf.set_sample_rate(sample_rate)
    hackrf.set_amp_enable(True)  # Включение усиления
    
    # Передача данных (IQ в формате I/Q, по 8 бит на канал)
    iq_bytes = pack('<%db' % (2 * len(iq_data)), *np.concatenate((iq_data.real, iq_data.imag)).astype(np.int8))
    hackrf.write(iq_bytes)
    
    # Короткая задержка для завершения передачи
    time.sleep(len(iq_data) / sample_rate)
    
    hackrf.close()

# Главная функция для передачи пакета 4 раза
def send_packet_repeatedly(packet, repeats=4, pause_duration=PAUSE_BETWEEN_REPEATS):
    iq_packet = generate_packet(packet)
    
    for _ in range(repeats):
        transmit_hackrf(iq_packet)
        time.sleep(pause_duration / 1000000)  # Пауза в секундах

# Пример пакета (9 байт)
packet = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]

# Запуск передачи
if __name__ == "__main__":
    try:
        send_packet_repeatedly(packet, repeats=4, pause_duration=PAUSE_BETWEEN_REPEATS)
        print("Передача завершена успешно.")
    except Exception as e:
        print(f"Ошибка: {e}")
