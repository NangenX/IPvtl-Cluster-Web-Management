"""数据模型定义"""
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, computed_field

class ChannelState(str, Enum):
    """通道状态枚举（与 IPVTL API 一致）"""
    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"

class ServerStatus(str, Enum):
    """服务器连接状态"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

class ChannelInfo(BaseModel):
    """通道信息"""
    id: int  # 通道编号 (1-based)
    state: ChannelState = ChannelState.IDLE
    status: str = ""  # 运行状态描述 "12:34:56 30fps@1234Kbps"
    
    @computed_field
    @property
    def name(self) -> str:
        return f"Channel {self.id}"

class IPVTLStatusResponse(BaseModel):
    """IPVTL /status 接口响应"""
    channels: list[dict]  # [{"state": "idle", "status": "..."}, ...]
    cpu: list[int]  # 每核心 CPU 使用率

class ServerConfig(BaseModel):
    """服务器配置（来自 JSON 文件）"""
    id: str
    name: str
    host: str
    port: int = 9527  # IPVTL 默认端口
    description: Optional[str] = None

    @property
    def base_url(self) -> str:
        return f"http://{self.host}:{self.port}"

class ServerState(BaseModel):
    """服务器运行状态（缓存数据）"""
    server_id: str
    status: ServerStatus = ServerStatus.OFFLINE
    cpu_cores: list[int] = Field(default_factory=list)  # 每核心 CPU
    cpu_avg: Optional[float] = None  # 平均 CPU
    channels: list[ChannelInfo] = Field(default_factory=list)
    last_poll_time: Optional[datetime] = None
    error_message: Optional[str] = None

class ServerResponse(BaseModel):
    """API 响应：服务器完整信息"""
    config: ServerConfig
    state: ServerState

class ChannelActionResult(BaseModel):
    """通道操作结果"""
    success: bool
    message: str
    channel_id: int
    server_id: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str = "ok"
    version: str
    servers_count: int
    poll_interval: int
