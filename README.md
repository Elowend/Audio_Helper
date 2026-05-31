# Audio Helper - 智能相遇地点推荐系统

基于语音输入的智能相遇地点推荐应用，通过语音识别、自然语言理解和地图服务，为用户推荐最佳相遇地点。

## 项目概述

### 核心功能

用户通过麦克风描述自己和朋友的位置，系统自动：
1. 🎙️ 语音识别（ASR）- 将语音转为文本
2. 🧠 槽位提取 - 识别两个位置信息
3. 🗺️ 地点计算 - 计算最佳相遇地点
4. 💬 生成回答 - 生成自然语言推荐
5. 🔊 语音合成（TTS）- 将回答转为语音播放

### 技术栈

| 层级 | 技术选型 |
|-----|---------|
| 前端 | React + Vite |
| 后端 | FastAPI (Python) |
| 语音识别 | 阿里云百炼 Qwen-ASR-Flash |
| NLU & NLG | DeepSeek |
| 地图服务 | 高德地图 MCP |
| 语音合成 | 阿里云百炼 CosyVoice |

## 项目结构

```
Audio_Helper/
├── frontend/              # React 前端
│   ├── src/
│   │   ├── App.jsx       # 主应用组件
│   │   ├── App.css       # 样式
│   │   └── main.jsx      # 入口文件
│   ├── package.json
│   └── vite.config.js    # 配置端口 5175
│
├── backend/               # FastAPI 后端
│   ├── main.py           # 主应用
│   ├── services/
│   │   └── bailian_asr.py # ASR 服务
│   ├── Storage/          # 存储目录
│   │   ├── audio_*.webm  # 音频文件
│   │   └── asr_*.json    # ASR 结果
│   ├── requirements.txt
│   └── .env              # 配置文件
│
└── docs/                  # 文档
    └── 百炼_接口文档.md   # 百炼 API 文档
```

## 快速开始

### 前置要求

- Node.js 18+
- Python 3.8+
- 阿里云百炼 API Key
- DeepSeek API Key
- 高德地图 API Key

### 1. 安装前端依赖

```bash
cd frontend
npm install
```

### 2. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 3. 配置环境变量

编辑 `backend/.env` 文件：

```bash
# 百炼配置（必填）
BAILIAN_API_KEY=your_bailian_api_key_here
BAILIAN_REGION=beijing

# DeepSeek 配置（后续使用）
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# 高德地图配置（后续使用）
AMAP_API_KEY=your_amap_api_key_here
```

### 4. 启动前端

```bash
cd frontend
npm run dev
```

前端运行在 `http://localhost:5175`

### 5. 启动后端

```bash
cd backend
python main.py
```

后端运行在 `http://localhost:8007`

## 当前进度

### ✅ 已完成

- [x] 前端页面搭建（React + 录音功能）
- [x] 后端服务框架（FastAPI）
- [x] 音频上传和存储
- [x] 百炼 ASR 集成（语音识别）
- [x] ASR 结果保存

### 🔄 进行中

- [ ] DeepSeek 槽位提取
- [ ] 高德 MCP 服务集成
- [ ] DeepSeek 回答生成
- [ ] 百炼 TTS 语音合成
- [ ] 端到端流程串联

## API 接口

### 后端 API

#### `POST /api/process-audio`

上传音频并处理。

**请求**：
- Content-Type: `multipart/form-data`
- 参数：`audio` (音频文件)

**响应**：
```json
{
  "message": "Audio processed successfully",
  "audio_file": {
    "filename": "audio_20260531_143000_abc123.webm",
    "size": 123456
  },
  "asr_result": {
    "text": "我在国贸，朋友在西二旗"
  }
}
```

## 开发规范

### 配置管理

- ✅ 所有配置从 `.env` 文件读取
- ✅ 不依赖系统环境变量
- ✅ 敏感信息不提交到 Git

### API 调用

- ✅ 使用 HTTP 请求，不使用 SDK
- ✅ ASR 使用 Base64 编码上传音频
- ✅ 自动清除代理环境变量

### 存储规范

- 音频文件：`audio_YYYYMMDD_HHMMSS_uuid.webm`
- ASR 结果：`asr_YYYYMMDD_HHMMSS_uuid.json`
- 统一保存在 `backend/Storage/` 目录

## 测试

### 测试 ASR 功能

1. 启动前后端服务
2. 打开前端页面：`http://localhost:5175`
3. 点击「开始录音」
4. 说话：例如"我在国贸，朋友在西二旗"
5. 点击「停止录音」
6. 查看页面显示的识别结果
7. 检查 `backend/Storage/` 目录：
   - `audio_*.webm` - 录音文件
   - `asr_*.json` - 识别结果

## 文档

- [百炼 API 接口文档](./docs/百炼_接口文档.md)
- [前端 README](./frontend/README.md)
- [后端 README](./backend/README.md)

## License

MIT
