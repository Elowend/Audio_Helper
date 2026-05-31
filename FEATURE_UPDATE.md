# 功能更新：智能推荐 + 语音输出

## 🎉 新增功能

### 1. DeepSeek 智能推荐生成

基于高德 MCP 返回的地理信息，使用 DeepSeek V4 Pro 模型生成个性化推荐：

- ✅ 分析起点和终点的地理位置
- ✅ 理解用户的意图（如：找中间地点、询问路线等）
- ✅ 生成友好、实用的推荐文本
- ✅ 控制在 100-200 字以内

### 2. 百炼 TTS 语音合成

将推荐文本转换为语音输出：

- ✅ 使用阿里云百炼 CosyVoice TTS 模型
- ✅ 支持多种音色选择
- ✅ 高质量 MP3 格式输出
- ✅ 前端自动播放推荐语音

## 🔄 完整处理流程

```
用户录音
  ↓
1. ASR 语音识别 (百炼 Qwen-ASR)
  ↓
2. 地址提取 (DeepSeek V4 Flash)
  ↓
3. 地理编码 (高德 MCP)
  ↓
4. 智能推荐生成 (DeepSeek V4 Pro) ⭐ 新增
  ↓
5. TTS 语音合成 (百炼 CosyVoice) ⭐ 新增
  ↓
返回结果：文本 + 语音
```

## 📋 技术实现

### 后端新增模块

#### 1. `services/bailian_tts.py` - TTS 服务

```python
class BaiLianTTSService:
    async def synthesize(text, voice="longxiaochun") -> bytes
    async def synthesize_to_file(text, output_path) -> Path
```

**支持的音色**：
- `longxiaochun` - 女声（清新）
- `longwan` - 女声（温柔）
- `longxiaobai` - 男声
- 等多种音色

#### 2. `deepseek_service.py` 扩展 - 推荐生成

```python
class DeepSeekService:
    async def generate_recommendation(
        origin_info: Dict,
        destination_info: Dict,
        user_query: str
    ) -> Dict
```

**推荐逻辑**：
- 分析两地的地址、区域、坐标
- 理解用户查询意图
- 生成个性化推荐
- 使用 DeepSeek V4 Pro（高性能模型）

### API 更新

#### 新增端点：`GET /api/audio/{filename}`

用于获取生成的语音文件。

**示例**：
```
GET /api/audio/tts_20260531_160000_abc123.mp3
```

#### 更新端点：`POST /api/process-audio-with-location`

**新增返回字段**：
```json
{
  "recommendation": {
    "text": "推荐文本内容",
    "summary": "简短总结",
    "audio_file": "tts_*.mp3"
  },
  "logs": {
    "recommend_log": "recommend_*.json",
    "tts_audio": "tts_*.mp3"
  }
}
```

### 前端更新

#### 新增功能

1. **语音播放器**：自动播放推荐语音
2. **推荐显示**：在结果中显示推荐文本
3. **自动播放**：语音合成完成后自动播放

#### UI 组件

```jsx
{recommendationAudio && (
  <div className="audio-player">
    <p>🔊 语音推荐</p>
    <audio controls src={recommendationAudio} autoPlay>
      您的浏览器不支持音频播放
    </audio>
  </div>
)}
```

## 🎯 使用示例

### 示例 1：中间地点推荐

**用户录音**：
```
"我朋友在北京南站，我在望京，请帮我推荐一个中间一点的吃饭的地方"
```

**系统输出**：
```
📝 识别结果：
我朋友在北京南站，我在望京，请帮我推荐一个中间一点的吃饭的地方

📍 地址提取：
起点: 北京南站
终点: 望京

🗺️ 地理编码：
起点坐标: (116.378577, 39.865494)
终点坐标: (116.470806, 40.006463)

💡 智能推荐：
根据您和朋友的位置，建议选择三元桥或亮马桥附近的餐厅。
这两个地方位于南站和望京的中间位置，交通便利。
推荐三元桥凤凰汇或亮马桥燕莎友谊商城，都有丰富的餐饮选择。
乘坐地铁10号线从北京南站到三元桥约30分钟，从望京到三元桥约15分钟。

🔊 点击下方播放语音推荐
```

**语音播放**：自动播放上述推荐内容

### 示例 2：路线查询

**用户录音**：
```
"从上海东方明珠到外滩怎么走"
```

**系统输出**：
```
💡 智能推荐：
从东方明珠到外滩距离很近，大约1.5公里。
建议步行15分钟即可到达，沿着滨江步道走风景很好。
如果不想走路，可以打车5分钟，或者乘坐观光巴士。
沿途可以欣赏黄浦江两岸的美景，是游客的必走路线。

🔊 点击下方播放语音推荐
```

## 📊 日志文件

### 新增日志类型

#### 1. 推荐日志 - `recommend_*.json`

```json
{
  "recommendation": "推荐文本",
  "summary": "简短总结",
  "model": "deepseek-v4-pro",
  "usage": {
    "prompt_tokens": 200,
    "completion_tokens": 150,
    "total_tokens": 350
  }
}
```

#### 2. TTS 音频 - `tts_*.mp3`

生成的语音文件，可以通过以下方式访问：
- API：`GET /api/audio/tts_*.mp3`
- 本地：`backend/Storage/tts_*.mp3`

## 🎨 配置说明

### TTS 音色配置

在 `main.py` 中可以配置 TTS 音色：

```python
await tts_service.synthesize_to_file(
    text=recommend_text,
    output_path=audio_path,
    voice="longxiaochun"  # 可配置音色
)
```

**可选音色**：
- `longxiaochun` - 女声，清新自然（推荐）
- `longwan` - 女声，温柔亲切
- `longxiaobai` - 男声，稳重大方

### 推荐生成配置

在 `deepseek_service.py` 中可以调整：

```python
temperature=0.7  # 控制创造性（0-1）
max_tokens=500   # 最大生成长度
```

## 🚀 启动指南

### 1. 确保依赖已安装

所有依赖已在 `requirements.txt` 中，无需额外安装。

### 2. 确认配置

检查 `.env` 文件：
```env
# 百炼配置（ASR + TTS）
BAILIAN_API_KEY=sk-xxxxx

# DeepSeek 配置
DEEPSEEK_API_KEY=sk-xxxxx

# 高德地图配置
AMAP_MAPS_API_KEY=xxxxx
```

### 3. 重启服务

```bash
# 后端
cd backend
python main.py

# 前端（新终端）
cd frontend
npm run dev
```

### 4. 测试功能

打开 `http://localhost:5175`，录音说：
```
"我朋友在北京南站，我在望京，请帮我推荐一个中间一点的吃饭的地方"
```

应该会看到：
1. ✅ ASR 识别文本
2. ✅ 地址提取结果
3. ✅ 地理编码坐标
4. ✅ 智能推荐文本
5. ✅ 自动播放语音推荐

## 📈 成本估算

### DeepSeek API

- **地址提取**（V4 Flash）：~300 tokens = $0.00006
- **推荐生成**（V4 Pro）：~500 tokens = $0.00014
- **每次查询总计**：~$0.0002（约 0.0014 元）

### 百炼 TTS

根据阿里云百炼定价，具体费用请查看官网。

## 🎯 下一步优化建议

1. **添加地图展示**：在前端显示两个地点和推荐位置
2. **路线规划**：使用高德 MCP 的路线规划工具
3. **POI 搜索**：搜索附近的餐厅、咖啡厅等
4. **多轮对话**：支持用户追问和细化需求
5. **音色选择**：让用户选择喜欢的 TTS 音色
6. **缓存优化**：缓存常见地点的地理编码结果

## 📚 参考文档

- [DeepSeek API 文档](backend/docs/deepseek_api_guide.md)
- [MCP Client 文档](backend/docs/mcp_client_guide.md)
- [完整实施总结](IMPLEMENTATION_SUMMARY.md)

---

**更新时间**：2026年5月31日
**版本**：v2.0
