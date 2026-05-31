# DeepSeek API 开发指南

## 概述

DeepSeek API 使用与 OpenAI/Anthropic 兼容的 API 格式，可以使用 OpenAI SDK 直接访问。

## 基本配置

| 参数 | 值 |
| --- | --- |
| base_url | `https://api.deepseek.com` |
| api_key | 从官网申请 API key |
| model | `deepseek-v4-flash` (快速) / `deepseek-v4-pro` (高性能) |

## Python 调用示例

### 1. 安装依赖

```bash
pip install openai
```

### 2. 基本调用

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_DEEPSEEK_API_KEY",
    base_url="https://api.deepseek.com"
)

response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    stream=False
)

print(response.choices[0].message.content)
```

### 3. 带思考模式的调用

```python
response = client.chat.completions.create(
    model="deepseek-v4-pro",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "复杂的推理问题"}
    ],
    thinking={"type": "enabled"},
    reasoning_effort="high",  # 或 "max"
    stream=False
)
```

## 地址提取最佳实践

### System Prompt 示例

```python
system_prompt = """你是一个地址提取助手。
从用户的语音输入中，提取两个地址信息：起点和终点。

要求：
1. 返回 JSON 格式
2. 如果只有一个地址，终点为空
3. 如果没有地址信息，返回 null

返回格式：
{
  "origin": "起点地址",
  "destination": "终点地址"
}
"""
```

### 调用示例

```python
response = client.chat.completions.create(
    model="deepseek-v4-flash",
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "我想从北京天安门到故宫"}
    ],
    temperature=0.3,  # 低温度保证稳定输出
    response_format={"type": "json_object"}
)

result = json.loads(response.choices[0].message.content)
```

## 注意事项

1. **API Key 安全**：使用环境变量存储，不要硬编码
2. **错误处理**：实现重试机制和超时处理
3. **速率限制**：注意 API 调用频率限制
4. **成本控制**：记录 token 使用量
5. **模型选择**：
   - `deepseek-v4-flash`：快速、便宜，适合简单任务
   - `deepseek-v4-pro`：高性能，适合复杂推理

## 价格（2026年5月）

- Input tokens: $0.14 / 1M tokens
- Output tokens: $0.28 / 1M tokens

## 参考链接

- 官方文档：https://api-docs.deepseek.com/zh-cn/
- API 申请：https://platform.deepseek.com/
