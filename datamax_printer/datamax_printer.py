import socket
import serial

class DPLPrinter:
    SOH = '\x01'
    STX = '\x02'

    command_mode = True

    def __init__(self, printer_ip=None, printer_port=9100, com_port=None, baudrate=9600):
        """
        Инициализация принтера. Можно выбрать либо сетевое подключение (IP/порт), либо COM-порт.
        :param printer_ip: IP-адрес принтера (для сетевого подключения).
        :param printer_port: Порт принтера (по умолчанию 9100).
        :param com_port: Имя COM-порта (например, 'COM6').
        :param baudrate: Скорость передачи данных для COM-порта (по умолчанию 9600).
        """
        self.use_com = com_port is not None
        self.command_mode = True

        if self.use_com:
            # Инициализация COM-порта
            self.com_port = com_port
            self.baudrate = baudrate
            try:
                self.serial_connection = serial.Serial(com_port, baudrate, timeout=1)
                print(f"Connected to printer via COM port {com_port} at {baudrate} baud.")
            except serial.SerialException as e:
                raise RuntimeError(f"Failed to connect to COM port {com_port}: {e}")
        elif printer_ip is not None:
            # Инициализация TCP/IP соединения
            self.printer = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.connection_info = (printer_ip, printer_port)
            try:
                self.printer.connect(self.connection_info)
                print(f"Connected to printer at {printer_ip}:{printer_port}")
            except socket.error as e:
                raise RuntimeError(f"Failed to connect to printer at {printer_ip}:{printer_port}: {e}")
        else:
            raise ValueError("Either printer_ip or com_port must be specified.")

    def __send_to_printer(self, command: str):
        """
        Отправка команды на принтер.
        """
        print('Sent: ' + command)
        if self.use_com:
            # Отправка через COM-порт
            return self.serial_connection.write(command.encode('cp866'))
        else:
            # Отправка через TCP/IP
            return self.printer.send(command.encode('cp866'))

    def send_to_printer(self, command: str):
        return self.__send_to_printer(command)

    def __adjust_number_length(self, value: str, length: int):
        while len(value) < length:
            value = '0' + value
        return value

    def start_document(self):
        if not self.command_mode:
            raise RuntimeError('Already in label formatting mode')
        success = False
        if self.command_mode and self.__send_to_printer(f'{self.STX}L') == 2:
            self.__send_to_printer('D11\x0D')
            self.command_mode = False
            success = True
        return success

    def configure(self, border_bottom=0, imperial=False):
        if not self.command_mode:
            raise RuntimeError('Cannot configure printer label formatting mode')
        if imperial:
            self.__send_to_printer(f'{self.STX}n')
        else:
            self.__send_to_printer(f'{self.STX}m')

        sop = str(border_bottom)
        while len(sop) < 4:
            sop = '0' + sop
        self.__send_to_printer(f'{self.STX}O{sop}')

    def set_encoding(self, encoding: str = "CP"):
        """
        Устанавливает кодировку перед отправкой текста.
        :param encoding: Параметр кодировки (например, CP для CP866)
        """
        if self.command_mode:
            raise RuntimeError('Cannot set encoding in command mode')
        command = f'yS{encoding}\x0D'
        return self.__send_to_printer(command)

    def set_label(self, x_pos, y_pos, text, font_id, font_size, rotation=0):
        if self.command_mode:
            raise RuntimeError('Cannot print label in command mode')
        rot_value = 1
        if rotation == 90:
            rot_value = 2
        elif rotation == 180:
            rot_value = 3
        elif rotation == 270:
            rot_value = 4

        x_pos = self.__adjust_number_length(str(x_pos), 4)
        y_pos = self.__adjust_number_length(str(y_pos), 4)

        size = '000'
        width_multiplier = 1
        height_multiplier = 1
        if font_id == 9:
            size = 'A' + self.__adjust_number_length(str(font_size), 2)
        else:
            if len(font_size) == 2:
                width_multiplier = font_size[0]
                height_multiplier = font_size[1]

        data = str(rot_value) + str(font_id) + str(width_multiplier) + str(height_multiplier) + size + y_pos + x_pos + text + '\x0D'
        return self.__send_to_printer(data)

    def set_qr_code(self, x_pos, y_pos, data, size=8):
        if self.command_mode:
            raise RuntimeError('Cannot print qr-code in command mode')
        x_pos = str(x_pos)
        while len(x_pos) < 4:
            x_pos = '0' + x_pos

        y_pos = str(y_pos)
        while len(y_pos) < 4:
            y_pos = '0' + y_pos

        if size > 9:
            size = chr(ord('A') + (size - 10))
        command = f'1W1d{size}{size}000{y_pos}{x_pos}{data}\x0D\x0D'
        return self.__send_to_printer(command)

    def print(self):
        self.__send_to_printer('E')
        self.command_mode = True

    def close_connection(self):
        """
        Закрытие соединения.
        """
        if self.use_com:
            self.serial_connection.close()
        else:
            self.printer.close()
