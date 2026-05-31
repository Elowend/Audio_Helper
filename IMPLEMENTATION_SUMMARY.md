# Audio Helper 后端完善实施总结

## 完成内容

### 1. 文档整理

已创建并保存在 `backend/docs/` 目录：

- ✅ `deepseek_api_guide.md` - DeepSeek API 开发指南
- ✅ `mcp_client_guide.md` - MCP Python Client 开发指南
- ✅ `setup_guide.md` - 配置指南（API Key 获取步骤）

### 2. 服务模块开发

已创建三个核心服务模块：

#### `logger_service.py` - 日志服务
- ✅ 统一的中文简洁日志输出
- ✅ 支持信息、成功、警告、错误、步骤日志
- ✅ 日志文件保存功能
- ✅ 时间戳自动添加

#### `deepseek_service.py` - DeepSeek 地址提取服务
- ✅ 使用 OpenAI SDK 调用 DeepSeek API
- ✅ 从 ASR 文本中提取起点和终点地址
- ✅ JSON 格式化返回
- ✅ Token 使用统计
- ✅ 完整的错误处理

#### `mcp_service.py` - 高德 MCP 客户端服务
- ✅ 严格按照 `amap-mcp-service` SKILL 规范实现
- ✅ Streamable HTTP 连接高德 MCP Server
- ✅ 完整的调用链：initialize → list_tools → call_tool
- ✅ 地理编码（地址转经纬度）
- ✅ 兼容 MCP 和 REST 两种返回格式
- ✅ REST API 回退机制
- ✅ 城市参数支持
- ✅ 完整的 MCP 调用链日志记录

### 3. 主应用集成

更新 `main.py`：

- ✅ 导入所有新服务模块
- ✅ 统一使用中文日志
- ✅ 新增 `/api/process-audio-with-location` 端点
- ✅ 完整业务流程：ASR → DeepSeek → 高德MCP
- ✅ 所有节点的运行状态跟踪
- ✅ 详细的输出信息

### 4. 配置文件

- ✅ 更新 `requirements.txt` 添加依赖（openai, mcp）
- ✅ 更新 `.env` 添加高德 MCP 配置
- ✅ 创建 `.env.example` 配置模板
- ✅ 创建 `README.md` 完整项目文档

### 5. 前端更新

更新 `frontend/src/App.jsx`：

- ✅ 调用新的 `/api/process-audio-with-location` 接口
- ✅ 显示地址提取结果
- ✅ 显示地理编码结果（经纬度和详细地址）
- ✅ 显示请求 ID

## 完整流程

```
用户录音
  ↓
前端上传音频
  ↓
后端接收 (/api/process-audio-with-location)
  ↓
1. 保存音频文件 (Storage/audio_*.webm)
   [日志] ✅ 音频已保存
  ↓
2. ASR 语音识别 (阿里云百炼)
   [日志] 🔹 [ASR识别] 开始语音识别...
   [日志] ✅ ASR 识别完成
   [存储] Storage/asr_*.json
  ↓
3. DeepSeek 地址提取
   [日志] 🔹 [地址提取] 开始分析文本
   [日志] ✅ 地址提取完成 - 起点: xxx, 终点: xxx
   [日志] ℹ️  Token 使用: 输入=x, 输出=y, 总计=z
   [存储] Storage/deepseek_*.json
  ↓
4. 高德 MCP 连接
   [日志] 🔹 [MCP连接] 开始建立连接...
   [日志] 🔹 [MCP连接] 执行 initialize...
   [日志] 🔹 [MCP连接] 获取工具列表...
   [日志] ✅ MCP 连接成功，可用工具: maps_geo, maps_distance, ...
  ↓
5. 地理编码查询
   [日志] 🔹 [地理编码] 地址转经纬度: xxx (城市: xxx)
   [日志] 🔹 [MCP调用] 调用 maps_geo
   [日志] ✅ 地理编码成功: (lng, lat)
   [存储] Storage/mcp_call_*.json (完整调用链)
  ↓
6. 返回结果给前端
   [日志] ✅ 请求处理完成 [request_id]
  ↓
前端显示完整结果
```

## 日志系统

### 控制台日志格式

```
[15:00:00] ℹ️  信息日志
[15:00:01] ✅ 成功日志
[15:00:02] ⚠️  警告日志
[15:00:03] ❌ 错误日志
[15:00:04] 🔹 [步骤名] 步骤日志
```

### 文件日志

所有日志保存在 `Storage/` 目录：

1. **ASR 日志** - `asr_TIMESTAMP_ID.json`
   - ASR 识别结果
   - 识别文本
   - 置信度等

2. **DeepSeek 日志** - `deepseek_TIMESTAMP_ID.json`
   ```json
   {
     "origin": "起点地址",
     "destination": "终点地址",
     "raw_text": "原始文本",
     "model": "deepseek-v4-flash",
     "usage": {
       "prompt_tokens": 100,
       "completion_tokens": 50,
       "total_tokens": 150
     }
   }
   ```

3. **MCP 调用链日志** - `mcp_call_REQUEST_ID.json`
   ```json
   {
     "request_id": "abc123",
     "mcp_url_host": "https://mcp.amap.com/mcp",
     "mcp_enabled": true,
     "started_at": "2026-05-31T15:00:00",
     "steps": [
       {
         "name": "initialize",
         "success": true,
         "timestamp": "..."
       },
       {
         "name": "list_tools",
         "success": true,
         "tools": ["maps_geo", "..."],
         "tool_count": 10
       },
       {
         "name": "call_tool",
         "tool": "maps_geo",
         "arguments_preview": {"address": "...", "city": "..."},
         "success": true
       }
     ],
     "normalized_result": {...},
     "fallback_used": false,
     "finished_at": "2026-05-31T15:00:05"
   }
   ```

## MCP 规范遵循

严格按照 `.cursor/skills/amap-mcp-service/SKILL.md` 实现：

✅ **开发规范**
- 使用 Streamable HTTP MCP
- 完整流程：initialize → list_tools → call_tool
- 不跳过 list_tools()

✅ **环境变量规范**
- 优先支持 AMAP_MCP_URL
- 支持 AMAP_MAPS_API_KEY 拼接
- REST 回退配置

✅ **Python MCP 写法**
- 使用 `read_stream, write_stream, *_` 避免解包失败
- ClientSession 正确使用

✅ **结果解析规范**
- 兼容 MCP 和 REST 两种格式
- 归一化为统一结构

✅ **留档规范**
- 完整的 MCP 调用链日志
- 从 list_tools() 开始记录
- 每次 call_tool() 都记录
- REST 回退标记

✅ **城市与多候选规范**
- 支持默认城市配置
- 调用时传递 city 参数

✅ **REST 回退规范**
- 配置可控
- 显式标记 via_mcp
- 记录 fallback_reason

## 使用指南

### 1. 安装依赖

```bash
cd backend
source venv/bin/activate  # 如果已有虚拟环境
pip install -r requirements.txt
```

### 2. 配置 API Key

编辑 `backend/.env` 文件：

```env
# 阿里云百炼（ASR）
BAILIAN_API_KEY=sk-xxxxx

# DeepSeek（地址提取）
DEEPSEEK_API_KEY=sk-xxxxx

# 高德地图（MCP）
AMAP_MAPS_API_KEY=your_key
AMAP_WEB_SERVICE_KEY=your_key  # 用于回退
```

详细配置指南：`backend/docs/setup_guide.md`

### 3. 启动后端

```bash
cd backend
python main.py
```

### 4. 启动前端

```bash
cd frontend
npm run dev
```

### 5. 测试

打开浏览器访问 `http://localhost:5175`，点击"开始录音"，说：

```
"我想从北京天安门到故宫"
```

将会看到完整的处理结果：
- ASR 识别文本
- 提取的起点和终点
- 两个地点的经纬度坐标
- 详细地址信息

### 6. 查看日志

- **控制台日志**：后端终端实时显示
- **文件日志**：`backend/Storage/` 目录

## API 端点

### 旧端点（仅 ASR）
```
POST /api/process-audio
```

### 新端点（完整流程）
```
POST /api/process-audio-with-location
```

返回示例：
```json
{
  "request_id": "abc123",
  "message": "Audio processed with location successfully",
  "asr_result": {
    "text": "我想从北京天安门到故宫"
  },
  "addresses": {
    "origin": "北京天安门",
    "destination": "北京故宫"
  },
  "locations": {
    "origin": {
      "lng": 116.397428,
      "lat": 39.90923,
      "formatted_address": "北京市东城区天安门",
      "via_mcp": true
    },
    "destination": {
      "lng": 116.403119,
      "lat": 39.915119,
      "formatted_address": "北京市东城区故宫博物院",
      "via_mcp": true
    }
  },
  "logs": {
    "asr_log": "asr_*.json",
    "deepseek_log": "deepseek_*.json",
    "mcp_log": "mcp_call_*.json"
  }
}
```

## 技术栈

- **FastAPI** - Web 框架
- **OpenAI SDK** - 调用 DeepSeek API（兼容格式）
- **MCP Python SDK (>=1.14.0)** - 高德 MCP 客户端
- **阿里云百炼** - ASR 语音识别
- **React + Vite** - 前端

## 下一步建议

1. **添加距离计算**：使用 `maps_distance` 工具
2. **添加路线规划**：使用 `maps_direction_*` 工具
3. **中点推荐**：计算两个地点的中点，推荐相遇地点
4. **前端地图展示**：集成地图组件显示位置
5. **用户反馈**：让用户确认提取的地址是否正确
6. **历史记录**：保存用户的查询历史

## 验收清单

✅ 后端环境能正常 import `mcp`
✅ MCP URL 解析正确，Key 不会明文出现在日志中
✅ `initialize()` + `list_tools()` 冒烟通过
✅ 留档中能看到从 `list_tools()` 到每次 `call_tool()` 的完整链路
✅ `maps_geo` 能处理真实返回体，并能归一化经纬度
✅ 业务响应能区分本次结果来自 MCP 还是 REST 回退
✅ 中文简洁日志完整，能跟踪所有节点运行状态
✅ 所有 MCP 调用日志完整存储在 Storage 中

## 完成时间

2026年5月31日
