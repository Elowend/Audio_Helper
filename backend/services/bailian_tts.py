"""
阿里云百炼 TTS 服务
使用 WebSocket 调用 CosyVoice TTS 模型
"""
import os
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

import websockets


class BaiLianTTSService:
    """百炼 TTS 服务（WebSocket）"""
    
    def __init__(self, api_key: str, region: str = "beijing"):
        self.api_key = api_key
        self.region = region
        
        self._clear_proxy_env()
        
        if region == "singapore":
            self.ws_url = "wss://dashscope-intl.aliyuncs.com/api-ws/v1/inference"
        else:
            self.ws_url = "wss://dashscope.aliyuncs.com/api-ws/v1/inference"
    
    @staticmethod
    def _clear_proxy_env():
        """清除所有代理环境变量"""
        proxy_vars = [
            'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
            'ALL_PROXY', 'all_proxy', 'NO_PROXY', 'no_proxy'
        ]
        for var in proxy_vars:
            os.environ.pop(var, None)
    
    async def synthesize(
        self,
        text: str,
        model: str = "cosyvoice-v1",
        voice: str = "longxiaochun",
        format: str = "mp3",
        sample_rate: int = 22050
    ) -> bytes:
        """
        调用百炼 TTS 服务合成语音（WebSocket）
        
        Args:
            text: 要合成的文本
            model: TTS 模型名称
            voice: 音色（longxiaochun, longwan, longxiaobai 等）
            format: 音频格式（mp3, wav, pcm）
            sample_rate: 采样率
            
        Returns:
            音频数据（字节）
        """
        print(f"🎵 调用百炼 TTS API (WebSocket):")
        print(f"   URL: {self.ws_url}")
        print(f"   模型: {model}")
        print(f"   音色: {voice}")
        print(f"   文本长度: {len(text)} 字符")
        
        task_id = str(uuid.uuid4()).replace("-", "")
        audio_chunks = []
        
        try:
            # 创建 WebSocket 连接
            async with websockets.connect(
                self.ws_url,
                additional_headers={
                    "Authorization": f"Bearer {self.api_key}"
                },
                ping_interval=None
            ) as websocket:
                # 1. 发送 run-task 指令（启动任务）
                run_task = {
                    "header": {
                        "action": "run-task",
                        "streaming": "duplex",
                        "task_id": task_id
                    },
                    "payload": {
                        "task_group": "audio",
                        "task": "tts",
                        "function": "SpeechSynthesizer",
                        "model": model,
                        "parameters": {
                            "text_type": "PlainText",
                            "voice": voice,
                            "format": format,
                            "sample_rate": sample_rate,
                            "volume": 50,
                            "rate": 1.0,
                            "pitch": 1.0
                        },
                        "input": {}  # 必须包含空的 input 对象
                    }
                }
                
                run_task_json = json.dumps(run_task, ensure_ascii=False)
                print(f"   📤 发送 run-task 指令:")
                print(f"   {run_task_json[:200]}...")
                await websocket.send(run_task_json)
                print("   ✅ 已发送 run-task 指令")
                
                # 等待 task-started 事件
                task_started = False
                while not task_started:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    if isinstance(message, str):
                        data = json.loads(message)
                        event = data.get("header", {}).get("event")
                        print(f"   📨 收到事件: {event}")
                        
                        if event == "task-started":
                            task_started = True
                            print("   ✅ 收到 task-started 事件")
                        elif event == "task-failed":
                            error_msg = data.get("header", {}).get("error_message", "Unknown error")
                            error_code = data.get("header", {}).get("error_code", "")
                            print(f"   ❌ 收到 task-failed 事件: [{error_code}] {error_msg}")
                            print(f"   完整错误信息: {json.dumps(data, ensure_ascii=False)}")
                            raise Exception(f"TTS synthesis failed at run-task: [{error_code}] {error_msg}")
                
                # 2. 发送 continue-task 指令（发送文本）
                continue_task = {
                    "header": {
                        "action": "continue-task",
                        "streaming": "duplex",
                        "task_id": task_id
                    },
                    "payload": {
                        "input": {
                            "text": text
                        }
                    }
                }
                
                continue_task_json = json.dumps(continue_task, ensure_ascii=False)
                print(f"   📤 发送 continue-task 指令")
                await websocket.send(continue_task_json)
                print("   ✅ 已发送 continue-task 指令（文本）")
                
                # 3. 发送 finish-task 指令（结束任务）
                finish_task = {
                    "header": {
                        "action": "finish-task",
                        "streaming": "duplex",
                        "task_id": task_id
                    },
                    "payload": {
                        "input": {}
                    }
                }
                
                finish_task_json = json.dumps(finish_task, ensure_ascii=False)
                print(f"   📤 发送 finish-task 指令")
                await websocket.send(finish_task_json)
                print("   ✅ 已发送 finish-task 指令")
                
                # 4. 接收响应和音频数据
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                        
                        # 解析消息
                        if isinstance(message, bytes):
                            # 二进制音频数据
                            audio_chunks.append(message)
                            print(f"   📦 收到音频数据块: {len(message)} bytes")
                        else:
                            # JSON 消息（事件）
                            data = json.loads(message)
                            event = data.get("header", {}).get("event")
                            
                            if event == "result-generated":
                                print("   ✅ 收到 result-generated 事件")
                            
                            elif event == "task-finished":
                                print(f"   ✅ 收到 task-finished 事件")
                                print(f"✅ TTS 合成成功")
                                break
                            
                            elif event == "task-failed":
                                error_msg = data.get("header", {}).get("error_message", "Unknown error")
                                error_code = data.get("header", {}).get("error_code", "")
                                raise Exception(f"TTS synthesis failed: [{error_code}] {error_msg}")
                    
                    except asyncio.TimeoutError:
                        print("⚠️  WebSocket 接收超时，可能已完成")
                        break
            
            # 合并音频数据
            if audio_chunks:
                audio_bytes = b"".join(audio_chunks)
                print(f"   音频大小: {len(audio_bytes)} bytes")
                return audio_bytes
            else:
                raise Exception("未收到音频数据")
        
        except Exception as e:
            print(f"❌ TTS API 调用失败: {str(e)}")
            raise
    
    async def synthesize_to_file(
        self,
        text: str,
        output_path: Path,
        model: str = "cosyvoice-v1",
        voice: str = "longxiaochun",
        format: str = "mp3"
    ) -> Path:
        """
        合成语音并保存到文件
        
        Args:
            text: 要合成的文本
            output_path: 输出文件路径
            model: TTS 模型名称
            voice: 音色
            format: 音频格式
            
        Returns:
            输出文件路径
        """
        audio_bytes = await self.synthesize(
            text=text,
            model=model,
            voice=voice,
            format=format
        )
        
        output_path.write_bytes(audio_bytes)
        print(f"💾 语音已保存: {output_path}")
        
        return output_path
