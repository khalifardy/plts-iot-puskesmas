from app.db.models.sensor_data import (
    TemperatureSensorReadings,
    PZEM004TReading
)

from app.db.models.device import Alert
from app.db.database import get_connection
from typing import List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

#defenisi ambang batas default
DEFAULT_THRESHOLDS = {
    "temperature": {
        "min": 0,
        "max": 50
    },
    "voltage": {
        "min": 180,
        "max": 260
    },
    "current": {
        "min": 0,
        "max": 20
    },
    "power": {
        "min": 0,
        "max": 5000
    }
}

async def check_alerts_temperature(reading: TemperatureSensorReadings)-> List[Alert]:
    """Cek apakah ada alert untuk pembacaan suhu"""
    
    alerts = []
    
    #ambil konfigurasi threshold untuk device ini
    thresholds = await get_device_thresholds(reading.device_id)
    
    # cek suhu tinggi
    if reading.temperature > thresholds.get("temperature").get("max", DEFAULT_THRESHOLDS["temperature"]['max']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="high_temperature",
            message=f"Temperature too high: {reading.temperature}°C",
            threshold=thresholds.get("temperature").get("max", DEFAULT_THRESHOLDS["temperature"]['max']),
            actual_value=reading.temperature,
        ))
    
    #cek suhu rendah
    if reading.temperature < thresholds.get("temperature").get("min", DEFAULT_THRESHOLDS["temperature"]['min']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="low_temperature",
            message=f"Temperature too low: {reading.temperature}°C",
            threshold=thresholds.get("temperature").get("min", DEFAULT_THRESHOLDS["temperature"]['min']),
            actual_value=reading.temperature,
        ))
    
    if alerts:
        await save_alerts(alerts)
    
    return alerts

async def check_alerts_pzem004t(reading: PZEM004TReading)-> List[Alert]:
    """Cek apakah ada alert untuk pembacaan PZEM004T"""
    
    alerts = []
    
    #ambil konfigurasi threshold untuk device ini
    thresholds = await get_device_thresholds(reading.device_id)
    
    # cek tegangan tinggi
    if reading.voltage > thresholds.get("voltage").get("max", DEFAULT_THRESHOLDS["voltage"]['max']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="high_voltage",
            message=f"Voltage too high: {reading.voltage}V",
            threshold=thresholds.get("voltage").get("max", DEFAULT_THRESHOLDS["voltage"]['max']),
            actual_value=reading.voltage,
        ))
    
    #cek tegangan rendah
    if reading.voltage < thresholds.get("voltage").get("min", DEFAULT_THRESHOLDS["voltage"]['min']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="low_voltage",
            message=f"Voltage too low: {reading.voltage}V",
            threshold=thresholds.get("voltage").get("min", DEFAULT_THRESHOLDS["voltage"]['min']),
            actual_value=reading.voltage,
        ))
    
    #cek arus tinggi
    if reading.current > thresholds.get("current").get("max", DEFAULT_THRESHOLDS["current"]['max']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="high_current",
            message=f"Current too high: {reading.current}A",
            threshold=thresholds.get("current").get("max", DEFAULT_THRESHOLDS["current"]['max']),
            actual_value=reading.current,
        ))
    
    #cek arus rendah
    if reading.current < thresholds.get("current").get("min", DEFAULT_THRESHOLDS["current"]['min']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="low_current",
            message=f"Current too low: {reading.current}A",
            threshold=thresholds.get("current").get("min", DEFAULT_THRESHOLDS["current"]['min']),
            actual_value=reading.current,
        ))
    
    #cek daya tinggi
    if reading.power > thresholds.get("power").get("max", DEFAULT_THRESHOLDS["power"]['max']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="high_power",
            message=f"Power too high: {reading.power}W",
            threshold=thresholds.get("power").get("max", DEFAULT_THRESHOLDS["power"]['max']),
            actual_value=reading.power,
        ))
    
    #cek daya rendah
    if reading.power < thresholds.get("power").get("min", DEFAULT_THRESHOLDS["power"]['min']):
        alerts.append(Alert(
            device_id = reading.device_id,
            alert_type="low_power",
            message=f"Power too low: {reading.power}W",
            threshold=thresholds.get("power").get("min", DEFAULT_THRESHOLDS["power"]['min']),
            actual_value=reading.power,
        ))
    if alerts:
        await save_alerts(alerts)
    return alerts

async def get_device_thresholds(device_id:str)-> dict:
    """Ambil konfigurasi threshold untuk device ini"""
    
    async with get_connection() as conn :
        # Cek apakah ada custom threshold
        rows = await conn.fetch(
            '''
            SELECT config_key, config_value::float
            FROM dbo.device_configs
            WHERE device_id = $1 AND config_key LIKE '%\_threshold'
            ''', device_id
        )
        
        #default ke threshold default
        thresholds = DEFAULT_THRESHOLDS.copy()
        
        # Update dengan custom threshold
        for row in rows:
            key = row['config_key'].replace('_threshold','')
            thresholds[key] = row['config_value']
            
        return thresholds

async def save_alerts(alerts: List[Alert]):
    """Simpan alert ke database"""
    
    async with get_connection() as conn :
        '''Simpan alert ke database'''
        async with get_connection() as conn:
            for alert in alerts:
                await conn.execute(
                    '''
                    INSERT INTO dbo.alerts (device_id, alert_type, message, threshold, actual_value, created_at, acknowledged)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    ''',
                    alert.device_id,
                    alert.alert_type,
                    alert.message,
                    alert.threshold,
                    alert.actual_value,
                    alert.created_at or datetime.now(),
                    alert.acknowledged
                )


    