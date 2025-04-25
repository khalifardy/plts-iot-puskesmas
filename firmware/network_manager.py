import network
import socket
import machine 
import json
import os 
import gc
import time
from config import *
from lib.umqtt.simple_mqqt import MQTTClient

#status LED
led = machine.Pin(18, machine.Pin.OUT)

#wifi manager
class NetworkManager:
    def __init__(self, config_file=CONFIG_SAVE_FILE):
        self.config_file = config_file
        self.sta_if = network.WLAN(network.STA_IF)
        self.ap_if = network.WLAN(network.AP_IF)
        self.config = self._load_config()
        self.web_server_socket = None
        
    def _load_config(self):
        """Memuat Konfigurasi WIFI dari file"""
        
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except (OSError, ValueError):
            #File tidak ada atau rusak, gunakan default
            return {
                "ssid": WIFI_SSID,
                "password": WIFI_PASSWORD
            }
    
    def _save_config(self, ssid, password):
        """Menyimpan Konfigurasi WIFI ke file"""
        
        try:
            with open(self.config_file, 'w') as f:
                json.dump(
                    {
                        "ssid":ssid,
                        "password": password
                        
                    },
                    f
                )
                return True
        
        except OSError:
            return False
    
    def blink_led(self, times=3, delay=0.2):
        """Kedipkan LED untuk indikasi visual"""
        for _ in range(times):
            led.value(1)
            time.sleep(delay)
            led.value(0)
            time.sleep(delay)
    
    def connect_wifi(self, timeout=WIFI_TIMEOUT):
        """Mencoba terhubung ke WiFi dengan kredensial tersimpan"""
    
        if not self.config['ssid']:
            print("SSID tidak tersedia")
            led.value(0)  # Pastikan LED mati jika tidak ada SSID
            return False
    
        print(f"Menghubungkan ke WiFi: {self.config['ssid']}")
        self.sta_if.active(True)
    
        if not self.sta_if.isconnected():
            self.sta_if.connect(self.config['ssid'], self.config['password'])
        
            # Tunggu koneksi
            attempts = 0
            while not self.sta_if.isconnected() and attempts < timeout:
                led.value(attempts % 2)  # Kedipkan LED
                time.sleep(1)
                attempts += 1
                print(".", end="")
        
            print(" ")
        
        if self.sta_if.isconnected():
            network_info = self.sta_if.ifconfig()
            print("Connected to WiFi")
            print("IP Address:", network_info[0])
            print("Subnet Mask:", network_info[1])
            print("Gateway:", network_info[2])
            print("DNS Server:", network_info[3])
            self.blink_led(3, 0.1)
            led.value(1)  # LED menyala saat terhubung
            return True
        else:
            print("Gagal terhubung")
            led.value(0)  # LED mati saat gagal terhubung
            return False
        
    def start_ap(self):
        """Mengaktifkan Access Point"""
        
        self.ap_if.active(True)
        self.ap_if.config(essid=AP_SSID, password=AP_PASSWORD, channel=AP_CHANNEL)
        
        #konfigurasi IP statis
        self.ap_if.ifconfig((AP_IP, '255.255.255.0', AP_IP, '8.8.8.8'))
        
        print(f"Access Point started: {AP_SSID}")
        print("IP Adress: {AP_IP}")
        
        #indikasi mode AP dengan LED
        for _ in range(5):
            led.value(1)
            time.sleep(0.1)
            led.value(0)
            time.sleep(0.1)
        
        return True
    
    def stop_ap(self):
        """Menonaktifkan Access Point"""
        
        self.ap_if.active(False)
        print("Access Point dimatikan")
    
    def start_web_server(self):
        """Memulai Web Server"""
        
        if not self.ap_if.active():
            print("Access Point tidak aktif")
            self.start_ap()
        
        #buat socket server
        self.web_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.web_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            self.web_server_socket.bind(('0.0.0.0', WEB_SERVER_PORT))
            self.web_server_socket.listen(1)
            print(f"Web Server aktif di port {WEB_SERVER_PORT}")
            print(f"akses http://{AP_IP} untuk konfigurasi WIFI")
            
            #indikasi web server aktif
            led.value(1)
            
            return True

        except OSError as e:
            print("Gagal memulai web server: {e}")
            return False
    
    def handle_web_client(self, max_clients=10):
        """menangani klient web untuk konfigurasi WIFI"""
        
        if not self.web_server_socket:
            print("web server tidak aktif")
            return 
        
        clients_handled = 0
        new_config = False
        
        while clients_handled < max_clients:
            try:
                #tunggu koneksi klien dengan timeout
                self.web_server_socket.settimeout(1)
                try:
                    conn,addr  = self.web_server_socket.accept()
                except OSError:
                    #timeout cek apakah harus terus menunggu
                    continue
                print(f"Klien terhubung dari {addr}")
                
                #terima request
                request = conn.recv(1024).decode('utf-8')
                
                #parse request
                if request.find('POST /save') != -1:
                    #ekstrak data dari POST request
                    content_length_pos = request.find('Content-Length: ')
                    if content_length_pos != -1 :
                        content_length_end = request.find('\r\n', content_length_pos)
                        content_length = int(request[content_length_pos+16:content_length_end])
                        # Cari body data
                        body_pos = request.find('\r\n\r\n')
                        if body_pos != -1:
                            body = request[body_pos + 4:body_pos + 4 + content_length]
                            
                            # Parse form data (contoh: ssid=nama&password=katasandi)
                            params = {}
                            for param in body.split('&'):
                                key, value = param.split('=')
                                params[key] = value.replace('+', ' ')
                            
                            # Simpan konfigurasi baru
                            if 'ssid' in params and 'password' in params:
                                self._save_config(params['ssid'], params['password'])
                                new_config = True
                                
                                # Kirim halaman berhasil
                                response = """
                                HTTP/1.1 200 OK
                                Content-Type: text/html

                                <html>
                                <head>
                                    <title>PLTS Puskesmas - WiFi Setup</title>
                                    <meta name="viewport" content="width=device-width, initial-scale=1">
                                    <style>
                                        body {font-family: Arial; margin: 0; padding: 20px; text-align: center;}
                                        .container {max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;}
                                        h1 {color: #4CAF50;}
                                        .message {margin: 20px 0; padding: 10px; background-color: #f1f1f1;}
                                        .button {background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px;}
                                    </style>
                                </head>
                                <body>
                                    <div class="container">
                                        <h1>Konfigurasi WiFi</h1>
                                        <div class="message">
                                            <p>Konfigurasi WiFi berhasil disimpan!</p>
                                            <p>SSID: """ + params['ssid'] + """</p>
                                        </div>
                                        <p>Perangkat akan mencoba terhubung ke jaringan WiFi.</p>
                                        <p>Jika koneksi berhasil, mode Access Point akan dimatikan.</p>
                                    </div>
                                </body>
                                </html>
                                """
                                conn.send(response.replace('\n', '\r\n').encode())
                                conn.close()
                                
                                # Coba koneksi dengan konfigurasi baru
                                break  # Keluar dari loop untuk mencoba koneksi baru
                    
                else:
                    # Kirim halaman konfigurasi
                    response = """
                    HTTP/1.1 200 OK
                    Content-Type: text/html

                    <html>
                    <head>
                        <title>PLTS Puskesmas - WiFi Setup</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <style>
                            body {font-family: Arial; margin: 0; padding: 20px; text-align: center;}
                            .container {max-width: 400px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px;}
                            h1 {color: #4CAF50;}
                            input[type=text], input[type=password] {width: 100%; padding: 12px 20px; margin: 8px 0; display: inline-block; border: 1px solid #ccc; box-sizing: border-box; border-radius: 4px;}
                            .button {background-color: #4CAF50; color: white; padding: 10px 20px; border: none; cursor: pointer; border-radius: 4px;}
                            .available {margin-top: 20px; text-align: left;}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>Konfigurasi WiFi</h1>
                            <p>Konfigurasikan koneksi WiFi untuk PLTS Puskesmas</p>
                            
                            <form action="/save" method="post">
                                <label for="ssid">Nama Jaringan (SSID):</label>
                                <input type="text" id="ssid" name="ssid" value="%s">
                                
                                <label for="password">Password:</label>
                                <input type="password" id="password" name="password" value="%s">
                                
                                <input type="submit" class="button" value="Simpan">
                            </form>
                            
                            <div class="available">
                                <p><strong>Jaringan yang tersedia:</strong></p>
                                <ul>
                                """ % (self.config["ssid"], self.config["password"])
                    
                    # Scan jaringan WiFi yang tersedia
                    if self.sta_if.active():
                        networks = self.sta_if.scan()
                        for ssid, bssid, channel, rssi, authmode, hidden in networks:
                            ssid_str = ssid.decode('utf-8')
                            signal_strength = (rssi + 100) * 2  # Konversi kisaran nilai RSSI
                            if signal_strength > 100:
                                signal_strength = 100
                            response += "<li>%s (Sinyal: %d%%)</li>" % (ssid_str, signal_strength)
                    else:
                        response += "<li>Aktifkan WiFi untuk scan jaringan</li>"
                    
                    response += """
                                </ul>
                            </div>
                        </div>
                    </body>
                    </html>
                    """
                    
                    conn.send(response.replace('\n', '\r\n').encode())
                    conn.close()
                
                clients_handled += 1
                
                # Kelola memori
                gc.collect()
                
            except Exception as e:
                print(f"Error menangani klien web: {e}")
        
        return new_config
    
    def stop_web_server(self):
        """menghentikan web server"""
        
        if self.web_server_socket:
            try:
                self.web_server_socket.close()
                print("Web Server dimatikan")
            except:
                pass
            self.web_server_socket = None
        led.value(0) #matikan LED
    
    def auto_connect(self):
        """Mencoba terhubung ke WiFi, jika gagal aktifkan mode AP dengan web config"""
    
        # Coba terhubung ke WiFi
        if self.connect_wifi():
            print("Koneksi WiFi berhasil")
            # Mulai monitoring status WiFi untuk mendeteksi pemutusan
            self.start_wifi_monitoring()
            return True
    
        # Jika gagal, aktifkan mode AP dan web server
        print("Mengaktifkan mode Access Point dan webserver...")
        self.start_ap()
        self.start_web_server()
    
        # Menangani klien web dan menunggu konfigurasi baru
        new_config = self.handle_web_client()
    
        if new_config:
            print("Konfigurasi baru diterima, mencoba koneksi...")
            self.stop_web_server()
            time.sleep(1)
        
            if self.connect_wifi():
                print("Koneksi WiFi berhasil dengan konfigurasi baru")
                self.stop_ap()
                # Mulai monitoring status WiFi
                self.start_wifi_monitoring()
                return True
            else:
                print("Koneksi gagal, mengembalikan mode AP")
                self.start_web_server()
    
        return False
    
    def check_wifi_status(self):
        """Memeriksa status koneksi WiFi dan perbarui LED"""
        if self.sta_if.isconnected():
            # Terhubung - LED menyala
            led.value(1)
            return True
        else:
            # Tidak terhubung - LED mati
            led.value(0)
            return False
    
    def start_wifi_monitoring(self, check_interval=10):
        """Mulai memonitor status WiFi dalam interval tertentu (detik)"""
        import _thread
    
        def monitor_thread():
            while True:
                self.check_wifi_status()
                time.sleep(check_interval)
    
        # Mulai thread untuk monitoring
        try:
            _thread.start_new_thread(monitor_thread, ())
            print(f"Monitoring WiFi dimulai (interval {check_interval} detik)")
        except:
            print("Gagal memulai thread monitoring WiFi")


#MQQT manager
class MQQTManager:
    MQQT_TEMP = MQTT_TOPIC_BASE + "temperature"
    MQQT_PZEM = MQTT_TOPIC_BASE + "pzem"
    MQQT_VOLTAGE = MQTT_TOPIC_BASE + "voltage"
    MQQT_CURRENT = MQTT_TOPIC_BASE + "current"
    MQQT_POWER = MQTT_TOPIC_BASE + "power"
    MQQT_ENERGY = MQTT_TOPIC_BASE + "energy"
    MESSAGE_INTERVAL = 5
    
    def __init__(self, client_id=MQTT_CLIENT_ID , server=MQTT_BROKER, port=MQTT_PORT, user=MQTT_USER, password=MQTT_PASSWORD):
        self.client = MQTTClient(client_id, server, port, user, password)
        
    def sub_cb(self, topic, msg):
        print((topic, msg))
        if topic == MQTT_TOPIC_BASE + 'notification'and msg.decode('utf-8') == 'received':
            print('ESP received hello message')
    
    def connect_and_subscribe(self,topic_sub=MQTT_BROKER+'notification'):
        self.client.set_callback(self.sub_cb)
        self.client.connect()
        self.client.subscribe(topic_sub)
        print(f"Connected to {MQTT_BROKER} , subscribed to {topic_sub}")
        return self.client
    
    def restart_and_reconnect(self):
        print('Failed to connect to MQTT broker. Reconnecting...')
        time.sleep(10)
        machine.reset()
    
    def publish(self, topic, msg,client,id_sensor=None):
        #try:
            #client = self.connect_and_subscribe()
        #except OSError as e:
            #print("MQTT connection failed: {e}")
            #self.restart_and_reconnect()
        
        #msg = str(msg).encode('utf-8')
        
        if topic == "Temperatur":
            topic = self.MQQT_TEMP
            payload = {
                "device_id": id_sensor,
                "temperature": msg
            }
        elif topic == "Tegangan":
            topic = self.MQQT_VOLTAGE
            payload = {
                "device_id": id_sensor,
                "voltage": msg
            }
        elif topic == "Arus":
            topic = self.MQQT_CURRENT + '/' + str(id_sensor)
            payload = {
                "device_id": id_sensor,
                "current": msg
            }
        elif topic == "Energy":
            topic = self.MQQT_ENERGY + '/' + str(id_sensor)
            payload = {
                "device_id": id_sensor,
                "energy": msg
            }
        elif topic == "Power":
            topic = self.MQQT_POWER + '/' + str(id_sensor)
            payload = {
                "device_id": id_sensor,
                "power": msg
            }
        elif topic == "all":
            topic = self.MQQT_PZEM
            payload = {
                "device_id": id_sensor,
                "voltage": msg['voltage'],
                "current": msg['current'],
                "power": msg['power'],
                "energy": msg['energy']
            }
            
            
        
        payload = json.dumps(payload).encode('utf-8')
        #print("hasil encode: ",payload)
        #last_message = 0
        #while True:
            #try:
                #if (time.time() - last_message) > self.MESSAGE_INTERVAL:
        client.publish(topic, payload)
                    #last_message = time.time()
            #except OSError as e:
                #print("Failed to publish to MQTT: {e}")
                #self.restart_and_reconnect() 
                
    
#fungsi helper untuk penggunaan langsung
def connect():
    nm = NetworkManager()
    return nm.auto_connect()
def connect_mqqt():
    mq = MQQTManager()
    return mq.connect_and_subscribe()

if __name__ =='__main__':
    network_manager = NetworkManager()
    network_manager.auto_connect()
        
        
    