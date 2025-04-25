# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import dan panggil create_tables terlebih dahulu sebelum mengimpor router
from app.db.models import create_tables
from app.db.database import init_db, pool
from app.services.mqqt_service import setup_mqtt, stop_mqtt
from app.api.routes import websocket,sensor_data
from app.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
# Inisialisasi aplikasi FastAPI
app = FastAPI(
    title ="API PLTS PUSKESMAS TANAH TORAJA",
    description= "API untuk aplikasi PLTS Puskesmas Tanah Toraja",
    version = "0.0.1"
)

# Tambahkan middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Buat tabel pada waktu startup aplikasi
#@app.on_event("startup")
#async def startup_event():
    #create_tables()
    #print("Database setup complete")

# Impor router setelah create_tables() dipanggil
from app.api.routes.auth import router as auth_router

# Sertakan router
app.include_router(auth_router, prefix=f"{config.API_PREFIX}/auth", tags=["auth"])
app.include_router(sensor_data.router, prefix=f"{config.API_PREFIX}/sensor", tags=["sensor"])
app.include_router(websocket.router, prefix=f"{config.API_PREFIX}/websocket", tags=["websocket"])

@app.on_event("startup")
async def startup_event():
    """Initialize database and MQTT client on startup"""
    await init_db()
    await setup_mqtt()
    logging.info("Application started")

@app.on_event("shutdown")
async def shutdown_event():
    """Close database and MQTT connection on shutdown"""
    if pool:
        await pool.close()
    stop_mqtt()
    logging.info("Application shutdown")


@app.get("/")
async def root():
    return {"message": "Assalamualaikum, selamat datang di API PLTS Puskesmas Tanah Toraja"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)