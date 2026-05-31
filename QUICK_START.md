# Audio Helper 快速启动指南

## 🚀 快速开始

### 前置要求

- Python 3.8+
- Node.js 16+
- 麦克风权限

### 1️⃣ 安装后端依赖

```bash
# 进入后端目录
cd backend

# 确保虚拟环境已激活
source venv/bin/activate

# 安装新添加的依赖
pip install openai mcp

# 或者重新安装所有依赖
pip install -r requirements.txt
```

### 2️⃣ 配置 API Keys

编辑 `backend/.env` 文件，配置以下 API Keys：

```env
# 阿里云百炼（必需 - 用于 ASR）
BAILIAN_API_KEY=sk-你的百炼key

# DeepSeek（必需 - 用于地址提取）
DEEPSEEK_API_KEY=sk-你的deepseek_key

# 高德地图（必需 - 用于地理编码）
AMAP_MAPS_API_KEY=你的高德key
AMAP_WEB_SERVICE_KEY=你的高德key
```

📝 **获取 API Keys 的详细步骤**：查看 `backend/docs/setup_guide.md`

### 3️⃣ 测试服务配置

在启动前，先测试各个服务是否正确配置：

```bash
cd backend
python test_services.py
```

应该看到：
```
✅ DeepSeek 服务测试通过 ✓
✅ 高德 MCP 服务测试通过 ✓
✅ 完整流程测试通过 ✓
🎉 所有测试通过！服务配置正确。
```

如果有失败，请检查对应的 API Key 配置。

### 4️⃣ 启动后端服务

```bash
# 在 backend 目录，虚拟环境已激活
python main.py
```

应该看到：
```
========================================
🚀 启动 Audio Helper API 服务
   地址: http://0.0.0.0:8007
   存储路径: /path/to/Storage
========================================
✅ 百炼 ASR 服务已初始化（地域: beijing）
✅ DeepSeek 服务初始化成功
✅ 高德 MCP 服务已初始化 (URL: https://mcp.amap.com/mcp)
```

### 5️⃣ 启动前端

打开新的终端窗口：

```bash
cd frontend
npm run dev
```

### 6️⃣ 开始使用

1. 打开浏览器访问 `http://localhost:5175`
2. 点击"🎙 开始录音"
3. 说出包含地址的语音，例如：
   - "我想从北京天安门到故宫"
   - "我在上海东方明珠，朋友在南京路"
   - "从杭州西湖到灵隐寺怎么走"
4. 点击"⏹ 停止录音"
5. 查看处理结果：
   - 📝 ASR 识别的文本
   - 📍 提取的起点和终点地址
   - 🗺️ 地理编码结果（经纬度和详细地址）

### 7️⃣ 查看日志

所有处理日志保存在 `backend/Storage/` 目录：

```bash
cd backend/Storage
ls -lt | head -10  # 查看最新的日志文件
```

- `asr_*.json` - ASR 识别日志
- `deepseek_*.json` - DeepSeek 地址提取日志
- `mcp_call_*.json` - 高德 MCP 调用链日志

## 🔍 故障排查

### 问题 1：后端启动时提示端口被占用

```
ERROR: address already in use
```

**解决方案**：
```bash
# 查找占用 8007 端口的进程
lsof -ti :8007 | xargs kill -9

# 重新启动
python main.py
```

### 问题 2：DeepSeek 服务不可用

**检查**：
1. `.env` 文件中的 `DEEPSEEK_API_KEY` 是否正确
2. Key 是否有前缀 `sk-`
3. Key 是否有额度

**测试**：
```bash
python test_services.py
```

### 问题 3：高德 MCP 连接失败

**检查**：
1. `.env` 文件中的 `AMAP_MAPS_API_KEY` 是否正确
2. 网络是否能访问 `https://mcp.amap.com`
3. Key 的配额是否用完

**测试**：
```bash
python test_services.py
```

### 问题 4：前端显示"处理失败"

**查看后端日志**：
后端终端会显示详细的错误信息和堆栈跟踪。

**查看文件日志**：
```bash
cd backend/Storage
# 查看最新的错误日志
cat mcp_call_*.json | grep error
```

### 问题 5：语音识别不准确

**原因**：
- 录音时间太短
- 环境噪音太大
- 麦克风质量问题

**建议**：
- 说话清晰，语速适中
- 在安静的环境中录音
- 录音时长保持在 3-10 秒

## 📚 更多文档

- [完整实施总结](IMPLEMENTATION_SUMMARY.md) - 了解系统架构和完整流程
- [后端 README](backend/README.md) - API 文档和配置说明
- [配置指南](backend/docs/setup_guide.md) - 详细的 API Key 获取步骤
- [DeepSeek 开发指南](backend/docs/deepseek_api_guide.md) - DeepSeek API 使用说明
- [MCP 开发指南](backend/docs/mcp_client_guide.md) - MCP 客户端开发指南

## 💡 使用提示

1. **清晰表达地址**：说话时尽量包含城市名称，如"北京天安门"而不是"天安门"
2. **明确起点终点**：使用"从...到..."的句式，如"从A到B"
3. **查看完整日志**：每次请求都会生成完整的调用链日志，方便排查问题
4. **关注控制台**：后端控制台有详细的中文日志，可以实时了解处理进度

## 🎯 测试用例

以下是一些测试用例，可以用来验证系统：

1. **简单路线**：
   - "我想从北京天安门到故宫"
   - "从上海外滩到东方明珠"

2. **跨城市**：
   - "我在北京西站，朋友在天津站"

3. **具体地址**：
   - "从杭州西湖文化广场到杭州东站"

4. **口语化表达**：
   - "我在三里屯，要去国贸"

## 🐛 报告问题

如果遇到问题：
1. 查看后端控制台日志
2. 查看 `Storage/` 目录下的日志文件
3. 运行 `python test_services.py` 测试配置
4. 记录详细的错误信息和复现步骤

---

**祝使用愉快！** 🎉
