# 配置指南

本指南将帮助你获取和配置所需的 API Key。

## 1. 阿里云百炼 API Key

### 获取步骤

1. 访问 [阿里云百炼平台](https://bailian.console.aliyun.com/)
2. 登录阿里云账号
3. 进入"API Key管理"
4. 创建新的 API Key
5. 复制 API Key

### 配置

在 `.env` 文件中设置：

```env
BAILIAN_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
BAILIAN_REGION=beijing
```

## 2. DeepSeek API Key

### 获取步骤

1. 访问 [DeepSeek 平台](https://platform.deepseek.com/)
2. 注册并登录账号
3. 进入"API Keys"页面
4. 创建新的 API Key
5. 复制 API Key

### 配置

在 `.env` 文件中设置：

```env
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 价格

- Input tokens: $0.14 / 1M tokens
- Output tokens: $0.28 / 1M tokens

非常便宜，适合大量使用。

## 3. 高德地图 API Key

### 获取步骤

1. 访问 [高德开放平台](https://console.amap.com/)
2. 注册并登录账号
3. 进入"应用管理"
4. 创建新应用
5. 添加 Key：
   - **服务平台**：Web服务（用于 MCP）
   - **服务平台**：Web服务（用于 REST 回退）
6. 复制两个 Key

### 配置

在 `.env` 文件中设置：

```env
# 用于 MCP 连接
AMAP_MAPS_API_KEY=your_key_here

# 用于 REST 回退（可选，建议配置）
AMAP_WEB_SERVICE_KEY=your_key_here

# MCP 相关配置
AMAP_MCP_ENABLED=true
AMAP_HTTP_GEOCODE_FALLBACK=true
AMAP_GEOCODE_DEFAULT_CITY=北京
```

### 说明

- `AMAP_MAPS_API_KEY`：用于构建 MCP URL
- `AMAP_WEB_SERVICE_KEY`：当 MCP 调用失败时，自动回退到 REST API
- 两个 Key 可以使用同一个（但建议分开管理）

## 4. 完整的 .env 配置示例

```env
# 服务器配置
HOST=0.0.0.0
PORT=8007
STORAGE_PATH=Storage

# 阿里云百炼配置
BAILIAN_API_KEY=sk-7d45f77cbe0d46a5975c36819f1214d6
BAILIAN_REGION=beijing
BAILIAN_ASR_MODEL=qwen3-asr-flash
BAILIAN_TTS_MODEL=cosyvoice-v1

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
DEEPSEEK_BASE_URL=https://api.deepseek.com

# 高德地图配置
AMAP_MCP_ENABLED=true
AMAP_MCP_URL=
AMAP_MAPS_API_KEY=your_amap_maps_api_key
AMAP_WEB_SERVICE_KEY=your_amap_web_service_key
AMAP_MCP_DISTANCE_TYPE=0
AMAP_HTTP_GEOCODE_FALLBACK=true
AMAP_GEOCODE_DEFAULT_CITY=北京

# CORS 配置
FRONTEND_URL=http://localhost:5175
```

## 5. 验证配置

启动服务后，检查控制台日志：

```
✅ 百炼 ASR 服务已初始化（地域: beijing）
✅ DeepSeek 服务初始化成功
✅ 高德 MCP 服务已初始化 (URL: https://mcp.amap.com/mcp)
```

如果看到 ⚠️ 警告，说明对应的服务未正确配置。

## 6. 测试服务

### 测试 ASR

```bash
curl -X POST http://localhost:8007/api/process-audio \
  -F "audio=@test.webm"
```

### 测试完整流程

```bash
curl -X POST http://localhost:8007/api/process-audio-with-location \
  -F "audio=@test.webm"
```

## 常见问题

### Q: DeepSeek API Key 配置了但提示不可用？

A: 检查 Key 是否正确，是否有前缀 `sk-`。

### Q: 高德 MCP 连接失败？

A: 检查：
1. `AMAP_MAPS_API_KEY` 是否正确
2. 网络是否能访问 `https://mcp.amap.com`
3. Key 的配额是否用完

### Q: MCP 调用失败后会怎样？

A: 如果配置了 `AMAP_WEB_SERVICE_KEY` 和 `AMAP_HTTP_GEOCODE_FALLBACK=true`，会自动回退到 REST API。

### Q: 如何查看详细的调用日志？

A: 查看 `Storage` 目录下的日志文件：
- `mcp_call_*.json`：MCP 调用链
- `deepseek_*.json`：DeepSeek 提取结果
- `asr_*.json`：ASR 识别结果

## 安全建议

1. **不要提交 .env 文件到 Git**：`.env` 已在 `.gitignore` 中
2. **定期更换 API Key**：特别是泄露后
3. **使用环境变量**：生产环境使用系统环境变量
4. **限制 Key 权限**：在平台上设置 IP 白名单和使用限额
