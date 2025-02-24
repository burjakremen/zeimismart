import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
transmitter_pin = 18  # Пин GPIO для передатчика
GPIO.setup(transmitter_pin, GPIO.OUT)

def send_pulse(duration_high, duration_low):
    GPIO.output(transmitter_pin, GPIO.HIGH)
    time.sleep(duration_high / 1000000)  # Длительность в микросекундах
    GPIO.output(transmitter_pin, GPIO.LOW)
    time.sleep(duration_low / 1000000)

def send_packet(packet, repeats=4, pause_duration=175000):  # Пауза 175 мс
    binary_packet = ''.join(format(byte, '08b') for byte in packet)
    for _ in range(repeats):
        for bit in binary_packet:
            if bit == '0':
                send_pulse(423, 18546)  # Короткий импульс + короткая пауза
            else:
                send_pulse(632, 18546)  # Длинный импульс + длинная пауза (пример, уточните реальные значения)
        time.sleep(pause_duration / 1000000)  # Пауза между повторениями

# Пример пакета (9 байт)
packet = [0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09]
send_packet(packet, repeats=4, pause_duration=175000)

GPIO.cleanup()
