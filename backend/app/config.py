# app/services/config.py or app/config.py (wherever it's located)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    #Database COnfiguration
    DATABASE_URL: str = "postgresql://plts_puskesmas_tanah_toraja:qwerty12345@localhost/plts"
    POSTGRES_USER: str = "plts_puskesmas_tanah_toraja"
    POSTGRES_PASSWORD: str = "qwerty12345"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "plts"
    #MQQT Configuration
    MQTT_BROKER: str = "192.168.18.39"
    MQTT_BROKER_HIVE: str = "broker.hivemq.com"
    MQTT_PORT: int = 1883
    MQTT_USER:str = ""                    
    MQTT_PASSWORD:str = ""                  
    MQTT_TOPIC:str = "puskesmas/plts/"
    MQTT_TOPIC_TEMPERATURE:str = "puskesmas/plts/temperature"
    MQTT_TOPIC_PZEM:str = "puskesmas/plts/pzem"
    
    API_PREFIX:str = "/api/v1"
    
    
    DEBUG: bool = True
    
    
    class Config:
        env_file = ".env"

config = Settings()