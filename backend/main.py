import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

import aiofiles
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from dotenv import load_dotenv

from services.bailian_asr import BaiLianASRService
from services.bailian_tts import BaiLianTTSService
from deepseek_service import DeepSeekService
from mcp_service import AmapMCPService
from logger_service import logger

# 加载环境变量（从 .env 文件）
load_dotenv()

app = FastAPI(title="Audio Helper API", version="1.0.0")

# 从 .env 文件读取配置（不从系统环境变量读取）
def get_env(key: str, default: str = "") -> str:
    """从 .env 文件读取配置"""
    return os.getenv(key, default)

HOST = get_env("HOST", "0.0.0.0")
PORT = int(get_env("PORT", "8007"))
STORAGE_PATH = Path(get_env("STORAGE_PATH", "Storage"))
FRONTEND_URL = get_env("FRONTEND_URL", "http://localhost:5175")

# 百炼配置
BAILIAN_API_KEY = get_env("BAILIAN_API_KEY")
BAILIAN_REGION = get_env("BAILIAN_REGION", "beijing")

# 创建存储目录
STORAGE_PATH.mkdir(exist_ok=True)

# 初始化服务
asr_service = None
tts_service = None
if BAILIAN_API_KEY and BAILIAN_API_KEY != "your_bailian_api_key_here":
    asr_service = BaiLianASRService(api_key=BAILIAN_API_KEY, region=BAILIAN_REGION)
    tts_service = BaiLianTTSService(api_key=BAILIAN_API_KEY, region=BAILIAN_REGION)
    logger.success(f"百炼 ASR/TTS 服务已初始化（地域: {BAILIAN_REGION}）")
else:
    logger.warning("未配置百炼 API Key，ASR/TTS 功能将不可用")

# 初始化 DeepSeek 服务
deepseek_service = DeepSeekService()

# 初始化高德 MCP 服务
amap_mcp_service = AmapMCPService()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5175"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {
        "service": "Audio Helper API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "storage_path": str(STORAGE_PATH.absolute()),
        "storage_exists": STORAGE_PATH.exists(),
        "services": {
            "asr": asr_service is not None,
            "tts": tts_service is not None,
            "deepseek": deepseek_service.is_available() if deepseek_service else False,
            "amap_mcp": amap_mcp_service.mcp_enabled if amap_mcp_service else False
        }
    }


@app.get("/api/audio/{filename}")
async def get_audio(filename: str):
    """
    获取生成的音频文件
    """
    file_path = STORAGE_PATH / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    # 根据文件扩展名设置 MIME 类型
    mime_types = {
        ".mp3": "audio/mpeg",
        ".wav": "audio/wav",
        ".webm": "audio/webm",
        ".ogg": "audio/ogg"
    }
    
    extension = file_path.suffix.lower()
    media_type = mime_types.get(extension, "audio/mpeg")
    
    return FileResponse(
        path=file_path,
        media_type=media_type,
        filename=filename
    )


@app.post("/api/process-audio")
async def process_audio(audio: UploadFile = File(...)):
    try:
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 检查 ASR 服务是否可用
        if not asr_service:
            raise HTTPException(
                status_code=500,
                detail="ASR service not available. Please configure BAILIAN_API_KEY in .env file"
            )
        
        # 1. 保存上传的音频文件
        file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"audio_{timestamp}_{unique_id}.{file_extension}"
        
        file_path = STORAGE_PATH / filename
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await audio.read()
            await f.write(content)
        
        logger.success(f"音频已保存: {filename}")
        logger.info(f"文件大小: {len(content)} bytes, 类型: {audio.content_type}")
        
        # 2. 调用百炼 ASR 进行语音识别
        mime_type_map = {
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_type_map.get(file_extension, "audio/webm")
        
        logger.step("ASR识别", "开始语音识别...")
        asr_result = await asr_service.recognize(
            audio_path=file_path,
            mime_type=mime_type
        )
        logger.success(f"ASR 识别完成: {asr_result['text'][:50]}...")
        
        # 3. 保存 ASR 识别结果
        result_filename = f"asr_{timestamp}_{unique_id}.json"
        result_path = STORAGE_PATH / result_filename
        asr_service.save_result(asr_result, result_path)
        
        # 4. 返回结果
        return JSONResponse(
            status_code=200,
            content={
                "message": "Audio processed successfully",
                "audio_file": {
                    "filename": filename,
                    "path": str(file_path),
                    "size": len(content),
                    "content_type": audio.content_type
                },
                "asr_result": {
                    "text": asr_result["text"],
                    "result_file": result_filename,
                    "result_path": str(result_path)
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("处理音频时出错", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process audio: {str(e)}")


@app.post("/api/process-audio-with-location")
async def process_audio_with_location(audio: UploadFile = File(...)):
    """
    完整流程：ASR识别 → DeepSeek地址提取 → 高德MCP查询
    """
    request_id = str(uuid.uuid4())[:8]
    
    try:
        logger.info(f"========== 开始处理请求 [{request_id}] ==========")
        
        if not audio.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # 检查 ASR 服务
        if not asr_service:
            raise HTTPException(
                status_code=500,
                detail="ASR service not available"
            )
        
        # ========== 1. 保存音频文件 ==========
        file_extension = audio.filename.split(".")[-1] if "." in audio.filename else "webm"
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"audio_{timestamp}_{unique_id}.{file_extension}"
        file_path = STORAGE_PATH / filename
        
        async with aiofiles.open(file_path, "wb") as f:
            content = await audio.read()
            await f.write(content)
        
        logger.success(f"音频已保存: {filename}")
        
        # ========== 2. ASR 语音识别 ==========
        mime_type_map = {
            "webm": "audio/webm",
            "mp3": "audio/mpeg",
            "wav": "audio/wav",
            "ogg": "audio/ogg",
            "m4a": "audio/mp4"
        }
        mime_type = mime_type_map.get(file_extension, "audio/webm")
        
        logger.step("ASR识别", "开始语音识别...")
        asr_result = await asr_service.recognize(
            audio_path=file_path,
            mime_type=mime_type
        )
        asr_text = asr_result.get("text", "")
        logger.success(f"ASR 识别完成: {asr_text[:50]}...")
        
        # 保存 ASR 结果
        asr_filename = f"asr_{timestamp}_{unique_id}.json"
        asr_path = STORAGE_PATH / asr_filename
        asr_service.save_result(asr_result, asr_path)
        
        # ========== 3. DeepSeek 地址提取 ==========
        addresses = None
        if deepseek_service.is_available() and asr_text:
            logger.step("地址提取", "调用 DeepSeek 提取地址...")
            addresses = await deepseek_service.extract_addresses(asr_text)
            
            # 保存 DeepSeek 结果
            deepseek_filename = f"deepseek_{timestamp}_{unique_id}.json"
            await logger.save_log_file(STORAGE_PATH, deepseek_filename, addresses)
        else:
            logger.warning("DeepSeek 服务不可用或无识别文本，跳过地址提取")
        
        # ========== 4. 高德 MCP 地理编码 ==========
        location_results = {}
        
        if addresses and (addresses.get("origin") or addresses.get("destination")):
            # 连接 MCP 服务
            mcp_connected = await amap_mcp_service.connect(request_id)
            
            if mcp_connected:
                # 查询起点
                if addresses.get("origin"):
                    logger.step("MCP查询", f"查询起点: {addresses['origin']}")
                    origin_geo = await amap_mcp_service.geocode(addresses["origin"])
                    if origin_geo:
                        location_results["origin"] = origin_geo
                        logger.success(f"起点经纬度: ({origin_geo['lng']}, {origin_geo['lat']})")
                
                # 查询终点
                if addresses.get("destination"):
                    logger.step("MCP查询", f"查询终点: {addresses['destination']}")
                    destination_geo = await amap_mcp_service.geocode(addresses["destination"])
                    if destination_geo:
                        location_results["destination"] = destination_geo
                        logger.success(f"终点经纬度: ({destination_geo['lng']}, {destination_geo['lat']})")
                
                # 保存 MCP 调用链日志
                await amap_mcp_service.save_call_log(STORAGE_PATH, request_id)
                
                # 关闭 MCP 连接
                await amap_mcp_service.close()
            else:
                logger.warning("MCP 连接失败，跳过地理编码")
        else:
            logger.info("未提取到地址信息，跳过地理编码")
        
        # ========== 5. DeepSeek 生成推荐 ==========
        recommendation = None
        if location_results.get("origin") and location_results.get("destination"):
            if deepseek_service.is_available():
                logger.step("推荐生成", "调用 DeepSeek 生成推荐...")
                recommendation = await deepseek_service.generate_recommendation(
                    origin_info=location_results["origin"],
                    destination_info=location_results["destination"],
                    user_query=asr_text
                )
                
                # 保存推荐结果
                recommend_filename = f"recommend_{timestamp}_{unique_id}.json"
                await logger.save_log_file(STORAGE_PATH, recommend_filename, recommendation)
            else:
                logger.warning("DeepSeek 服务不可用，跳过推荐生成")
        
        # ========== 6. TTS 语音合成 ==========
        audio_response_file = None
        if recommendation and tts_service:
            try:
                logger.step("TTS合成", "生成语音推荐...")
                
                recommend_text = recommendation.get("recommendation", "")
                if recommend_text:
                    audio_filename = f"tts_{timestamp}_{unique_id}.mp3"
                    audio_path = STORAGE_PATH / audio_filename
                    
                    await tts_service.synthesize_to_file(
                        text=recommend_text,
                        output_path=audio_path,
                        voice="longxiaochun"  # 可配置音色
                    )
                    
                    audio_response_file = audio_filename
                    logger.success(f"语音合成完成: {audio_filename}")
            except Exception as e:
                logger.error("TTS 合成失败", e)
        
        # ========== 7. 返回完整结果 ==========
        logger.success(f"请求处理完成 [{request_id}]")
        
        return JSONResponse(
            status_code=200,
            content={
                "request_id": request_id,
                "message": "Audio processed with location successfully",
                "audio_file": {
                    "filename": filename,
                    "size": len(content)
                },
                "asr_result": {
                    "text": asr_text,
                    "result_file": asr_filename
                },
                "addresses": addresses or {},
                "locations": location_results,
                "recommendation": {
                    "text": recommendation.get("recommendation") if recommendation else None,
                    "summary": recommendation.get("summary") if recommendation else None,
                    "audio_file": audio_response_file
                } if recommendation else None,
                "logs": {
                    "asr_log": asr_filename,
                    "deepseek_log": f"deepseek_{timestamp}_{unique_id}.json" if addresses else None,
                    "mcp_log": f"mcp_call_{request_id}.json" if location_results else None,
                    "recommend_log": f"recommend_{timestamp}_{unique_id}.json" if recommendation else None,
                    "tts_audio": audio_response_file
                }
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"处理请求失败 [{request_id}]", e)
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    logger.info("========================================")
    logger.info("🚀 启动 Audio Helper API 服务")
    logger.info(f"   地址: http://{HOST}:{PORT}")
    logger.info(f"   存储路径: {STORAGE_PATH.absolute()}")
    logger.info("========================================")
    uvicorn.run(app, host=HOST, port=PORT)
