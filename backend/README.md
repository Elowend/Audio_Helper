# Audio Helper 后端服务

智能音频处理后端服务，完整流程：ASR 语音识别 → 地址提取 → 地理编码 → 智能推荐 → 语音合成。

## 功能特性

1. **音频上传与保存**：支持多种音频格式
2. **ASR 语音识别**：使用阿里云百炼 Qwen-ASR 服务
3. **智能地址提取**：使用 DeepSeek V4 Flash 从语音文本中提取起点和终点
4. **地理编码查询**：使用高德 MCP 服务获取地址的经纬度
5. **智能推荐生成**：使用 DeepSeek V4 Pro 生成个性化推荐 ⭐ 新增
6. **TTS 语音合成**：使用百炼 CosyVoice 将推荐转为语音 ⭐ 新增
7. **完整日志记录**：包含 MCP 调用链、推荐结果、语音文件等

## 快速开始

### 1. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必要的 API Key：

- `BAILIAN_API_KEY`：阿里云百炼 API Key
- `DEEPSEEK_API_KEY`：DeepSeek API Key
- `AMAP_MAPS_API_KEY`：高德地图 API Key（用于 MCP）
- `AMAP_WEB_SERVICE_KEY`：高德 Web 服务 Key（用于 REST 回退）

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://localhost:8007` 启动。

## API 端点

### 1. 基础音频处理

```
POST /api/process-audio
```

上传音频文件进行 ASR 识别。

**请求**：
- Content-Type: `multipart/form-data`
- Body: `audio` 文件

**响应**：
```json
{
  "message": "Audio processed successfully",
  "audio_file": {
    "filename": "audio_20260531_150000_abc123.webm",
    "size": 12345
  },
  "asr_result": {
    "text": "我想从北京天安门到故宫",
    "result_file": "asr_20260531_150000_abc123.json"
  }
}
```

### 2. 完整处理（ASR + 地址提取 + 地理编码 + 推荐 + TTS）

```
POST /api/process-audio-with-location
```

完整流程：ASR 识别 → DeepSeek 地址提取 → 高德 MCP 地理编码 → DeepSeek 推荐生成 → 百炼 TTS 语音合成。

**请求**：
- Content-Type: `multipart/form-data`
- Body: `audio` 文件

**响应**：
```json
{
  "request_id": "abc123",
  "message": "Audio processed with location successfully",
  "audio_file": {
    "filename": "audio_20260531_150000_abc123.webm",
    "size": 12345
  },
  "asr_result": {
    "text": "我想从北京天安门到故宫",
    "result_file": "asr_20260531_150000_abc123.json"
  },
  "addresses": {
    "origin": "北京天安门",
    "destination": "北京故宫",
    "raw_text": "我想从北京天安门到故宫"
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
  "recommendation": {
    "text": "从天安门到故宫距离很近，步行5-10分钟即可到达...",
    "summary": "建议步行前往，约5-10分钟",
    "audio_file": "tts_20260531_150000_abc123.mp3"
  },
  "logs": {
    "asr_log": "asr_20260531_150000_abc123.json",
    "deepseek_log": "deepseek_20260531_150000_abc123.json",
    "mcp_log": "mcp_call_abc123.json",
    "recommend_log": "recommend_20260531_150000_abc123.json",
    "tts_audio": "tts_20260531_150000_abc123.mp3"
  }
}
```

### 3. 获取音频文件

```
GET /api/audio/{filename}
```

获取生成的语音文件（TTS 输出）。

**示例**：
```
GET /api/audio/tts_20260531_150000_abc123.mp3
```

### 4. 健康检查

```
GET /health
```

检查服务状态，包括各个服务的可用性。

## 日志系统

### 控制台日志

服务运行时会输出中文简洁日志，包括：

- ℹ️ 信息日志
- ✅ 成功日志
- ⚠️ 警告日志
- ❌ 错误日志
- 🔹 步骤日志

### 文件日志

所有日志文件保存在 `Storage` 目录下：

1. **ASR 日志**：`asr_*.json` - ASR 识别结果
2. **DeepSeek 地址提取日志**：`deepseek_*.json` - 地址提取结果
3. **MCP 调用链日志**：`mcp_call_*.json` - 完整的 MCP 调用链
4. **推荐日志**：`recommend_*.json` - 智能推荐结果 ⭐ 新增
5. **TTS 音频**：`tts_*.mp3` - 生成的语音文件 ⭐ 新增

## MCP 调用链日志

每次 MCP 调用都会生成完整的调用链日志，包含：

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
      "timestamp": "2026-05-31T15:00:01"
    },
    {
      "name": "list_tools",
      "success": true,
      "tools": ["maps_geo", "maps_distance", "..."],
      "tool_count": 10,
      "timestamp": "2026-05-31T15:00:02"
    },
    {
      "name": "call_tool",
      "success": true,
      "tool": "maps_geo",
      "arguments_preview": {
        "address": "北京天安门",
        "city": "北京"
      },
      "timestamp": "2026-05-31T15:00:03"
    }
  ],
  "normalized_result": {
    "lng": 116.397428,
    "lat": 39.90923,
    "formatted_address": "北京市东城区天安门"
  },
  "fallback_used": false,
  "fallback_reason": null,
  "finished_at": "2026-05-31T15:00:04"
}
```

## 配置说明

### 高德 MCP 配置

- `AMAP_MCP_ENABLED`：是否启用 MCP（默认 true）
- `AMAP_MCP_URL`：完整的 MCP URL（可选，优先级最高）
- `AMAP_MAPS_API_KEY`：高德地图 API Key（用于拼接 MCP URL）
- `AMAP_WEB_SERVICE_KEY`：高德 Web 服务 Key（用于 REST 回退）
- `AMAP_MCP_DISTANCE_TYPE`：距离类型（0=直线，1=驾车，3=步行）
- `AMAP_HTTP_GEOCODE_FALLBACK`：是否启用 REST 回退（默认 true）
- `AMAP_GEOCODE_DEFAULT_CITY`：默认城市（用于短地名查询）

### DeepSeek 配置

- `DEEPSEEK_API_KEY`：DeepSeek API Key
- `DEEPSEEK_BASE_URL`：DeepSeek API 地址（默认官方地址）

## 开发文档

- [DeepSeek API 开发指南](docs/deepseek_api_guide.md)
- [MCP Client 开发指南](docs/mcp_client_guide.md)

## 技术栈

- **FastAPI**：Web 框架
- **OpenAI SDK**：调用 DeepSeek API（地址提取 + 推荐生成）
- **MCP Python SDK**：高德 MCP 客户端（地理编码）
- **阿里云百炼**：ASR 语音识别 + TTS 语音合成

## 许可证

MIT
