#config.py - Pengaturan konfigurasi untuk PLTS Monitoring System

#Informsi Sistem
DEVICE_NAME = "PLTS_Puskesmas_Tana_Toraja"
DEVICE_ID = "plts001"
VERSION = "1.0.0"

#konfigurasi jaringan
WIFI_SSID = "Ali" # nama wifi
WIFI_PASSWORD = "20180427" # password wifi
WIFI_TIMEOUT = 20 #waktu untuk timeout koneksi Wifi

WIFI_SSID_PUSKESMAS = "tselhome-2253" #"PUSKESMAS_MAKALE_UTARA"
WIFI_PASSWORD_PUSKESMAS = "HE98EHMHRL5"


#Konfigurasi Access Point jika Wifi gagal
AP_SSID = "PLTS_Puskesmas"
AP_PASSWORD = "puskesmas123"
AP_CHANNEL = 1
AP_IP = "192.168.4.1"

# Konfigurasi MQTT
MQQT_BROKER_HIVE = "broker.hivemq.com"
MQTT_BROKER = "192.168.18.39"#"broker.hivemq.com"  # Broker MQTT (ganti dengan broker Anda)
MQTT_PORT = 1883
MQTT_USER = ""                    # Kosongkan jika tidak menggunakan autentikasi
MQTT_PASSWORD = ""                # Kosongkan jika tidak menggunakan autentikasi
MQTT_CLIENT_ID = DEVICE_ID        # ID Klien MQTT
MQTT_TOPIC_BASE = "puskesmas/plts/"  # Topik dasar untuk publikasi data
MQTT_QOS = 0                      # Quality of Service (0, 1, atau 2)
MQTT_KEEPALIVE = 60               # Keepalive dalam detik

# Konfigurasi Web Server
WEB_SERVER_PORT = 80

# Konfigurasi Pin
LED_PIN = 2                       # Built-in LED
RELAY_PIN = 16                    # Pin untuk relay kontrol

# Konfigurasi Sensor
VOLTAGE_PIN = 34                  # Pin ADC untuk sensor tegangan
CURRENT_PIN = 35                  # Pin ADC untuk sensor arus
TEMP_PIN = 32                     # Pin ADC untuk sensor suhu

# Faktor Kalibrasi Sensor (sesuaikan dengan sensor Anda)
VOLTAGE_FACTOR = 5.0              # Contoh untuk pembagi tegangan
CURRENT_FACTOR = 0.1              # Contoh untuk sensor arus
TEMP_FACTOR = 100.0               # Contoh untuk sensor suhu (LM35)

# Batas Peringatan
VOLTAGE_HIGH = 14.5               # Batas tegangan tinggi (V)
VOLTAGE_LOW = 10.5                # Batas tegangan rendah (V)
TEMP_HIGH = 70.0                  # Batas suhu tinggi (°C)
CURRENT_HIGH = 10.0               # Batas arus tinggi (A)

# Interval Pengambilan Data dan Publikasi (dalam detik)
READING_INTERVAL = 10             # Interval pembacaan sensor
PUBLISH_INTERVAL = 60             # Interval publikasi ke MQTT
ALERT_CHECK_INTERVAL = 5          # Interval cek peringatan

# File untuk Penyimpanan Lokal
LOG_FILE = "plts_log.csv"         # Log data CSV
CONFIG_SAVE_FILE = "plts_config.json"  # File penyimpanan konfigurasi

# Mode Debug
DEBUG = True       
