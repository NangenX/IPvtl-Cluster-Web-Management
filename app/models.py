from pydantic import BaseModel
from typing import List, Optional


class Channel(BaseModel):
    id: str
    name: Optional[str] = None
    status: Optional[str] = None


class Server(BaseModel):
    id: str
    name: Optional[str] = None
    host: str
    port: Optional[int] = None
    channels: Optional[List[str]] = []


class ServerStatus(BaseModel):
    id: str
    cpu: Optional[float] = None
    channels: List[Channel] = []
