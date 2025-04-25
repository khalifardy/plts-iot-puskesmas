import asyncio
import asyncpg
import os
from dotenv import load_dotenv
import logging

# setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)

load_dotenv()

async def init_database():
    # connect to default postgresql database
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "postgres"),
        password=os.getenv("POSTGRES_PASSWORD", 'password_baru'),
        host=os.getenv("POSTGRES_HOST", 'localhost'),
        port=os.getenv("POSTGRES_PORT", 5432),
        database="postgres",
    )
    
    # buat database jika belum ada
    db_name = os.getenv("POSTGRES_DB", "plts")
    
    try:
        await conn.execute(f"CREATE DATABASE {db_name}")
        logger.info(f"Database {db_name} created successfully.")
    except asyncpg.exceptions.DuplicateDatabaseError:
        logger.info(f"Database {db_name} already exists.")
    finally:
        await conn.close()
    
    # connect to the new database
    conn = await asyncpg.connect(
        user=os.getenv("POSTGRES_USER", "plts_puskesmas_tanah_toraja"),
        password=os.getenv("POSTGRES_PASSWORD", "qwerty12345"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", 5432),
        database=db_name,
    )
    
    # Tambahkan ini setelah koneksi dan sebelum membuat tabel
    try:
        await conn.execute("CREATE SCHEMA IF NOT EXISTS dbo;")
        logger.info("Schema dbo created or already exists.")
    except Exception as e:
        logger.error(f"Error creating schema dbo: {e}")
    
    try:
        # enable timescaledb extension
        try:
            await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;")
            logger.info("TimescaleDB extension enabled.")
        except Exception as e:
            logger.error(f"Error enabling TimescaleDB extension: {e}")
            logger.warning("TimescaleDB extension may not be enabled.")
    
        # create tables
        # 1.Sensor Temperature reading (TimmescaleDB hypertable)
        await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dbo.temperature_sensor_readings (
            time TIMESTAMPTZ NOT NULL,
            device_id TEXT NOT NULL,
            temperature DOUBLE PRECISION,
            PRIMARY KEY (device_id, time)
        );
        '''
        )
        
        # convert to hypertable if TimescaleDB is enabled
        try:
            await conn.execute(
                "SELECT dbo.create_hypertable('dbo.temperature_sensor_readings', 'time', if_not_exists:=TRUE);"
            )
            logger.info("Hypertable created for temperature sensor readings.")
        except Exception as e:
            logger.error(f"Error creating hypertable for temperature sensor readings: {e}")
            logger.warning("Hypertable may not be created.")
        
        # 2.Sensor PZEM004T reading tabel (TimmescaleDB hypertable)
        await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dbo.pzem004t_sensor_readings (
            time TIMESTAMPTZ NOT NULL,
            device_id TEXT NOT NULL,
            voltage DOUBLE PRECISION,
            current DOUBLE PRECISION,
            power DOUBLE PRECISION,
            energy DOUBLE PRECISION,
            PRIMARY KEY (device_id, time)
        );
        '''
        )
        
        # convert to hypertable if TimescaleDB is enabled
        try:
            await conn.execute(
                "SELECT dbo.create_hypertable('dbo.pzem004t_sensor_readings', 'time', if_not_exists:=TRUE);"
            )
            logger.info("Hypertable created for PZEM004T sensor readings.")
        except Exception as e:
            logger.error(f"Error creating hypertable for PZEM004T sensor readings: {e}")
            logger.warning("Hypertable may not be created.")
        
        # 3. Device table
        await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dbo.devices (
            device_id TEXT PRIMARY KEY,
            name TEXT,
            location TEXT,
            type TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            last_active TIMESTAMPTZ
        );
        '''
        )
        
        # 4. device config table
        await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dbo.device_configs (
            device_id TEXT REFERENCES dbo.devices(device_id),
            config_key TEXT,
            config_value TEXT,
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            PRIMARY KEY (device_id, config_key)
        );
        '''
        )
        
        # 5. Alerts table
        await conn.execute(
        '''
        CREATE TABLE IF NOT EXISTS dbo.alerts (
            alert_id SERIAL PRIMARY KEY,
            device_id TEXT REFERENCES dbo.devices(device_id),
            alert_type TEXT,
            message TEXT,
            threshold FLOAT,
            actual_value FLOAT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            acknowledged BOOLEAN DEFAULT FALSE
        );
        '''
        )
        
        # Create indexes
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_temperatur_readings_time ON dbo.temperature_sensor_readings (time DESC);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_sensor_pzem004t_readings_time ON dbo.pzem004t_sensor_readings (time DESC);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_device ON dbo.alerts (device_id);')
        await conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_created ON dbo.alerts (created_at DESC);')
        
        logger.info("Tables and indexes created successfully.")
        
        # Insert sample device data dengan menambahkan sensor-pzem004t-001
        await conn.execute(
            '''
            INSERT INTO dbo.devices (device_id, name, location, type)
            VALUES
                ('sensor-temp-001', 'Temperature Sensor 1', 'PV', 'temperature'),
                ('sensor-pzem004t-001', 'PZEM004T Sensor 0', 'PV', 'all electricity'),
                ('sensor-pzem004t-002', 'PZEM004T Sensor 1', 'PV', 'all electricity'),
                ('sensor-pzem004t-003', 'PZEM004T Sensor 2', 'Battery', 'all electricity')
            ON CONFLICT (device_id) DO NOTHING;
            '''
        )
        
        # insert sample device configuration/threshold dengan memperbaiki nilai
        await conn.execute(
            '''
            INSERT INTO dbo.device_configs (device_id, config_key, config_value)
            VALUES 
                ('sensor-temp-001', 'high_temperature_threshold', '30.0'),
                ('sensor-temp-001', 'low_temperature_threshold', '18.0'),
                ('sensor-pzem004t-001', 'high_voltage_threshold', '4.8'),
                ('sensor-pzem004t-001', 'low_voltage_threshold', '4.0'),
                ('sensor-pzem004t-001', 'high_current_threshold', '10.0'),
                ('sensor-pzem004t-001', 'low_current_threshold', '1.0'),
                ('sensor-pzem004t-001', 'high_power_threshold', '2000.0'),
                ('sensor-pzem004t-001', 'low_power_threshold', '100.0'),
                ('sensor-pzem004t-001', 'high_energy_threshold', '10000.0'),
                ('sensor-pzem004t-001', 'low_energy_threshold', '1000.0'),
                ('sensor-pzem004t-002', 'high_voltage_threshold', '4.8'),
                ('sensor-pzem004t-002', 'low_voltage_threshold', '4.0'),
                ('sensor-pzem004t-002', 'high_current_threshold', '10.0'),
                ('sensor-pzem004t-002', 'low_current_threshold', '1.0'),
                ('sensor-pzem004t-002', 'high_power_threshold', '2000.0'),
                ('sensor-pzem004t-002', 'low_power_threshold', '100.0'),
                ('sensor-pzem004t-002', 'high_energy_threshold', '10000.0'),
                ('sensor-pzem004t-002', 'low_energy_threshold', '1000.0')
            ON CONFLICT (device_id, config_key) DO NOTHING;
            '''
        )
        logger.info("Sample device data inserted successfully.")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise
    finally:
        await conn.close()
    
if __name__ == "__main__":
    asyncio.run(init_database())