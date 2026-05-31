# MCP (Model Context Protocol) Python Client 开发指南

## 概述

MCP 是一个标准化协议，用于 LLM 应用与外部服务之间的上下文交互。本文档介绍如何使用 Python SDK 实现 MCP Client。

## 安装

```bash
pip install mcp>=1.14.0
```

## 基本架构

```
MCP Client (本地) <---> MCP Server (远端)
     ↑                      ↑
  读写流                 工具/资源
```

## Streamable HTTP Client 实现

### 1. 基本连接

```python
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def connect_mcp_server(url: str):
    async with streamable_http_client(url) as streams:
        # 注意：使用 *_ 接收额外返回值，避免 SDK 升级后解包失败
        read_stream, write_stream, *_ = streams
        
        async with ClientSession(read_stream, write_stream) as session:
            # 初始化连接
            await session.initialize()
            
            # 获取工具列表
            tools_response = await session.list_tools()
            tools = tools_response.tools
            
            # 调用工具
            result = await session.call_tool(
                "tool_name",
                arguments={"param": "value"}
            )
            
            return result
```

### 2. 完整的 MCP Client 类

```python
import asyncio
from typing import Dict, List, Any, Optional
from contextlib import AsyncExitStack
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

class MCPClient:
    def __init__(self, url: str):
        self.url = url
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools: List[Any] = []
    
    async def connect(self):
        """建立 MCP 连接"""
        streams = await self.exit_stack.enter_async_context(
            streamable_http_client(self.url)
        )
        read_stream, write_stream, *_ = streams
        
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(read_stream, write_stream)
        )
        
        # 初始化
        await self.session.initialize()
        
        # 获取工具列表
        tools_response = await self.session.list_tools()
        self.tools = tools_response.tools
        
        return self.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """调用 MCP 工具"""
        if not self.session:
            raise RuntimeError("MCP session not connected")
        
        result = await self.session.call_tool(tool_name, arguments)
        return result
    
    async def close(self):
        """关闭连接"""
        await self.exit_stack.aclose()
```

## 高德 MCP 服务接入

### URL 格式

```
https://mcp.amap.com/mcp?key=<AMAP_KEY>
```

### 常用工具

| 工具名 | 用途 | 参数 |
| --- | --- | --- |
| `maps_geo` | 地址转经纬度 | `address`, `city` |
| `maps_regeocode` | 经纬度转地址 | `location` |
| `maps_distance` | 计算距离 | `origins`, `destination`, `type` |
| `maps_direction_driving` | 驾车路线 | `origin`, `destination` |
| `maps_direction_walking` | 步行路线 | `origin`, `destination` |
| `maps_direction_transit_integrated` | 公交路线 | `origin`, `destination`, `city` |

### 距离类型

- `0`: 直线距离
- `1`: 驾车距离
- `3`: 步行距离

### 调用示例

```python
# 地址转经纬度
result = await client.call_tool(
    "maps_geo",
    arguments={
        "address": "天安门",
        "city": "北京"
    }
)

# 计算距离
result = await client.call_tool(
    "maps_distance",
    arguments={
        "origins": "116.397428,39.90923",
        "destination": "116.403119,39.915119",
        "type": 1  # 驾车距离
    }
)
```

## 最佳实践

### 1. 必须先 list_tools()

永远不要跳过 `list_tools()` 直接假设工具存在：

```python
# ❌ 错误：直接调用
result = await session.call_tool("maps_geo", {...})

# ✅ 正确：先获取工具列表
tools = await session.list_tools()
available_tools = {t.name for t in tools.tools}
if "maps_geo" in available_tools:
    result = await session.call_tool("maps_geo", {...})
```

### 2. 错误处理

```python
try:
    result = await client.call_tool("maps_geo", arguments)
except Exception as e:
    logger.error(f"MCP 调用失败: {str(e)}")
    # 可选：回退到 REST API
```

### 3. 完整的调用链日志

记录每个步骤的详细信息：

```python
log_entry = {
    "mcp_url_host": "https://mcp.amap.com/mcp",
    "steps": [
        {"name": "initialize", "success": True},
        {"name": "list_tools", "success": True, "tools": [...]},
        {"name": "call_tool", "tool": "maps_geo", "success": True}
    ]
}
```

### 4. 城市参数

短地名和重名地点必须传城市参数：

```python
# ✅ 正确
result = await client.call_tool("maps_geo", {
    "address": "天安门",
    "city": "北京"  # 必须传
})
```

## 返回值解析

MCP 返回的结构可能与 REST API 不同：

```python
def parse_geo_result(result):
    """解析地理编码结果（兼容 MCP 和 REST 格式）"""
    # MCP 格式
    if "results" in result:
        if result["results"]:
            item = result["results"][0]
            return {
                "lng": float(item["location"].split(",")[0]),
                "lat": float(item["location"].split(",")[1]),
                "formatted_address": item.get("formatted_address", "")
            }
    
    # REST 格式
    if "geocodes" in result:
        if result["geocodes"]:
            item = result["geocodes"][0]
            return {
                "lng": float(item["location"].split(",")[0]),
                "lat": float(item["location"].split(",")[1]),
                "formatted_address": item.get("formatted_address", "")
            }
    
    return None
```

## 安全注意事项

1. **不要记录完整 API Key**：日志中只记录 URL host
2. **参数脱敏**：不要记录敏感的用户信息
3. **结果摘要**：只记录必要的返回字段，不要记录完整原始数据

## 参考链接

- MCP 官方文档：https://modelcontextprotocol.io/
- Python SDK：https://github.com/modelcontextprotocol/python-sdk
- 高德地图 API：https://lbs.amap.com/api/webservice/summary
