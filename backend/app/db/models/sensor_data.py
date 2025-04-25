from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class TemperatureSensorReadings(BaseModel):
    device_id: str
    temperature: float
    time: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "sensor_1",
                "temperature": 25.5,
                "time": "2023-10-01T12:00:00Z"
            }
        }

class TemperatureSensorReadingsResponse(BaseModel):
    device_id: Optional[str] = None
    temperature: Optional[float] = None
    time: Optional[datetime] = None

class PZEM004TReading(BaseModel):
    device_id: str
    voltage: float
    current: float
    power: float
    energy: float
    time: Optional[datetime] = Field(default_factory=datetime.now)
    
    class Config:
        schema_extra = {
            "example": {
                "device_id": "sensor_2",
                "voltage": 230.0,
                "current": 10.0,
                "power": 2300.0,
                "energy": 5.0,
                "time": "2023-10-01T12:00:00Z"
            }
        }

class PZEM004TReadingResponse(BaseModel):
    device_id:Optional[str] = None
    voltage: Optional[float] = None
    current: Optional[float] = None
    power: Optional[float] = None
    energy: Optional[float] = None
    time: Optional[datetime] = None
    

class TemperatureStats(BaseModel):
    device_id: str
    avg_temperature: float
    min_temperature: float
    max_temperature: float
    reading_count: int
    last_reading_time: datetime

class PZEM004TStats(BaseModel):
    device_id: str
    avg_voltage: float
    avg_current: float
    avg_power: float
    total_energy: float
    reading_count: int
    last_reading_time: datetime