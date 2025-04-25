from fastapi import APIRouter, Query, HTTPException
from app.db.models.sensor_data import(
    TemperatureSensorReadings,
    PZEM004TReading,
    TemperatureSensorReadingsResponse,
    PZEM004TReadingResponse,
    TemperatureStats,
    PZEM004TStats,
)

from app.services.sensor_service import (
    get_temperature_sensor_readings,
    get_pzem004t_sensor_readings,
    get_aggregated_data_pzem004t,
    get_aggregated_data_temperature,
    get_temperature_sensor_stats,
    get_pzem004t_sensor_stats,
)

from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/readings/temperature", response_model=List[TemperatureSensorReadingsResponse])
async def read_sensor_data_temperature(
    device_id: Optional[str] = Query(None, description="ID of the device"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
    limit: Optional[int] = Query(100, description="Number of readings to return"),
):
    """Menampilkan data sensor temperatur dengan parameter pencarian

    Args:
        device_id (Optional[str], optional): _description_. Defaults to Query(None, description="ID of the device").
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
        limit (Optional[int], optional): _description_. Defaults to Query(100, description="Number of readings to return").
    """
    
    try:
        readings = await get_temperature_sensor_readings(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        
        return readings
    except Exception as e:
        logger.error(f"Error retrieving temperature sensor data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    
@router.get("/readings/pzem004t", response_model=List[PZEM004TReadingResponse])
async def read_sensor_data_pzem004t(
    device_id: Optional[str] = Query(None, description="ID of the device"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
    limit: Optional[int] = Query(100, description="Number of readings to return"),
):
    """Menampilkan data sensor PZEM004T dengan parameter pencarian

    Args:
        device_id (Optional[str], optional): _description_. Defaults to Query(None, description="ID of the device").
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
        limit (Optional[int], optional): _description_. Defaults to Query(100, description="Number of readings to return").
    """
    
    try:
        readings = await get_pzem004t_sensor_readings(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return readings
    except Exception as e:
        logger.error(f"Error retrieving PZEM004T sensor data: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/stats/temperature/{device_id}", response_model=TemperatureStats)
async def read_sensor_stats_temperature(
    device_id:str,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
) :
    """mendapatkan statistik untuk suatu spesifik device untuk beberapa periode waktu
    Args:
        device_id (str): _description_
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
    """
    
    try:
        stats = await get_temperature_sensor_stats(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )
        return stats
    except Exception as e:
        logger.error(f"Error retrieving temperature sensor stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/pzem004t/{device_id}", response_model=PZEM004TStats)
async def read_sensor_stats_pzem004t(
    device_id:str,
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
) :
    """mendapatkan statistik untuk suatu spesifik device untuk beberapa periode waktu
    Args:
        device_id (str): _description_
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
    """
    
    try:
        stats = await get_pzem004t_sensor_stats(
            device_id=device_id,
            start_time=start_time,
            end_time=end_time,
        )
        return stats
    except Exception as e:
        logger.error(f"Error retrieving PZEM004T sensor stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aggregated/temperature/{device_id}")
async def read_aggregated_data_temperature(
    device_id: str,
    interval: str = Query("1 hour", description="Aggregation interval (e.g., '1 minute', '1 hour', '1 day')"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
):
    """Get time-bucketed aggregated data for charts

    Args:
        device_id (str): _description_
        interval (str, optional): _description_. Defaults to Query("1h". description="Aggregation interval (e.g., '1 minute', '1 hour', '1 day')").
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
    """
    
    try:
        data = await get_aggregated_data_temperature(
            device_id=device_id,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )
        
        return data
    
    except Exception as e:
        logger.error(f"Error retrieving aggregated temperature data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/aggregated/pzem004t/{device_id}")
async def read_aggregated_data_pzem004t(
    device_id: str,
    interval: str = Query("1 hour", description="Aggregation interval (e.g., '1 minute', '1 hour', '1 day')"),
    start_time: Optional[datetime] = Query(None, description="Start time (ISO Format)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO Format)"),
):
    """Get time-bucketed aggregated data for charts

    Args:
        device_id (str): _description_
        interval (str, optional): _description_. Defaults to Query("1h". description="Aggregation interval (e.g., '1 minute', '1 hour', '1 day')").
        start_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="Start time (ISO Format)").
        end_time (Optional[datetime], optional): _description_. Defaults to Query(None, description="End time (ISO Format)").
    """
    
    try:
        data = await get_aggregated_data_pzem004t(
            device_id=device_id,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
        )
        
        return data
    
    except Exception as e:
        logger.error(f"Error retrieving aggregated PZEM004T data: {e}")
        raise HTTPException(status_code=500, detail=str(e))
