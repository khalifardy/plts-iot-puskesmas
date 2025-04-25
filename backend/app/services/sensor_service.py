from app.db.models.sensor_data import (
    TemperatureSensorReadings,
    PZEM004TReading,
    TemperatureStats,
    PZEM004TStats,
)
from app.db.database import get_connection
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

async def save_sensor_temperature_reading(reading: TemperatureSensorReadings):
    """Simpan data sensor temperatur ke TimescaleDB"""
    async with get_connection() as conn:
        try:
            await conn.execute(
                '''
                INSERT INTO dbo.temperature_sensor_readings (time, device_id, temperature)
                VALUES($1, $2, $3)
                ''', reading.time, reading.device_id, reading.temperature
            )
            
            # Update last_active di tabel devices
            # Tambahkan try/except terpisah agar INSERT tetap berhasil meskipun UPDATE gagal
            try:
                await conn.execute(
                    '''
                    UPDATE dbo.devices
                    SET last_active = $1
                    WHERE device_id = $2
                    ''',
                    reading.time,
                    reading.device_id
                )
            except Exception as e:
                logger.warning(f"Gagal mengupdate last_active untuk device {reading.device_id}: {e}")
            
            return True
        except Exception as e:
            logger.error(f"Error saving sensor reading: {e}")
            raise
        
async def save_sensor_pzem004t_reading(reading: PZEM004TReading):
    """Simpan data sensor PZEM004T ke TimescaleDB"""
    async with get_connection() as conn:
        try:
            await conn.execute(
                '''
                INSERT INTO dbo.pzem004t_sensor_readings (time, device_id, voltage, current, power, energy)
                VALUES($1, $2, $3, $4, $5, $6)
                ''', reading.time, reading.device_id,
                reading.voltage,
                reading.current,
                reading.power,
                reading.energy
            )
            
            # Update last_active di tabel devices
            # Tambahkan try/except terpisah agar INSERT tetap berhasil meskipun UPDATE gagal
            try:
                await conn.execute(
                    '''
                    UPDATE dbo.devices
                    SET last_active = $1
                    WHERE device_id = $2
                    ''',
                    reading.time,
                    reading.device_id
                )
            except Exception as e:
                logger.warning(f"Gagal mengupdate last_active untuk device {reading.device_id}: {e}")
                
            return True
        except Exception as e:
            logger.error(f"Error saving PZEM004T reading: {e}")
            raise

async def get_temperature_sensor_readings(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[TemperatureSensorReadings]:
    """Ambil data sensor temperatur dari database dengan filter"""
    async with get_connection() as conn:
        # Bangun query dengan filter
        query = "SELECT time, device_id, temperature FROM dbo.temperature_sensor_readings"
        params = []
        conditions = []
        print(device_id)
        
        if device_id:
            conditions.append("device_id = $" + str(len(params) + 1))
            params.append(device_id)
            print(params)
        
        if start_time:
            conditions.append("time >= $" + str(len(params) + 1))
            params.append(start_time)
        
        if end_time:
            conditions.append("time <= $" + str(len(params) + 1))
            params.append(end_time)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY time DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        # Execute query
        rows = await conn.fetch(query, *params)
        
        # Convert to SensorReading objects - PERBAIKAN: Urutan field yang benar
        readings = []
        for row in rows:
            readings.append(
                TemperatureSensorReadings(
                    time=row['time'],
                    device_id=row['device_id'],
                    temperature=row['temperature']
                )
            )
        #print(readings)
        return readings

async def get_pzem004t_sensor_readings(
    device_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 100
) -> List[PZEM004TReading]:
    """Ambil data sensor PZEM004T dari database dengan filter"""
    async with get_connection() as conn:
        # Bangun query dengan filter
        query = "SELECT time, device_id, voltage, current, power, energy FROM dbo.pzem004t_sensor_readings"
        params = []
        conditions = []
        
        if device_id:
            conditions.append("device_id = $" + str(len(params) + 1))
            params.append(device_id)
        
        if start_time:
            conditions.append("time >= $" + str(len(params) + 1))
            params.append(start_time)
        
        if end_time:
            conditions.append("time <= $" + str(len(params) + 1))
            params.append(end_time)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
        
        query += " ORDER BY time DESC LIMIT $" + str(len(params) + 1)
        params.append(limit)
        
        # Execute query
        rows = await conn.fetch(query, *params)
        
        # Convert to PZEM004TReading objects
        readings = []
        for row in rows:
            readings.append(
                PZEM004TReading(
                    time=row['time'],
                    device_id=row['device_id'],
                    voltage=row['voltage'],
                    current=row['current'],
                    power=row['power'],
                    energy=row['energy']
                )
            )
        
        return readings

async def get_temperature_sensor_stats(
    device_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> TemperatureStats:
    """Hitung statistik data sensor temperatur"""
    
    if not start_time:
        start_time = datetime.now() - timedelta(days=1)  # default satu hari terakhir
    
    if not end_time:
        end_time = datetime.now()
    
    async with get_connection() as conn:
        # query untuk statistik
        # PERBAIKAN: Nama tabel yang benar (temperature_sensor_readings bukan temperature_sensor_reading)
        stats = await conn.fetchrow(
            '''
            SELECT 
                device_id,
                AVG(temperature) as avg_temperature,
                MIN(temperature) as min_temperature,
                MAX(temperature) as max_temperature,
                COUNT(*) as reading_count,
                MAX(time) as last_reading_time
            FROM dbo.temperature_sensor_readings
            WHERE device_id = $1 AND time BETWEEN $2 AND $3
            GROUP BY device_id
            ''', device_id, start_time, end_time
        )
        
        if stats:
            # PERBAIKAN: Typo last_reading_time (hilangkan tanda [])
            return TemperatureStats(
                device_id=stats['device_id'],
                avg_temperature=stats['avg_temperature'],
                min_temperature=stats['min_temperature'],
                max_temperature=stats['max_temperature'],
                reading_count=stats['reading_count'],
                last_reading_time=stats['last_reading_time']
            )
        else:
            # PERBAIKAN: Typo avf_temperature dan perbaikan struktur
            return TemperatureStats(
                device_id=device_id,
                avg_temperature=0,
                min_temperature=0,
                max_temperature=0,
                reading_count=0,
                last_reading_time=start_time
            )

async def get_pzem004t_sensor_stats(
    device_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> PZEM004TStats:
    """Hitung statistik data sensor PZEM004T"""
    
    if not start_time:
        start_time = datetime.now() - timedelta(days=1)  # default satu hari terakhir
    
    if not end_time:
        end_time = datetime.now()
    
    async with get_connection() as conn:
        # query untuk statistik
        
        stats = await conn.fetchrow(
            '''
            SELECT 
                device_id,
                AVG(voltage) as avg_voltage,
                AVG(current) as avg_current,
                AVG(power) as avg_power,
                SUM(energy) as total_energy,
                COUNT(*) as reading_count,
                MAX(time) as last_reading_time
            FROM dbo.pzem004t_sensor_readings
            WHERE device_id = $1 AND time BETWEEN $2 AND $3
            GROUP BY device_id
            ''', device_id, start_time, end_time
        )
        
        if stats:
            return PZEM004TStats(
                device_id=stats['device_id'],
                avg_voltage=stats['avg_voltage'],
                avg_current=stats['avg_current'],
                avg_power=stats['avg_power'],
                total_energy=stats['total_energy'],
                reading_count=stats['reading_count'],
                last_reading_time=stats['last_reading_time']
            )
        else:
            return PZEM004TStats(
                device_id=device_id,
                avg_voltage=0,
                avg_current=0,
                avg_power=0,
                total_energy=0,
                reading_count=0,
                last_reading_time=start_time
            )
            
async def get_aggregated_data_temperature(
    device_id: str,
    interval: str = "1 hours",  # Interval untuk agregasi: ' 1 MINUTE, 1 HOUR, 1 DAY'
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[dict]:
    """
    Ambil data agregasi temperatur untuk grafik
    menggunakan fitur time_bucket TimescaleDB untuk agregasi efisien
    """
    
    if not start_time:
        start_time = datetime.now() - timedelta(days=7) 
    
    if not end_time:
        end_time = datetime.now()
    
    async with get_connection() as conn:
        # Gunakan raw SQL dengan literal string untuk interval
        rows = await conn.fetch(
            f'''
            SELECT
                dbo.time_bucket('{interval}'::interval, time::timestamptz) AS bucket,
                device_id,
                AVG(temperature) AS avg_temperature,
                COUNT(*) as reading_count
            FROM dbo.temperature_sensor_readings
            WHERE device_id = $1 AND time BETWEEN $2 AND $3
            GROUP BY bucket, device_id
            ORDER BY bucket ASC
            ''', device_id, start_time, end_time  # Parameter sudah berkurang menjadi 3
        )
        
        return [dict(row) for row in rows]

async def get_aggregated_data_pzem004t(
    device_id: str,
    interval: str = "1 hours",  # Interval untuk agregasi: ' 1 MINUTE, 1 HOUR, 1 DAY'
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> List[dict]:
    """
    Ambil data agregasi PZEM004T untuk grafik
    menggunakan fitur time_bucket TimescaleDB untuk agregasi efisien
    """
    
    if not start_time:
        start_time = datetime.now() - timedelta(days=7) 
    
    if not end_time:
        end_time = datetime.now()
    
    async with get_connection() as conn:
        rows = await conn.fetch(
            f'''
            SELECT
                dbo.time_bucket('{interval}'::interval, time::timestamptz) AS bucket,
                device_id,
                AVG(voltage) AS avg_voltage,
                AVG(current) AS avg_current,
                AVG(power) AS avg_power,
                SUM(energy) AS total_energy,
                COUNT(*) as reading_count
            FROM dbo.pzem004t_sensor_readings
            WHERE device_id = $1 AND time BETWEEN $2 AND $3
            GROUP BY bucket, device_id
            ORDER BY bucket ASC
            ''', device_id, start_time, end_time
        )
        
        return [dict(row) for row in rows]