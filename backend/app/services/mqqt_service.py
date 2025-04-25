import json
import asyncio
import paho.mqtt.client as mqtt
from datetime import datetime
from app.config import config
from app.db.models.sensor_data import (
    TemperatureSensorReadings,
    PZEM004TReading,
)
from app.services.sensor_service import (
    save_sensor_temperature_reading,
    save_sensor_pzem004t_reading,
)
from app.services.alert_service import (
    check_alerts_temperature,
    check_alerts_pzem004t,
)
import logging
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# Variabel untuk menyimpan event loop utama
main_loop = None
# Thread pool untuk operasi I/O
thread_pool = ThreadPoolExecutor(max_workers=10)

# WebSocket connection manager (akan digunakan untuk broadcast)
class ConnectionManager:
    def __init__(self):
        self.active_connections = []
    
    async def connect(self, websocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        return websocket
    
    def disconnect(self, websocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    
    async def broadcast(self, message):
        if not self.active_connections:
            return
            
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Gagal mengirim pesan ke WebSocket: {e}")
                disconnected.append(connection)
                
        # Hapus koneksi yang terputus
        for conn in disconnected:
            self.disconnect(conn)

# Inisialisasi connection manager
manager = ConnectionManager()

# Set Up MQTT Client
mqtt_client = mqtt.Client()

# Fungsi untuk menjalankan coroutine di event loop utama
def run_coroutine_in_main_loop(coro):
    if main_loop is None:
        logger.error("Main loop tidak diatur! Tidak dapat memproses pesan MQTT dengan benar.")
        return
    
    future = asyncio.run_coroutine_threadsafe(coro, main_loop)
    try:
        # Tunggu hasil dengan timeout untuk mencegah blocking permanen
        future.result(timeout=10)
    except Exception as e:
        logger.error(f"Error menjalankan coroutine di main loop: {e}")

# Fungsi untuk memastikan format data temperature sesuai
def ensure_temperature_format(payload, topic):
    if not isinstance(payload, dict):
        # Jika hanya nilai numerik, buat dict dengan format yang benar
        try:
            payload = {
                "device_id": topic.split('/')[-1],
                "temperature": float(payload)
            }
        except (ValueError, TypeError):
            logger.error(f"Tidak dapat mengkonversi payload ke format yang benar: {payload}")
            payload = {
                "device_id": topic.split('/')[-1],
                "temperature": 0.0
            }
    
    # Pastikan ada device_id
    if "device_id" not in payload:
        payload["device_id"] = topic.split('/')[-1]
    
    # Pastikan ada temperature
    if "temperature" not in payload:
        payload["temperature"] = 0.0
    
    # Pastikan ada time
    if "time" not in payload:
        payload["time"] = datetime.now().isoformat()
    
    return payload

# Fungsi untuk memastikan format data PZEM sesuai
def ensure_pzem_format(payload, topic):
    if not isinstance(payload, dict):
        # Jika payload bukan dict, ini tidak valid untuk PZEM
        logger.error(f"Payload PZEM bukan format JSON yang valid: {payload}")
        payload = {
            "device_id": topic.split('/')[-1],
            "voltage": 0.0,
            "current": 0.0,
            "power": 0.0,
            "energy": 0.0
        }
    
    # Pastikan semua field yang diperlukan ada
    if "device_id" not in payload:
        payload["device_id"] = topic.split('/')[-1]
    
    for field in ["voltage", "current", "power", "energy"]:
        if field not in payload:
            payload[field] = 0.0
    
    # Pastikan ada time
    if "time" not in payload:
        payload["time"] = datetime.now().isoformat()
    
    return payload

# Callback ketika pesan MQTT diterima
def on_message(client, userdata, message):
    try:
        # Decode payload
        payload_str = message.payload.decode("utf-8")
        logger.debug(f"Menerima pesan dari topik {message.topic}: {payload_str}")
        
        # Coba parse JSON
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            # Jika bukan JSON valid, coba parse sebagai nilai numerik
            try:
                payload = float(payload_str)
            except ValueError:
                logger.error(f"Tidak dapat memparse payload: {payload_str}")
                return
        
        topic = message.topic
        
        # Proses berdasarkan topik
        if topic == config.MQTT_TOPIC_TEMPERATURE:
            # Pastikan format data sesuai
            formatted_payload = ensure_temperature_format(payload, topic)
            
            try:
                # Buat objek TemperatureSensorReadings
                sensor_reading = TemperatureSensorReadings(**formatted_payload)
                
                # Jalankan proses di event loop utama
                run_coroutine_in_main_loop(
                    process_sensor_temperatur_data(sensor_reading, json.dumps(formatted_payload))
                )
            except Exception as e:
                logger.error(f"Error saat membuat objek sensor temperature: {e}")
                logger.exception(e)
        
        elif topic == config.MQTT_TOPIC_PZEM:
            # Pastikan format data sesuai
            formatted_payload = ensure_pzem_format(payload, topic)
            
            try:
                # Buat objek PZEM004TReading
                sensor_reading = PZEM004TReading(**formatted_payload)
                
                # Jalankan proses di event loop utama
                run_coroutine_in_main_loop(
                    process_sensor_pzem004_data(sensor_reading, json.dumps(formatted_payload))
                )
            except Exception as e:
                logger.error(f"Error saat membuat objek sensor PZEM: {e}")
                logger.exception(e)
        
        else:
            logger.warning(f"Topik tidak dikenal: {topic}")
    
    except Exception as e:
        logger.error(f"Gagal memproses pesan MQTT: {e}")
        logger.exception(e)

async def process_sensor_temperatur_data(sensor_reading: TemperatureSensorReadings, payload_str: str):
    try:
        # Simpan ke database
        try:
            await save_sensor_temperature_reading(sensor_reading)
            logger.debug(f"Data temperature berhasil disimpan: {sensor_reading.device_id}, temperature: {sensor_reading.temperature}")
        except Exception as e:
            logger.error(f"Gagal menyimpan data temperature ke database: {e}")
        
        # Cek alert
        alerts = []
        try:
            alerts = await check_alerts_temperature(sensor_reading)
        except Exception as e:
            logger.error(f"Gagal memeriksa alert temperature: {e}")
        
        # Broadcast data
        try:
            if alerts:
                payload_with_alerts = json.loads(payload_str)
                payload_with_alerts['alerts'] = [alert.dict() for alert in alerts]
                await manager.broadcast(json.dumps(payload_with_alerts))
            else:
                await manager.broadcast(payload_str)
        except Exception as e:
            logger.error(f"Gagal melakukan broadcast data temperature: {e}")
    
    except Exception as e:
        logger.error(f"Gagal memproses data sensor temperature: {e}")
        logger.exception(e)

async def process_sensor_pzem004_data(sensor_reading: PZEM004TReading, payload_str: str):
    try:
        # Simpan ke database
        try:
            await save_sensor_pzem004t_reading(sensor_reading)
            logger.debug(f"Data PZEM berhasil disimpan: {sensor_reading.device_id}")
        except Exception as e:
            logger.error(f"Gagal menyimpan data PZEM ke database: {e}")
        
        # Cek alert
        alerts = []
        try:
            alerts = await check_alerts_pzem004t(sensor_reading)
        except Exception as e:
            logger.error(f"Gagal memeriksa alert PZEM: {e}")
        
        # Broadcast data
        try:
            if alerts:
                payload_with_alerts = json.loads(payload_str)
                payload_with_alerts['alerts'] = [alert.dict() for alert in alerts]
                await manager.broadcast(json.dumps(payload_with_alerts))
            else:
                await manager.broadcast(payload_str)
        except Exception as e:
            logger.error(f"Gagal melakukan broadcast data PZEM: {e}")
    
    except Exception as e:
        logger.error(f"Gagal memproses data sensor PZEM: {e}")
        logger.exception(e)

# Callback ketika terhubung ke broker MQTT
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Terhubung ke broker MQTT")
        # Subscribe ke topik yang diinginkan
        client.subscribe(config.MQTT_TOPIC_TEMPERATURE)
        client.subscribe(config.MQTT_TOPIC_PZEM)
    else:
        logger.error(f"Gagal terhubung ke broker MQTT, kode pengembalian: {rc}")

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

async def setup_mqtt():
    global main_loop
    
    # Simpan referensi ke event loop utama
    main_loop = asyncio.get_running_loop()
    
    if config.MQTT_USER and config.MQTT_PASSWORD:
        mqtt_client.username_pw_set(config.MQTT_USER, config.MQTT_PASSWORD)
    
    try:
        # Jalankan fungsi sinkron dalam thread pool untuk mencegah blocking
        await main_loop.run_in_executor(
            thread_pool, 
            lambda: (
                mqtt_client.connect(config.MQTT_BROKER, config.MQTT_PORT, 60),
                mqtt_client.loop_start()
            )
        )
        logger.info("Pengaturan klien MQTT selesai dan loop dimulai")
    except Exception as e:
        logger.error(f"Gagal terhubung ke broker MQTT: {e}")
        logger.exception(e)

def stop_mqtt():
    # Hentikan MQTT client
    try:
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        logger.info("Klien MQTT terputus")
    except Exception as e:
        logger.error(f"Error saat menghentikan klien MQTT: {e}")
    
    # Hentikan thread pool
    try:
        thread_pool.shutdown(wait=False)
    except Exception as e:
        logger.error(f"Error saat menghentikan thread pool: {e}")