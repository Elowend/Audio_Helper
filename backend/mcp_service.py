"""
高德 MCP 客户端服务
按照 amap-mcp-service SKILL 规范实现
"""
import os
import json
import httpx
from datetime import datetime
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from logger_service import logger


class AmapMCPService:
    """高德 MCP 客户端服务"""
    
    def __init__(self):
        self.mcp_enabled = os.getenv("AMAP_MCP_ENABLED", "true").lower() == "true"
        self.mcp_url = self._build_mcp_url()
        self.web_service_key = os.getenv("AMAP_WEB_SERVICE_KEY")
        self.default_city = os.getenv("AMAP_GEOCODE_DEFAULT_CITY", "")
        self.distance_type = int(os.getenv("AMAP_MCP_DISTANCE_TYPE", "0"))
        self.fallback_enabled = os.getenv("AMAP_HTTP_GEOCODE_FALLBACK", "true").lower() == "true"
        
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[Any] = []
        
        # 调用链日志
        self.call_log: Dict[str, Any] = {
            "request_id": "",
            "mcp_url_host": self._get_url_host(self.mcp_url) if self.mcp_url else None,
            "mcp_enabled": self.mcp_enabled,
            "started_at": "",
            "steps": [],
            "selected_tools": [],
            "normalized_result": {},
            "fallback_used": False,
            "fallback_reason": None,
            "finished_at": ""
        }
        
        if self.mcp_enabled and self.mcp_url:
            logger.success(f"高德 MCP 服务已初始化 (URL: {self._get_url_host(self.mcp_url)})")
        else:
            logger.warning("高德 MCP 未启用或 URL 未配置")
    
    def _build_mcp_url(self) -> Optional[str]:
        """构建 MCP URL"""
        # 优先使用完整 URL
        mcp_url = os.getenv("AMAP_MCP_URL")
        if mcp_url:
            return mcp_url
        
        # 使用 API Key 拼接
        api_key = os.getenv("AMAP_MAPS_API_KEY")
        if api_key and api_key != "your_amap_api_key_here":
            return f"https://mcp.amap.com/mcp?key={api_key}"
        
        return None
    
    @staticmethod
    def _get_url_host(url: str) -> str:
        """获取 URL host（不包含 key 参数）"""
        if "?" in url:
            return url.split("?")[0]
        return url
    
    def _log_step(self, step_name: str, success: bool, **kwargs):
        """记录步骤日志"""
        step_entry = {
            "name": step_name,
            "success": success,
            "timestamp": datetime.now().isoformat()
        }
        step_entry.update(kwargs)
        self.call_log["steps"].append(step_entry)
    
    async def connect(self, request_id: str) -> bool:
        """
        建立 MCP 连接
        
        Args:
            request_id: 请求 ID
            
        Returns:
            是否连接成功
        """
        if not self.mcp_enabled or not self.mcp_url:
            logger.warning("MCP 未启用，跳过连接")
            return False
        
        self.call_log["request_id"] = request_id
        self.call_log["started_at"] = datetime.now().isoformat()
        
        try:
            logger.step("MCP连接", "开始建立连接...")
            
            # 建立 Streamable HTTP 连接
            streams = await self.exit_stack.enter_async_context(
                streamable_http_client(self.mcp_url)
            )
            
            # 使用 *_ 接收额外返回值，避免 SDK 升级后解包失败
            read_stream, write_stream, *_ = streams
            
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(read_stream, write_stream)
            )
            
            # 初始化
            logger.step("MCP连接", "执行 initialize...")
            await self.session.initialize()
            self._log_step("initialize", True)
            
            # 获取工具列表
            logger.step("MCP连接", "获取工具列表...")
            tools_response = await self.session.list_tools()
            self.tools = tools_response.tools
            
            tool_names = [tool.name for tool in self.tools]
            logger.success(f"MCP 连接成功，可用工具: {', '.join(tool_names[:5])}{'...' if len(tool_names) > 5 else ''}")
            
            self._log_step(
                "list_tools",
                True,
                tools=tool_names,
                tool_count=len(tool_names)
            )
            
            return True
            
        except Exception as e:
            logger.error("MCP 连接失败", e)
            self._log_step("connect", False, error=str(e))
            return False
    
    async def geocode(self, address: str, city: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        地址转经纬度
        
        Args:
            address: 地址
            city: 城市（可选，但建议传入）
            
        Returns:
            {
                "lng": 经度,
                "lat": 纬度,
                "formatted_address": "格式化地址",
                "via_mcp": True/False
            }
        """
        if not address:
            return None
        
        # 使用默认城市
        if not city and self.default_city:
            city = self.default_city
            logger.info(f"使用默认城市: {city}")
        
        logger.step("地理编码", f"地址转经纬度: {address} (城市: {city or '未指定'})")
        
        # 尝试 MCP 调用
        if self.session and self.tools:
            try:
                result = await self._geocode_via_mcp(address, city)
                if result:
                    result["via_mcp"] = True
                    return result
            except Exception as e:
                import traceback
                error_details = {
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "traceback": traceback.format_exc()
                }
                logger.error(f"MCP 地理编码失败: {error_details['error_type']} - {error_details['error_message']}", e)
                self._log_step("call_tool_maps_geo", False, error=error_details)
        
        # MCP 失败，尝试 REST 回退
        if self.fallback_enabled and self.web_service_key:
            logger.warning("MCP 调用失败，使用 REST API 回退")
            self.call_log["fallback_used"] = True
            self.call_log["fallback_reason"] = "MCP 调用失败或不可用"
            
            try:
                result = await self._geocode_via_rest(address, city)
                if result:
                    result["via_mcp"] = False
                    return result
            except Exception as e:
                logger.error("REST API 地理编码失败", e)
        
        return None
    
    async def _geocode_via_mcp(self, address: str, city: Optional[str]) -> Optional[Dict[str, Any]]:
        """通过 MCP 进行地理编码"""
        # 检查工具是否存在
        tool_names = {tool.name for tool in self.tools}
        if "maps_geo" not in tool_names:
            logger.error("MCP 工具 'maps_geo' 不存在")
            return None
        
        # 构建参数
        arguments = {"address": address}
        if city:
            arguments["city"] = city
        
        logger.step("MCP调用", f"调用 maps_geo - {arguments}")
        
        # 调用工具
        result = await self.session.call_tool("maps_geo", arguments)
        
        # 提取原始 key（安全地）
        raw_keys = []
        try:
            if result.content and hasattr(result.content[0], 'text'):
                text_data = result.content[0].text
                if isinstance(text_data, dict):
                    raw_keys = list(text_data.keys())
                elif isinstance(text_data, str):
                    # 如果是字符串，尝试解析为 JSON 获取 keys
                    parsed = json.loads(text_data)
                    raw_keys = list(parsed.keys()) if isinstance(parsed, dict) else []
        except Exception:
            pass
        
        # 记录调用日志
        self._log_step(
            "call_tool",
            True,
            tool="maps_geo",
            arguments_preview=arguments,
            raw_keys=raw_keys
        )
        
        # 解析结果
        parsed = self._parse_geo_result(result)
        
        if parsed:
            logger.success(f"地理编码成功: ({parsed['lng']}, {parsed['lat']})")
            self.call_log["normalized_result"] = parsed
        else:
            logger.error("地理编码结果解析失败")
        
        return parsed
    
    async def _geocode_via_rest(self, address: str, city: Optional[str]) -> Optional[Dict[str, Any]]:
        """通过 REST API 进行地理编码（回退方案）"""
        url = "https://restapi.amap.com/v3/geocode/geo"
        params = {
            "key": self.web_service_key,
            "address": address
        }
        if city:
            params["city"] = city
        
        logger.step("REST回退", f"调用高德 REST API")
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
            
            if data.get("status") == "1" and data.get("geocodes"):
                geocode = data["geocodes"][0]
                location = geocode["location"].split(",")
                
                result = {
                    "lng": float(location[0]),
                    "lat": float(location[1]),
                    "formatted_address": geocode.get("formatted_address", ""),
                    "level": geocode.get("level", "")
                }
                
                logger.success(f"REST 地理编码成功: ({result['lng']}, {result['lat']})")
                return result
        
        return None
    
    def _parse_geo_result(self, result: Any) -> Optional[Dict[str, Any]]:
        """
        解析地理编码结果（兼容 MCP 和 REST 格式）
        
        按照 SKILL 规范：
        - MCP 形态：顶层 results[]，元素里包含 location
        - REST 形态：status + geocodes[]，元素里包含 location
        """
        try:
            # 提取原始数据
            if hasattr(result, 'content') and result.content:
                content = result.content[0]
                if hasattr(content, 'text'):
                    text_data = content.text
                    logger.info(f"MCP 原始返回类型: {type(text_data)}")
                    if isinstance(text_data, str):
                        logger.info(f"MCP 原始返回内容（前200字符）: {text_data[:200]}")
                        data = json.loads(text_data)
                    else:
                        data = text_data
                else:
                    logger.warning("MCP 返回的 content 没有 text 属性")
                    data = {}
            else:
                logger.warning("MCP 返回结果没有 content")
                data = {}
            
            # MCP 形态：results[]
            if "results" in data and data["results"]:
                item = data["results"][0]
                location = item.get("location", "").split(",")
                if len(location) == 2:
                    return {
                        "lng": float(location[0]),
                        "lat": float(location[1]),
                        "formatted_address": item.get("formatted_address", ""),
                        "level": item.get("level", ""),
                        "raw": item
                    }
            
            # REST 形态：geocodes[]
            if "geocodes" in data and data["geocodes"]:
                item = data["geocodes"][0]
                location = item.get("location", "").split(",")
                if len(location) == 2:
                    return {
                        "lng": float(location[0]),
                        "lat": float(location[1]),
                        "formatted_address": item.get("formatted_address", ""),
                        "level": item.get("level", ""),
                        "raw": item
                    }
            
            # 解析失败，记录实际的数据结构
            if isinstance(data, dict):
                logger.error(f"地理编码结果解析失败，实际顶层 key: {list(data.keys())}")
                logger.error(f"实际数据结构: {json.dumps(data, ensure_ascii=False)[:200]}...")
            elif isinstance(data, str):
                logger.error(f"地理编码返回了字符串而非字典: {data[:200]}")
            else:
                logger.error(f"地理编码结果类型错误: {type(data).__name__}, 内容: {str(data)[:200]}")
            
        except Exception as e:
            logger.error("解析地理编码结果时出错", e)
        
        return None
    
    async def close(self):
        """关闭 MCP 连接"""
        self.call_log["finished_at"] = datetime.now().isoformat()
        await self.exit_stack.aclose()
        logger.info("MCP 连接已关闭")
    
    async def save_call_log(self, storage_path: Path, request_id: str):
        """保存 MCP 调用链日志"""
        try:
            filename = f"mcp_call_{request_id}.json"
            file_path = storage_path / filename
            
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(self.call_log, f, ensure_ascii=False, indent=2)
            
            logger.success(f"MCP 调用链日志已保存: {filename}")
            return file_path
            
        except Exception as e:
            logger.error("保存 MCP 调用链日志失败", e)
            return None
