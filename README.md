**<ins> 1. Детальное описание алгоритма шифрования </ins>**

На основе предоставленных данных и результатов эмуляции я вывел алгоритм формирования пакетов для команд "Открыть" (right), "Закрыть" (left) и "Стоп" (stop). Алгоритм можно описать следующим образом:

**Структура пакета**

<ins> Каждый пакет состоит из 9 байтов: </ins>

* Байт 1 (b1) и Байт 2 (b2): Формируют префикс, уникальный для каждой команды. Префиксы циклически повторяются для каждой команды (16 вариантов на команду).
* Байт 3 (b3): Основной счётчик, уменьшающийся с фиксированным шагом (17, 51, 17, 119, 17, 34, 17, 51, 17, 119, 17, 51, 17, 255, 17, 51, 17, 119) и обнуляемый по модулю 256.
* Байт 4 (b4): Вспомогательный байт, изменяющийся в зависимости от интервала времени между пакетами, значения b3 и предыдущего b4. Он подвергается корректировкам на основе следующих правил:
  * Если b3 < 30, добавляется +17 к b4.
  * Если интервал времени > 12 секунд, b4 инвертируется с помощью XOR с 0x11.
  * Если интервал времени > 30 секунд, добавляется +34 к b4.
  * Если интервал < 5 секунд и команда меняется, добавляется +17 к b4.
  * Если интервал > 10 секунд и < 30 секунд, и b3 > 200, вычитается 17 из b4.
  * Если интервал < 2 секунд и b3 > 200, добавляется +1 к b4.
* Байт 5 (b5): b2 ^ 229.
* Байт 6 (b6): b2 ^ 23.
* Байт 7 (b7): b3 ^ 226.
* Байт 8 (b8): b4 ^ 1.
* Байт 9 (b9): Всегда 8 (закрывающий байт, вероятно, контрольная сумма или флаг).

<ins> Префиксы для команд </ins>
* **"Открыть" (right)**: b352, a243, 8061, 9170, 7f9e, 6e8f, 5dbc, 4cad, 3bda, 2acb, 19f8, 08e9, f716, e607, d534, c425.
* **"Закрыть" (left)**: d034, c125, 2fcb, 3eda, 0de9, 1cf8, 6b8f, 7a9e, 49ad, 58bc, a743, b652, 8561, 9470, e307, f216.
* **"Стоп" (stop)**: 688f, 799e, 4aad, 5bbc, 2ccb, 3dda, 1ff8, 0ee9, 9770, 8661, b552, a443, d334, c225, e007, f116.

<ins> Шаги (steps) </ins> 

Шаги для изменения b3: [17, 51, 17, 119, 17, 34, 17, 51, 17, 119, 17, 51, 17, 255, 17, 51, 17, 119]. Эти шаги повторяются циклически каждые 18 пакетов.

<ins> Начальные пакеты </ins> 

Каждый набор пакетов (для каждой команды) начинается с реального пакета, который задаёт начальные значения b3 и b4. Последующие пакеты вычисляются на основе предыдущих, времени и правил выше.

<ins> Временные интервалы </ins> 

Интервалы между пакетами (в секундах) вычисляются как разница между текущим и предыдущим временем (в формате DD.MM.YYYY HH:MM:SS:MS). Эти интервалы влияют на b4 согласно описанным правилам


**<ins> 2. Исходные команды до их кодирования  </ins>**

На основе данных и структуры пакетов я могу определить, что исходные команды представляют собой простые текстовые или бинарные сигналы, которые кодируются в пакеты с описанным выше алгоритмом. Предположительно, исходные команды выглядят так:

* **"Открыть" (right)**: Сигнал для открытия устройства (например, "OPEN" или 0x01).
* **"Закрыть" (left)**: Сигнал для закрытия устройства (например, "CLOSE" или 0x02).
* **"Стоп" (stop)**: Сигнал для остановки устройства (например, "STOP" или 0x03).
Эти команды преобразуются в серии пакетов с уникальными префиксами и динамическими байтами, чтобы обеспечить последовательность и уникальность для каждого устройства (например, OrangePi3 и Wemos D1). Поскольку точный формат исходных сигналов не указан, я предполагаю, что они представляют собой простые идентификаторы (например, числа 1, 2, 3), которые мапятся на соответствующие префиксы и алгоритм генерации.



**Python-код для OrangePi3:**
```
import serial
import time
from datetime import datetime

# Префиксы для каждой команды
prefixes_open = ["b352", "a243", "8061", "9170", "7f9e", "6e8f", "5dbc", "4cad", "3bda", "2acb", "19f8", "08e9", "f716", "e607", "d534", "c425"]
prefixes_close = ["d034", "c125", "2fcb", "3eda", "0de9", "1cf8", "6b8f", "7a9e", "49ad", "58bc", "a743", "b652", "8561", "9470", "e307", "f216"]
prefixes_stop = ["688f", "799e", "4aad", "5bbc", "2ccb", "3dda", "1ff8", "0ee9", "9770", "8661", "b552", "a443", "d334", "c225", "e007", "f116"]

# Шаги для b3
steps = [17, 51, 17, 119, 17, 34, 17, 51, 17, 119, 17, 51, 17, 255, 17, 51, 17, 119]

# Начальные пакеты (из данных)
initial_open = bytes.fromhex("b35220f5b745c2f4588")  # Первый пакет "Открыть"
initial_close = bytes.fromhex("d0344a94d123a895fe8")  # Первый пакет "Закрыть"
initial_stop = bytes.fromhex("688ffc2c6a981e2d778")  # Первый пакет "Стоп"

def parse_time(time_str):
    return datetime.strptime(time_str, "%d.%m.%Y %H:%M:%S:%f")

def generate_packet(counter, prev_packet, prev_time, command_prefixes, current_time, prev_command=None):
    prefix = bytes.fromhex(command_prefixes[counter % 16])
    b1, b2 = prefix[0], prefix[1]
    
    if counter == 0:
        return list(initial_open if command_prefixes == prefixes_open else 
                   initial_close if command_prefixes == prefixes_close else initial_stop)
    
    step = steps[(counter - 1) % 18]
    b3 = (prev_packet[2] - step) % 256
    interval = (current_time - prev_time).total_seconds() if prev_time else 0
    
    b4 = prev_packet[3]
    if b3 < 30:
        b4 = (b4 + 17) % 256
        if interval > 12:
            b4 = (b4 ^ 0x11) % 256
    elif interval > 30:
        b4 = (b4 + 34) % 256
    elif interval < 5 and prev_command and prev_command != command_prefixes:
        b4 = (b4 + 17) % 256
    elif interval > 10 and interval < 30 and b3 > 200:
        b4 = (b4 - 17) % 256 if b3 > 200 else b4
    elif interval < 2 and b3 > 200:
        b4 = (b4 + 1) % 256
    
    b5 = b2 ^ 229
    b6 = b2 ^ 23
    b7 = b3 ^ 226
    b8 = b4 ^ 1
    return [b1, b2, b3, b4, b5, b6, b7, b8, 8]

def send_command(command, ser, packet_count=50, delay=2.25):
    if command == "open":
        command_prefixes = prefixes_open
        prev_command = None
    elif command == "close":
        command_prefixes = prefixes_close
        prev_command = prefixes_open if prev_time_open else None  # Предыдущая команда для смены
    else:  # stop
        command_prefixes = prefixes_stop
        prev_command = prefixes_close if prev_time_close else None

    current_time = datetime.now()
    packets = []
    prev_packet = None
    prev_time = prev_time_open if command == "open" else (prev_time_close if command == "close" else prev_time_stop)

    for i in range(packet_count):
        packet = generate_packet(i, prev_packet, prev_time, command_prefixes, current_time, prev_command)
        packets.append(bytes(packet))
        prev_packet = packet
        prev_time = current_time
        current_time = datetime.now()  # Реальное время для следующего пакета

        # Отправка пакета через UART
        ser.write(bytes(packet))
        time.sleep(delay)  # Интервал между пакетами ~2.25 сек (как в данных)

    # Обновление глобальных времён
    global prev_time_open, prev_time_close, prev_time_stop
    if command == "open":
        prev_time_open = current_time
    elif command == "close":
        prev_time_close = current_time
    else:
        prev_time_stop = current_time

# Инициализация UART (пример для OrangePi3, /dev/ttyS1, 9600 baud)
ser = serial.Serial('/dev/ttyS1', 9600, timeout=1)

# Глобальные переменные для сохранения времени последнего пакета
prev_time_open = None
prev_time_close = None
prev_time_stop = None

# Пример использования
if __name__ == "__main__":
    # Отправка команды "Открыть"
    print("Отправка команды 'Открыть'...")
    send_command("open", ser)

    time.sleep(5)  # Пауза перед следующей командой

    # Отправка команды "Закрыть"
    print("Отправка команды 'Закрыть'...")
    send_command("close", ser)

    time.sleep(5)  # Пауза

    # Отправка команды "Стоп"
    print("Отправка команды 'Стоп'...")
    send_command("stop", ser)

    ser.close()
```

**C++-код для Wemos D1 (ESP8266):**
```
#include <Arduino.h>
#include <TimeLib.h>  // Библиотека для работы со временем
#include <SoftwareSerial.h>

// Префиксы для каждой команды (в виде массива байтов)
const char* prefixes_open[] = {"b352", "a243", "8061", "9170", "7f9e", "6e8f", "5dbc", "4cad", "3bda", "2acb", "19f8", "08e9", "f716", "e607", "d534", "c425"};
const char* prefixes_close[] = {"d034", "c125", "2fcb", "3eda", "0de9", "1cf8", "6b8f", "7a9e", "49ad", "58bc", "a743", "b652", "8561", "9470", "e307", "f216"};
const char* prefixes_stop[] = {"688f", "799e", "4aad", "5bbc", "2ccb", "3dda", "1ff8", "0ee9", "9770", "8661", "b552", "a443", "d334", "c225", "e007", "f116"};

// Шаги для b3
const uint8_t steps[] = {17, 51, 17, 119, 17, 34, 17, 51, 17, 119, 17, 51, 17, 255, 17, 51, 17, 119};

// Начальные пакеты (в виде hex-строк)
const char* initial_open = "b35220f5b745c2f4588";
const char* initial_close = "d0344a94d123a895fe8";
const char* initial_stop = "688ffc2c6a981e2d778";

// Глобальные переменные для хранения времени (в секундах с эпохи)
time_t prev_time_open = 0;
time_t prev_time_close = 0;
time_t prev_time_stop = 0;

SoftwareSerial serial(13, 15);  // RX, TX для Wemos D1 (D7, D8)

uint8_t hexToByte(char c) {
    if (c >= '0' && c <= '9') return c - '0';
    if (c >= 'a' && c <= 'f') return c - 'a' + 10;
    if (c >= 'A' && c <= 'F') return c - 'A' + 10;
    return 0;
}

void parseHexString(const char* hex, uint8_t* bytes, int len) {
    for (int i = 0; i < len; i += 2) {
        bytes[i / 2] = (hexToByte(hex[i]) << 4) | hexToByte(hex[i + 1]);
    }
}

void generatePacket(int counter, uint8_t* prev_packet, time_t prev_time, const char** command_prefixes, time_t current_time, const char** prev_command) {
    const char* prefix = command_prefixes[counter % 16];
    uint8_t b1, b2;
    parseHexString(prefix, &b1, 2);  // Берем первые 2 байта префикса

    if (counter == 0) {
        parseHexString(initial_open, prev_packet, 9);  // Начальный пакет для "Открыть"
        if (command_prefixes == prefixes_close) parseHexString(initial_close, prev_packet, 9);
        if (command_prefixes == prefixes_stop) parseHexString(initial_stop, prev_packet, 9);
        return;
    }

    uint8_t step = steps[(counter - 1) % 18];
    uint8_t b3 = (prev_packet[2] - step) % 256;
    float interval = (current_time - prev_time);

    uint8_t b4 = prev_packet[3];
    if (b3 < 30) {
        b4 = (b4 + 17) % 256;
        if (interval > 12) b4 = (b4 ^ 0x11) % 256;
    } else if (interval > 30) {
        b4 = (b4 + 34) % 256;
    } else if (interval < 5 && prev_command && prev_command != command_prefixes) {
        b4 = (b4 + 17) % 256;
    } else if (interval > 10 && interval < 30 && b3 > 200) {
        b4 = (b4 - 17) % 256;
    } else if (interval < 2 && b3 > 200) {
        b4 = (b4 + 1) % 256;
    }

    uint8_t b5 = b2 ^ 229;
    uint8_t b6 = b2 ^ 23;
    uint8_t b7 = b3 ^ 226;
    uint8_t b8 = b4 ^ 1;
    prev_packet[0] = b1; prev_packet[1] = b2; prev_packet[2] = b3;
    prev_packet[3] = b4; prev_packet[4] = b5; prev_packet[5] = b6;
    prev_packet[6] = b7; prev_packet[7] = b8; prev_packet[8] = 8;
}

void sendCommand(const char* command, int packet_count = 50, float delay_sec = 2.25) {
    const char** command_prefixes = prefixes_open;
    const char** prev_command = NULL;
    if (strcmp(command, "close") == 0) command_prefixes = prefixes_close;
    else if (strcmp(command, "stop") == 0) command_prefixes = prefixes_stop;

    time_t current_time = now();  // Текущее время в секундах
    uint8_t prev_packet[9] = {0};
    time_t prev_time = prev_time_open;
    if (command_prefixes == prefixes_close) prev_time = prev_time_close;
    else if (command_prefixes == prefixes_stop) {
        prev_time = prev_time_stop;
        if (prev_time_close > 0) prev_command = prefixes_close;
    }

    for (int i = 0; i < packet_count; i++) {
        generatePacket(i, prev_packet, prev_time, command_prefixes, current_time, prev_command);
        serial.write(prev_packet, 9);  // Отправка пакета через Serial
        delay(delay_sec * 1000);  // Задержка в миллисекундах (2.25 сек)

        prev_time = current_time;
        current_time = now();  // Обновляем время
    }

    // Сохранение времени последней команды
    if (command_prefixes == prefixes_open) prev_time_open = current_time;
    else if (command_prefixes == prefixes_close) prev_time_close = current_time;
    else prev_time_stop = current_time;
}

void setup() {
    Serial.begin(9600);  // Инициализация Serial для отладки
    serial.begin(9600);  // Инициализация SoftwareSerial для передачи пакетов

    // Настройка времени (пример, нужно синхронизировать с RTC или NTP)
    setTime(26, 52, 12, 26, 12, 2024);  // Установить начальное время (DD, HH, MM, DD, MM, YYYY)
}

void loop() {
    // Пример отправки команд (можно запускать по триггеру, например, по кнопке)
    sendCommand("open");  // Открыть
    delay(5000);  // Пауза 5 сек
    sendCommand("close");  // Закрыть
    delay(5000);  // Пауза 5 сек
    sendCommand("stop");  // Стоп
    delay(5000);  // Пауза 5 сек
}
```

Примечания к коду:

* OrangePi3 (Python): Код предполагает использование UART (/dev/ttyS1) с baud rate 9600. Можно адаптировать порт и скорость под конкретное оборудование. Для работы с реальным временем используется datetime.now().
* Wemos D1 (C++): Код использует SoftwareSerial для отправки пакетов через UART. Для работы со временем необходима синхронизация (например, через NTP или RTC). Если требуется WiFi, можно добавить отправку через UDP/TCP, заменив serial.write на отправку через WiFi.
* Оба кода генерируют пакеты с интервалом ~2.25 секунды (как в данных), но интервал можно настроить под нужды устройства.
