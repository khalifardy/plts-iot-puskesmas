from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Any

class DeviceBase(BaseModel):
    device_id: str
    name: str
    location: Optional[str]=None
    type : Optional[str]=None
    
class DeviceCreate(DeviceBase):
    pass

class DeviceResponse(DeviceBase):
    created_at: datetime
    last_active: Optional[datetime]=None
    
class DeviceConfig(BaseModel):
    device_id: str
    config: Dict[str, Any]
    
class Alert(BaseModel):
    id: Optional[int] = None
    device_id: str
    alert_type: str
    message: str
    threshold: float
    actual_value: float
    created_at: Optional[datetime] = None
    acknowledged: bool = False
    
    