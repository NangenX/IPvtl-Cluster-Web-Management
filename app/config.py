"""应用配置管理"""
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    """应用设置"""
    # 应用信息
    app_name: str = "IPvtl Cluster Manager"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # 服务器配置文件路径
    servers_config_path: Path = Field(
        default=Path("servers/servers.json"),
        description="服务器配置文件路径"
    )
    
    # 轮询配置
    poll_interval: int = Field(default=30, description="轮询间隔(秒)")
    poll_timeout: float = Field(default=5.0, description="单次请求超时(秒)")
    poll_max_concurrent: int = Field(default=10, description="最大并发轮询数")
    
    # 通道操作配置
    channel_stop_timeout: float = Field(default=30.0, description="停止通道超时")
    channel_start_timeout: float = Field(default=30.0, description="启动通道超时")
    channel_restart_delay: float = Field(default=2.0, description="重启间隔延迟")
    
    class Config:
        env_file = ".env"
        env_prefix = "IPVTL_"

# 全局配置实例
settings = Settings()
