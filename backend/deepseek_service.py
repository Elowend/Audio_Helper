"""
DeepSeek 服务
包含：
1. 地址提取 - 从 ASR 文本中提取地址信息
2. 推荐生成 - 基于地理信息生成推荐内容
"""
import json
import os
from typing import Dict, Optional, List
from openai import OpenAI
from logger_service import logger


class DeepSeekService:
    """DeepSeek 服务类"""
    
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
        self.extract_model = "deepseek-v4-flash"  # 快速模型，适合地址提取
        self.recommend_model = "deepseek-v4-pro"  # 高性能模型，适合推荐生成
        
        if not self.api_key or self.api_key == "your_deepseek_api_key_here":
            logger.warning("DeepSeek API Key 未配置")
            self.client = None
        else:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.success("DeepSeek 服务初始化成功")
    
    def is_available(self) -> bool:
        """检查服务是否可用"""
        return self.client is not None
    
    async def extract_addresses(self, text: str) -> Dict[str, Optional[str]]:
        """
        从文本中提取起点和终点地址
        
        Args:
            text: ASR 识别的文本
            
        Returns:
            {
                "origin": "起点地址",
                "destination": "终点地址",
                "raw_text": "原始文本"
            }
        """
        if not self.is_available():
            logger.error("DeepSeek 服务不可用")
            return {
                "origin": None,
                "destination": None,
                "raw_text": text,
                "error": "DeepSeek API Key 未配置"
            }
        
        logger.step("地址提取", f"开始分析文本: {text[:50]}...")
        
        system_prompt = """你是一个专业的地址提取助手。
从用户的语音输入中，提取两个地址信息：起点（origin）和终点（destination）。

规则：
1. 必须返回 JSON 格式
2. 如果只有一个地址，终点为 null
3. 如果没有明确的地址信息，两个都为 null
4. 提取完整的地址名称，包括城市信息
5. 识别常见表达：从...到...、去...、在...等

返回格式示例：
{
  "origin": "北京天安门",
  "destination": "北京故宫"
}

或

{
  "origin": null,
  "destination": "上海东方明珠"
}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.extract_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,  # 低温度保证稳定输出
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            
            origin = result.get("origin")
            destination = result.get("destination")
            
            logger.success(f"地址提取完成 - 起点: {origin}, 终点: {destination}")
            
            # 记录 token 使用情况
            usage = response.usage
            logger.info(f"Token 使用: 输入={usage.prompt_tokens}, 输出={usage.completion_tokens}, 总计={usage.total_tokens}")
            
            return {
                "origin": origin,
                "destination": destination,
                "raw_text": text,
                "model": self.extract_model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            }
            
        except json.JSONDecodeError as e:
            logger.error("解析 DeepSeek 返回的 JSON 失败", e)
            return {
                "origin": None,
                "destination": None,
                "raw_text": text,
                "error": f"JSON 解析失败: {str(e)}"
            }
            
        except Exception as e:
            logger.error("DeepSeek API 调用失败", e)
            return {
                "origin": None,
                "destination": None,
                "raw_text": text,
                "error": str(e)
            }
    
    async def generate_recommendation(
        self,
        origin_info: Dict,
        destination_info: Dict,
        user_query: str
    ) -> Dict[str, str]:
        """
        基于两个地点的信息生成推荐
        
        Args:
            origin_info: 起点信息（包含地址、经纬度等）
            destination_info: 终点信息（包含地址、经纬度等）
            user_query: 用户原始查询
            
        Returns:
            {
                "recommendation": "推荐文本",
                "summary": "简短总结"
            }
        """
        if not self.is_available():
            logger.error("DeepSeek 服务不可用")
            return {
                "recommendation": "抱歉，推荐服务暂时不可用。",
                "summary": "服务不可用",
                "error": "DeepSeek API Key 未配置"
            }
        
        logger.step("推荐生成", "分析地理信息并生成推荐...")
        
        # 构建上下文信息
        origin_addr = origin_info.get("formatted_address") or origin_info.get("address", "未知地点")
        dest_addr = destination_info.get("formatted_address") or destination_info.get("address", "未知地点")
        
        origin_district = origin_info.get("raw", {}).get("district", "")
        dest_district = destination_info.get("raw", {}).get("district", "")
        
        system_prompt = """你是一个专业的地点推荐助手。
基于用户提供的两个地点信息，为用户提供实用的推荐建议。

要求：
1. 推荐内容要具体、实用
2. 如果用户询问中间地点（如餐厅、咖啡厅），推荐两地之间的区域
3. 如果用户询问路线，简要说明交通方式
4. 语气要友好、自然
5. 控制在 100-200 字以内"""
        
        user_message = f"""用户查询：{user_query}

起点信息：
- 地址：{origin_addr}
- 区域：{origin_district}
- 坐标：({origin_info.get('lng')}, {origin_info.get('lat')})

终点信息：
- 地址：{dest_addr}
- 区域：{dest_district}
- 坐标：({destination_info.get('lng')}, {destination_info.get('lat')})

请基于以上信息，为用户提供合适的推荐。"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.recommend_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.7,  # 适中温度，保持创造性
                max_tokens=500
            )
            
            recommendation = response.choices[0].message.content
            
            # 生成简短总结（前50个字符）
            summary = recommendation[:50] + "..." if len(recommendation) > 50 else recommendation
            
            logger.success(f"推荐生成完成 - {summary}")
            
            # 记录 token 使用情况
            usage = response.usage
            logger.info(f"Token 使用: 输入={usage.prompt_tokens}, 输出={usage.completion_tokens}, 总计={usage.total_tokens}")
            
            return {
                "recommendation": recommendation,
                "summary": summary,
                "model": self.recommend_model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens,
                    "completion_tokens": usage.completion_tokens,
                    "total_tokens": usage.total_tokens
                }
            }
            
        except Exception as e:
            logger.error("DeepSeek 推荐生成失败", e)
            return {
                "recommendation": f"根据您的位置，从{origin_addr}到{dest_addr}，建议您选择两地之间的中心区域。",
                "summary": "推荐生成失败，使用默认建议",
                "error": str(e)
            }
