"""
阿里云百炼 ASR 服务
使用 HTTP 请求调用 Qwen-ASR-Flash 模型
"""
import os
import base64
import json
from pathlib import Path
from typing import Dict, Any, Optional

import httpx


class BaiLianASRService:
    """百炼 ASR 服务"""
    
    def __init__(self, api_key: str, region: str = "beijing"):
        self.api_key = api_key
        self.region = region
        
        self._clear_proxy_env()
        
        if region == "singapore":
            self.base_url = "https://dashscope-intl.aliyuncs.com"
        else:
            self.base_url = "https://dashscope.aliyuncs.com"
        
        self.asr_url = f"{self.base_url}/compatible-mode/v1/chat/completions"
    
    @staticmethod
    def _clear_proxy_env():
        """清除所有代理环境变量"""
        proxy_vars = [
            'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
            'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
        ]
        for var in proxy_vars:
            os.environ.pop(var, None)
        
        print("✅ 已清除所有代理环境变量")
    
    def encode_audio_to_base64(self, audio_path: Path, mime_type: str = "audio/webm") -> str:
        """
        将音频文件编码为 Base64 Data URI
        
        Args:
            audio_path: 音频文件路径
            mime_type: MIME 类型
            
        Returns:
            Data URI 字符串
        """
        audio_bytes = audio_path.read_bytes()
        base64_str = base64.b64encode(audio_bytes).decode('utf-8')
        data_uri = f"data:{mime_type};base64,{base64_str}"
        
        print(f"📝 音频编码完成:")
        print(f"   原始大小: {len(audio_bytes)} bytes")
        print(f"   Base64 大小: {len(base64_str)} bytes")
        
        return data_uri
    
    async def recognize(
        self,
        audio_path: Path,
        mime_type: str = "audio/webm",
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        调用百炼 ASR 服务识别音频
        
        Args:
            audio_path: 音频文件路径
            mime_type: 音频 MIME 类型
            stream: 是否流式返回
            
        Returns:
            识别结果字典，包含:
                - text: 识别的文本
                - raw_response: 原始 API 响应
        """
        data_uri = self.encode_audio_to_base64(audio_path, mime_type)
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen3-asr-flash",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_uri
                            }
                        }
                    ]
                }
            ],
            "stream": stream
        }
        
        print(f"🚀 调用百炼 ASR API:")
        print(f"   URL: {self.asr_url}")
        print(f"   模型: qwen3-asr-flash")
        print(f"   流式: {stream}")
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.asr_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code != 200:
                error_detail = response.text
                print(f"❌ ASR API 调用失败:")
                print(f"   状态码: {response.status_code}")
                print(f"   响应: {error_detail}")
                raise Exception(f"ASR API error: {response.status_code} - {error_detail}")
            
            result = response.json()
        
        print(f"✅ ASR 识别成功")
        
        recognized_text = result["choices"][0]["message"]["content"]
        
        print(f"📄 识别结果: {recognized_text}")
        
        return {
            "text": recognized_text,
            "raw_response": result
        }
    
    def save_result(self, result: Dict[str, Any], output_path: Path):
        """
        保存 ASR 识别结果到文件
        
        Args:
            result: 识别结果
            output_path: 输出文件路径
        """
        output_path.write_text(
            json.dumps(result, ensure_ascii=False, indent=2),
            encoding='utf-8'
        )
        print(f"💾 ASR 结果已保存: {output_path}")
