"""
服务测试脚本
用于验证各个服务是否正确配置和运行
"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

from deepseek_service import DeepSeekService
from mcp_service import AmapMCPService
from logger_service import logger

STORAGE_PATH = Path(os.getenv("STORAGE_PATH", "Storage"))


async def test_deepseek():
    """测试 DeepSeek 服务"""
    logger.info("========== 测试 DeepSeek 服务 ==========")
    
    service = DeepSeekService()
    
    if not service.is_available():
        logger.error("DeepSeek 服务不可用，请检查配置")
        return False
    
    # 测试地址提取
    test_text = "我想从北京天安门到故宫"
    logger.info(f"测试文本: {test_text}")
    
    result = await service.extract_addresses(test_text)
    
    if result.get("origin") and result.get("destination"):
        logger.success("DeepSeek 服务测试通过 ✓")
        logger.info(f"起点: {result['origin']}")
        logger.info(f"终点: {result['destination']}")
        return True
    else:
        logger.error("DeepSeek 地址提取失败")
        return False


async def test_amap_mcp():
    """测试高德 MCP 服务"""
    logger.info("========== 测试高德 MCP 服务 ==========")
    
    service = AmapMCPService()
    
    if not service.mcp_enabled or not service.mcp_url:
        logger.error("高德 MCP 未启用或 URL 未配置")
        return False
    
    # 连接 MCP
    request_id = "test_001"
    connected = await service.connect(request_id)
    
    if not connected:
        logger.error("MCP 连接失败")
        return False
    
    # 测试地理编码
    logger.info("测试地理编码...")
    result = await service.geocode("天安门", "北京")
    
    if result:
        logger.success("高德 MCP 服务测试通过 ✓")
        logger.info(f"经纬度: ({result['lng']}, {result['lat']})")
        logger.info(f"详细地址: {result.get('formatted_address', 'N/A')}")
        logger.info(f"数据来源: {'MCP' if result.get('via_mcp') else 'REST 回退'}")
        
        # 保存测试日志
        await service.save_call_log(STORAGE_PATH, request_id)
        
        # 关闭连接
        await service.close()
        return True
    else:
        logger.error("地理编码查询失败")
        await service.close()
        return False


async def test_full_flow():
    """测试完整流程"""
    logger.info("========== 测试完整流程 ==========")
    
    # 1. DeepSeek 地址提取
    deepseek = DeepSeekService()
    if not deepseek.is_available():
        logger.error("DeepSeek 服务不可用，跳过完整流程测试")
        return False
    
    test_text = "我在上海东方明珠，朋友在南京路步行街"
    logger.info(f"测试文本: {test_text}")
    
    addresses = await deepseek.extract_addresses(test_text)
    
    if not addresses.get("origin") and not addresses.get("destination"):
        logger.error("地址提取失败")
        return False
    
    logger.success(f"地址提取成功 - 起点: {addresses['origin']}, 终点: {addresses['destination']}")
    
    # 2. 高德 MCP 地理编码
    amap = AmapMCPService()
    
    if not amap.mcp_enabled or not amap.mcp_url:
        logger.warning("高德 MCP 未启用，跳过地理编码")
        return True
    
    request_id = "test_full_001"
    connected = await amap.connect(request_id)
    
    if not connected:
        logger.error("MCP 连接失败")
        return False
    
    # 查询起点
    if addresses.get("origin"):
        origin_geo = await amap.geocode(addresses["origin"], "上海")
        if origin_geo:
            logger.success(f"起点坐标: ({origin_geo['lng']}, {origin_geo['lat']})")
    
    # 查询终点
    if addresses.get("destination"):
        dest_geo = await amap.geocode(addresses["destination"], "上海")
        if dest_geo:
            logger.success(f"终点坐标: ({dest_geo['lng']}, {dest_geo['lat']})")
    
    # 保存日志
    await amap.save_call_log(STORAGE_PATH, request_id)
    await amap.close()
    
    logger.success("完整流程测试通过 ✓")
    return True


async def main():
    """主测试函数"""
    logger.info("========================================")
    logger.info("🧪 开始服务测试")
    logger.info("========================================")
    
    results = {
        "DeepSeek": False,
        "高德MCP": False,
        "完整流程": False
    }
    
    # 测试 DeepSeek
    try:
        results["DeepSeek"] = await test_deepseek()
    except Exception as e:
        logger.error("DeepSeek 测试异常", e)
    
    print()
    
    # 测试高德 MCP
    try:
        results["高德MCP"] = await test_amap_mcp()
    except Exception as e:
        logger.error("高德MCP 测试异常", e)
    
    print()
    
    # 测试完整流程
    try:
        results["完整流程"] = await test_full_flow()
    except Exception as e:
        logger.error("完整流程测试异常", e)
    
    # 输出测试结果
    print()
    logger.info("========================================")
    logger.info("📊 测试结果汇总")
    logger.info("========================================")
    
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        logger.info(f"{name}: {status}")
    
    all_passed = all(results.values())
    
    print()
    if all_passed:
        logger.success("🎉 所有测试通过！服务配置正确。")
    else:
        logger.warning("⚠️  部分测试失败，请检查配置。")
        logger.info("提示：查看 backend/docs/setup_guide.md 获取配置帮助")
    
    logger.info("========================================")


if __name__ == "__main__":
    asyncio.run(main())
