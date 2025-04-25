import asyncpg
from contextlib import asynccontextmanager
from app.config import config
import logging

logger = logging.getLogger(__name__)

# Pool koneksi database
pool = None

async def init_db():
    """Initialize database connection pool"""
    global pool
    try:
        logger.info("Menginisialisasi pool koneksi database...")
        pool = await asyncpg.create_pool(
            host=config.POSTGRES_SERVER,
            port=config.POSTGRES_PORT,
            user=config.POSTGRES_USER,
            password=config.POSTGRES_PASSWORD,
            database=config.POSTGRES_DB,
            min_size=3,
            max_size=10,
            command_timeout=60,
            max_inactive_connection_lifetime=300
        )
        
        # Verifikasi koneksi dengan query sederhana
        async with pool.acquire() as conn:
            version = await conn.fetchval('SELECT version();')
            logger.info(f"Terhubung ke database: {version}")
            
            # Cek apakah ekstensi TimescaleDB sudah terinstall
            is_timescale = await conn.fetchval(
                "SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'timescaledb');"
            )
            
            if is_timescale:
                logger.info("Ekstensi TimescaleDB sudah terinstall.")
            else:
                logger.warning("Ekstensi TimescaleDB belum terinstall.")
        
        logger.info("Pool koneksi database berhasil diinisialisasi")
        return pool
        
    except Exception as e:
        logger.error(f"Error ketika menghubungkan ke database: {e}")
        logger.exception(e)
        raise e

@asynccontextmanager
async def get_connection():
    """Context Manager untuk mendapatkan koneksi dari pool dengan retry logic"""
    if pool is None:
        await init_db()
        
    # Coba ambil koneksi hingga 3x jika gagal
    retries = 3
    last_error = None
    
    for attempt in range(1, retries + 1):
        try:
            async with pool.acquire() as conn:
                yield conn
                return  # Berhasil, keluar dari context manager
        except Exception as e:
            last_error = e
            if attempt < retries:
                logger.warning(f"Gagal mendapatkan koneksi database (percobaan {attempt}/{retries}): {e}. Mencoba lagi...")
            else:
                logger.error(f"Gagal mendapatkan koneksi database setelah {retries} percobaan: {e}")
    
    # Jika sampai di sini, berarti semua percobaan gagal
    raise last_error if last_error else RuntimeError("Gagal mendapatkan koneksi database")

# Fungsi alternatif get_connection untuk digunakan di luar context manager
async def get_db_connection():
    """Get a database connection from the pool"""
    if pool is None:
        await init_db()
    
    # Coba ambil koneksi hingga 3x jika gagal
    retries = 3
    for attempt in range(1, retries + 1):
        try:
            return await pool.acquire()
        except Exception as e:
            if attempt == retries:
                logger.error(f"Gagal mendapatkan koneksi database setelah {retries} percobaan: {e}")
                raise
            logger.warning(f"Gagal mendapatkan koneksi database (percobaan {attempt}/{retries}): {e}. Mencoba lagi...")