"""
日志服务模块
提供统一的中文简洁日志输出
"""
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class LoggerService:
    """日志服务类"""
    
    @staticmethod
    def info(message: str):
        """信息日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ℹ️  {message}")
    
    @staticmethod
    def success(message: str):
        """成功日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ✅ {message}")
    
    @staticmethod
    def warning(message: str):
        """警告日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] ⚠️  {message}")
    
    @staticmethod
    def error(message: str, error: Optional[Exception] = None):
        """错误日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        if error:
            print(f"[{timestamp}] ❌ {message}: {str(error)}")
        else:
            print(f"[{timestamp}] ❌ {message}")
    
    @staticmethod
    def step(step_name: str, message: str):
        """步骤日志"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] 🔹 [{step_name}] {message}")
    
    @staticmethod
    async def save_log_file(
        storage_path: Path,
        filename: str,
        data: Dict[str, Any]
    ):
        """保存日志文件到 Storage"""
        try:
            file_path = storage_path / filename
            
            # 添加时间戳
            data["logged_at"] = datetime.now().isoformat()
            
            # 写入 JSON 文件
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            LoggerService.success(f"日志已保存: {filename}")
            return file_path
            
        except Exception as e:
            LoggerService.error(f"保存日志文件失败", e)
            return None


# 全局日志实例
logger = LoggerService()
