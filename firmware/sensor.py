from machine import Pin, UART
import time, onewire, ds18x20
import random

# Mengimpor manager MQTT
from network_manager import MQQTManager

# Membuat koneksi MQTT global 
global mqqt_manager, mqtt_client, pin, MESSAGE_INTERVAL

# Inisialisasi variabel global
MESSAGE_INTERVAL = 5
pin = Pin(23, Pin.OUT)
mqqt_manager = MQQTManager()

# Fungsi untuk koneksi MQTT (hanya dipanggil sekali)
def setup_mqtt_connection():
    try:
        client = mqqt_manager.connect_and_subscribe()
        print("MQTT Connected Successfully")
        return client
    except OSError as e:
        print("MQTT connection failed:", e)
        mqqt_manager.restart_and_reconnect()
        return None

# Koneksi hanya satu kali di awal program
mqtt_client = setup_mqtt_connection()

class Temperature:
    def __init__(self, sensor_id):
        # Gunakan client dan manager MQTT yang telah dibuat di level global
        self.client = mqtt_client
        self.mqqt = mqqt_manager
        self.id_sensor = sensor_id
        self.pin = Pin(19)
        self.ds_sensor = ds18x20.DS18X20(onewire.OneWire(self.pin))
        try:
            self.roms = self.ds_sensor.scan()
            if not self.roms:
                print("No DS18B20 sensors found!")
                self.sensor_available = False
            else:
                print("Sensor DS18B20 ditemukan:", self.roms)
                self.sensor_available = True
        except Exception as e:
            print("Error scanning for sensors:", e)
            self.sensor_available = False
            self.roms = []
        
    
    def read_temperature(self):
        # Fungsi ini hanya membaca suhu tanpa loop
        # Check if sensor tersedia
        if not self.sensor_available or not self.roms:
            print("No sensor available")
            return None
            
        try:
            # Convert temperature 
            self.ds_sensor.convert_temp()
            # Wait for conversion to complete (750ms is minimum for 12-bit resolution)
            time.sleep_ms(1000)
            # Read temperature
            return self.ds_sensor.read_temp(self.roms[0])
        except Exception as e:
            print("Error reading temperature:", e)
            return None
    
    def send_temperature_once(self):
        # Fungsi untuk mengirim data suhu sekali saja
        try:
            temperature = self.read_temperature()
            if temperature is not None:
                self.mqqt.publish("Temperatur", temperature, self.client, self.id_sensor)
            return temperature
        except Exception as e:
            print("Error sending temperature:", e)
            return None
            
    def start_monitoring(self):
        # PERHATIAN: Fungsi ini berisi loop tak terbatas!
        last_message = 0
        
        print("Starting temperature monitoring...")
        while True:
            pin.value(1)  # LED indikator ON
            self.ds_sensor.convert_temp()
            try:
                if (time.time() - last_message) > MESSAGE_INTERVAL:
                    temperature = self.read_temperature()
                    if temperature is not None:
                        self.mqqt.publish("Temperatur", temperature, self.client, self.id_sensor)
                        print("Temperature:", temperature)
                        last_message = time.time()
            except OSError as e:
                print("MQTT connection failed:", e)
                self.mqqt.restart_and_reconnect()
            except Exception as e:
                print("Error in monitoring loop:", e)
                time.sleep(5)  # Delay before retrying
            
            pin.value(0)  # LED indikator OFF
            time.sleep(1)


class PZEM_RS485:
    """Kelas untuk komunikasi dengan sensor PZEM menggunakan protokol Modbus-RTU melalui RS-485"""
    
    # Default addresses
    DEFAULT_ADDR = 0x01    # Alamat default pabrik (0x01)
    SECOND_ADDR = 0x02     # Alamat kedua yang direkomendasikan (0x02)
    BROADCAST_ADDR = 0x00  # Alamat broadcast (0x00)
    GENERAL_ADDR = 0xF8    # Alamat umum untuk kalibrasi (0xF8)
    
    # Register Address dari dokumentasi
    REG_VOLTAGE = 0x0000    # Tegangan (0.01 V resolution)
    REG_CURRENT = 0x0001    # Arus (0.01 A resolution)
    REG_POWER_LOW = 0x0002  # Daya - 16 bit bawah (0.1 W resolution)
    REG_POWER_HIGH = 0x0003 # Daya - 16 bit atas
    REG_ENERGY_LOW = 0x0004 # Energi - 16 bit bawah (1 Wh resolution)
    REG_ENERGY_HIGH = 0x0005 # Energi - 16 bit atas
    REG_HIGH_VOLTAGE_ALARM = 0x0006 # Status alarm tegangan tinggi
    REG_LOW_VOLTAGE_ALARM = 0x0007 # Status alarm tegangan rendah
    
    # Parameter Register
    REG_HIGH_VOLTAGE_THRESHOLD = 0x0000 # Batas alarm tegangan tinggi
    REG_LOW_VOLTAGE_THRESHOLD = 0x0001 # Batas alarm tegangan rendah
    REG_MODBUS_ADDR = 0x0002 # Alamat modbus RTU
    
    # Function Codes
    FC_READ_HOLDING_REGISTER = 0x03 # Read Holding Registers
    FC_READ_INPUT_REGISTER = 0x04 # Read Input Registers
    FC_WRITE_SINGLE_REGISTER = 0x06 # Write Single Register
    FC_CALIBRATION = 0x41 # Calibration (hanya untuk internal)
    FC_RESET_ENERGY = 0x42 # Reset Energi
    
    
    def __init__(self, uart_id=1, tx_pin=17, rx_pin=16, de_pin=25, re_pin=26, 
                 slave_addr=None, id_sensor=1):
        """
        Inisialisasi komunikasi RS-485 untuk sensor PZEM
        
        Args:
            uart_id: ID UART (default: 1)
            tx_pin: Pin TX (default: 17)
            rx_pin: Pin RX (default: 16)
            de_pin: Pin DE untuk kontrol transmisi (default: 25)
            re_pin: Pin RE untuk kontrol penerimaan (default: 26)
            slave_addr: Alamat slave sensor (default: DEFAULT_ADDR jika None)
            id_sensor: ID sensor untuk MQTT (default: 1)
        """
        
        self.id_sensor = id_sensor
        
        # Inisialisasi UART - default baudrate 9600, 8 data bits, 2 stop bits, no parity
        self.uart = UART(uart_id, baudrate=9600, tx=tx_pin, rx=rx_pin, 
                          bits=8, parity=None, stop=2, timeout=1000)
        
        # Inisialisasi pin DE (Driver Enable) untuk kontrol transmisi
        self.de_pin = Pin(de_pin, Pin.OUT)
        self.de_pin.value(0)  # Nonaktifkan driver transmisi secara default
        
        # Inisialisasi pin RE (Receiver Enable) untuk kontrol penerimaan
        self.re_pin = Pin(re_pin, Pin.OUT)
        self.re_pin.value(0)  # Aktifkan receiver (active low pada kebanyakan modul)
        
        # Alamat slave sensor, gunakan default jika tidak ditentukan
        self.slave_addr = self.DEFAULT_ADDR if slave_addr is None else slave_addr
        
        # Gunakan client dan manager MQTT yang telah dibuat di level global
        self.client = mqtt_client
        self.mqqt = mqqt_manager
    
    def _send_command(self, function_code, register_addr, num_registers=1, register_value=None):
        """
        Mengirim perintah Modbus RTU ke sensor
        
        Args:
            function_code: Kode fungsi Modbus
            register_addr: Alamat register
            num_registers: Jumlah register (default: 1)
            register_value: Nilai register untuk operasi penulisan (None untuk operasi pembacaan)
            
        Returns:
            bytearray: Data respons atau None jika gagal
        """
        
        # Buat paket data
        packet = bytearray([self.slave_addr, function_code])
        
        # Tambahkan alamat register (2 byte)
        packet.append((register_addr >> 8) & 0xFF)  # High byte
        packet.append(register_addr & 0xFF)         # Low byte
        
        if function_code == self.FC_WRITE_SINGLE_REGISTER and register_value is not None:
            # Untuk fungsi penulisan, tambahkan nilai register (2 byte)
            packet.append((register_value >> 8) & 0xFF)  # High byte
            packet.append(register_value & 0xFF)         # Low byte
        else:
            # Untuk fungsi pembacaan, tambahkan jumlah register (2 byte)
            packet.append((num_registers >> 8) & 0xFF)  # High byte
            packet.append(num_registers & 0xFF)         # Low byte
        
        # Hitung dan tambahkan CRC
        crc = self._calculate_crc(packet)
        packet.append(crc & 0xFF)          # CRC low byte
        packet.append((crc >> 8) & 0xFF)   # CRC high byte
        
        # Set mode transmit
        self.de_pin.value(1)  # Aktifkan driver transmisi
        self.re_pin.value(1)  # Nonaktifkan receiver (active low)
        time.sleep_ms(1)      # Delay sebelum transmisi
        
        # Kirim data
        self.uart.write(packet)
        
        # Estimasi waktu transmisi (dalam ms) dan tambahkan sedikit margin
        # (Panjang data * 10 bit/byte) / (baudrate/1000) + margin
        tx_time_ms = (len(packet) * 10) / (9600 / 1000) + 5
        time.sleep_ms(int(tx_time_ms))
        
        # Set mode receive
        self.de_pin.value(0)  # Nonaktifkan driver transmisi
        self.re_pin.value(0)  # Aktifkan receiver (active low)
        
        # Baca respons
        # Hitung ukuran respons yang diharapkan
        if function_code == self.FC_READ_INPUT_REGISTER or function_code == self.FC_READ_HOLDING_REGISTER:
            # Respons: slave_addr(1) + func_code(1) + byte_count(1) + data(2*num_registers) + crc(2)
            expected_bytes = 5 + (2 * num_registers)
        elif function_code == self.FC_WRITE_SINGLE_REGISTER:
            # Respons: slave_addr(1) + func_code(1) + reg_addr(2) + reg_value(2) + crc(2)
            expected_bytes = 8
        else:
            expected_bytes = 8  # Default minimal
        
        # Tunggu respons
        timeout = 500  # Timeout dalam ms
        start_time = time.ticks_ms()
        
        while self.uart.any() < expected_bytes:
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                print("Timeout saat menunggu respons")
                return None
            time.sleep_ms(10)
        
        # Baca respons
        response = self.uart.read()
        
        # Cek respons valid
        if not response or len(response) < 5:  # Respons terpendek: slave_addr(1) + func_code(1) + err_code(1) + crc(2)
            print("Respons tidak valid atau terlalu pendek")
            return None
        
        # Cek error
        if (response[1] & 0x80) == 0x80:
            error_code = response[2]
            error_msgs = {
                0x01: "Fungsi tidak legal",
                0x02: "Alamat tidak legal",
                0x03: "Data tidak legal",
                0x04: "Error pada slave"
            }
            if error_code in error_msgs:
                print("Error Modbus: " + error_msgs[error_code])
            else:
                print("Error Modbus: Kode error tidak dikenal: " + str(error_code))
            return None
        
        # Verifikasi CRC
        received_crc = (response[-1] << 8) | response[-2]
        calculated_crc = self._calculate_crc(response[:-2])
        if received_crc != calculated_crc:
            print("Error CRC: " + str(received_crc) + " != " + str(calculated_crc))
            return None
        
        return response
    
    def _calculate_crc(self, data):
        """
        Hitung CRC-16 Modbus
        
        Args:
            data: Bytearray data
            
        Returns:
            int: Nilai CRC-16
        """
        crc = 0xFFFF
        
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc >>= 1
                    crc ^= 0xA001
                else:
                    crc >>= 1
        
        return crc
    
    def change_address(self, new_addr):
        """
        Mengubah alamat Modbus dari sensor PZEM
        
        Args:
            new_addr: Alamat baru (range: 0x01-0xF7)
            
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        # Validasi alamat
        if new_addr < 0x01 or new_addr > 0xF7:
            print("Alamat tidak valid. Harus dalam rentang 0x01-0xF7")
            return False
        
        # Kirim perintah untuk mengubah alamat
        response = self._send_command(
            self.FC_WRITE_SINGLE_REGISTER, 
            self.REG_MODBUS_ADDR, 
            register_value=new_addr
        )
        
        if response and len(response) >= 8:
            # Periksa apakah response valid
            reg_addr = (response[2] << 8) | response[3]
            reg_value = (response[4] << 8) | response[5]
            
            if reg_addr == self.REG_MODBUS_ADDR and reg_value == new_addr:
                print(f"Alamat berhasil diubah dari {self.slave_addr} ke {new_addr}")
                # Update alamat pada instance saat ini
                self.slave_addr = new_addr
                return True
            else:
                print("Respons tidak sesuai yang diharapkan")
                return False
        else:
            print("Gagal mengubah alamat")
            return False
    
    def read_voltage(self):
        """
        Baca nilai tegangan dari sensor
        
        Returns:
            float: Nilai tegangan dalam volt atau None jika gagal
        """
        response = self._send_command(self.FC_READ_INPUT_REGISTER, self.REG_VOLTAGE, 1)
        if response and len(response) >= 5:
            voltage_raw = (response[3] << 8) | response[4]
            return voltage_raw * 0.01  # 1LSB = 0.01V
        return None
    
    def read_current(self):
        """
        Baca nilai arus dari sensor
        
        Returns:
            float: Nilai arus dalam ampere atau None jika gagal
        """
        response = self._send_command(self.FC_READ_INPUT_REGISTER, self.REG_CURRENT, 1)
        if response and len(response) >= 5:
            current_raw = (response[3] << 8) | response[4]
            return current_raw * 0.01  # 1LSB = 0.01A
        return None
    
    def read_power(self):
        """
        Baca nilai daya dari sensor
        
        Returns:
            float: Nilai daya dalam watt atau None jika gagal
        """
        response = self._send_command(self.FC_READ_INPUT_REGISTER, self.REG_POWER_LOW, 2)
        if response and len(response) >= 7:
            power_low = (response[3] << 8) | response[4]
            power_high = (response[5] << 8) | response[6]
            power_raw = (power_high << 16) | power_low
            return power_raw * 0.1  # 1LSB = 0.1W
        return None
    
    def read_energy(self):
        """
        Baca nilai energi dari sensor
        
        Returns:
            int: Nilai energi dalam watt-jam atau None jika gagal
        """
        response = self._send_command(self.FC_READ_INPUT_REGISTER, self.REG_ENERGY_LOW, 2)
        if response and len(response) >= 7:
            energy_low = (response[3] << 8) | response[4]
            energy_high = (response[5] << 8) | response[6]
            energy_raw = (energy_high << 16) | energy_low
            return energy_raw  # 1LSB = 1Wh
        return None
    
    def read_all_parameters(self):
        """
        Baca semua parameter pengukuran dari sensor
        
        Returns:
            dict: Dictionary berisi semua parameter atau None jika gagal
        """
        response = self._send_command(self.FC_READ_INPUT_REGISTER, self.REG_VOLTAGE, 8)
        if response and len(response) >= 19:  # 1(addr) + 1(func) + 1(bytes) + 16(data) + 2(crc) = 21 bytes
            voltage_raw = (response[3] << 8) | response[4]
            current_raw = (response[5] << 8) | response[6]
            power_low = (response[7] << 8) | response[8]
            power_high = (response[9] << 8) | response[10]
            energy_low = (response[11] << 8) | response[12]
            energy_high = (response[13] << 8) | response[14]
            high_voltage_alarm = (response[15] << 8) | response[16]
            low_voltage_alarm = (response[17] << 8) | response[18]
            
            return {
                'voltage': voltage_raw * 0.01,  # V
                'current': current_raw * 0.01,  # A
                'power': ((power_high << 16) | power_low) * 0.1,  # W
                'energy': (energy_high << 16) | energy_low,  # Wh
                'high_voltage_alarm': high_voltage_alarm == 0xFFFF,
                'low_voltage_alarm': low_voltage_alarm == 0xFFFF
            }
        return None
    
    def reset_energy(self):
        """
        Reset nilai energi pada sensor
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        packet = bytearray([self.slave_addr, self.FC_RESET_ENERGY])
        crc = self._calculate_crc(packet)
        packet.append(crc & 0xFF)
        packet.append((crc >> 8) & 0xFF)
        
        # Set mode transmit
        self.de_pin.value(1)
        self.re_pin.value(1)
        time.sleep_ms(1)
        
        # Kirim data
        self.uart.write(packet)
        
        # Delay
        tx_time_ms = (len(packet) * 10) / (9600 / 1000) + 5
        time.sleep_ms(int(tx_time_ms))
        
        # Set mode receive
        self.de_pin.value(0)
        self.re_pin.value(0)
        
        # Tunggu respons
        timeout = 500
        start_time = time.ticks_ms()
        
        while self.uart.any() < 4:  # Respons: slave_addr(1) + func_code(1) + crc(2)
            if time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                print("Timeout saat menunggu respons reset energi")
                return False
            time.sleep_ms(10)
        
        # Baca respons
        response = self.uart.read()
        
        # Cek respons valid
        if not response or len(response) < 4:
            print("Respons reset energi tidak valid")
            return False
        
        # Cek error
        if (response[1] & 0x80) == 0x80:
            print("Error saat reset energi")
            return False
        
        # Cek respons sesuai
        if response[0] != self.slave_addr or response[1] != self.FC_RESET_ENERGY:
            print("Respons reset energi tidak sesuai")
            return False
        
        print("Reset energi berhasil")
        return True
    
    def send_data_once(self, parameter="all"):
        """
        Kirim data sensor ke MQTT sekali saja (tidak dalam loop)
        
        Args:
            parameter: Parameter yang akan dikirim ("voltage", "current", "power", "energy", "all")
            
        Returns:
            data: Data yang dikirim
        """
        # Siapkan data berdasarkan parameter
        if parameter == "voltage":
            topic = "Tegangan"
            data = self.read_voltage()
        elif parameter == "current":
            topic = "Arus"
            data = self.read_current()
        elif parameter == "power":
            topic = "Power"
            data = self.read_power()
        elif parameter == "energy":
            topic = "Energy"
            data = self.read_energy()
        else:
            topic = "all"
            data = self.read_all_parameters()
        
        # Kirim data ke MQTT (sekali saja, bukan dalam loop)
        try:
            pin.value(1)  # LED indikator ON
            self.mqqt.publish(topic, data, self.client, self.id_sensor)
            pin.value(0)  # LED indikator OFF
            return data
        except Exception as e:
            print("MQTT error:", e)
            pin.value(0)  # LED indikator OFF
            return None
    
    def start_monitoring(self, parameter="all"):
        """
        PERHATIAN: Fungsi ini berisi loop tak terbatas!
        
        Args:
            parameter: Parameter yang akan dipantau ("voltage", "current", "power", "energy", "all")
        """
        last_message = 0
        
        # Siapkan topic berdasarkan parameter
        if parameter == "voltage":
            topic = "Tegangan"
            get_data = self.read_voltage
        elif parameter == "current":
            topic = "Arus"
            get_data = self.read_current
        elif parameter == "power":
            topic = "Power"
            get_data = self.read_power
        elif parameter == "energy":
            topic = "Energy"
            get_data = self.read_energy
        else:
            topic = "all"
            get_data = self.read_all_parameters
            
        print("Starting PZEM sensor monitoring...")
        
        while True:
            pin.value(1)  # LED indikator ON
            
            try:
                if (time.time() - last_message) > MESSAGE_INTERVAL:
                    data = get_data()
                    if data is not None:
                        self.mqqt.publish(topic, data, self.client, self.id_sensor)
                        # Cetak data untuk debug
                        if parameter != "all":
                            print(f"{topic}: {data}")
                        else:
                            print("Semua parameter:", data)
                    else:
                        print("Gagal membaca data sensor")
                        
                    last_message = time.time()
            except OSError as e:
                print("MQTT connection failed:", e)
                self.mqqt.restart_and_reconnect()
                self.client = mqtt_client  # Update client reference after reconnect
            
            pin.value(0)  # LED indikator OFF
            time.sleep(1)