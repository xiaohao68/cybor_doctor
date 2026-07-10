'''知识图谱查询接口 - 用于查询实体之间的关系'''
from env import get_env_value                                      # 环境变量获取
import requests                                                   # HTTP请求库


def query_knowledge_graph(question: str) -> str:
    """
    查询知识图谱获取实体关系
    
    流程：
    1. 从环境变量获取知识图谱服务地址
    2. 构建查询请求
    3. 发送HTTP请求获取实体关系信息
    4. 解析并返回结果
    
    参数:
        question: 用户问题（用于提取实体）
    
    返回:
        str: 知识图谱查询结果（实体关系描述）
    """
    # 获取知识图谱服务地址
    graph_url = get_env_value("KNOWLEDGE_GRAPH_URL")
    
    if not graph_url:
        return "知识图谱服务未配置"
    
    try:
        # 构建查询参数
        payload = {
            "question": question,
            "limit": 5  # 返回最多5条关系
        }
        
        # 发送POST请求
        response = requests.post(
            graph_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            # 处理返回结果
            if data.get("success"):
                relations = data.get("relations", [])
                if relations:
                    # 格式化关系信息
                    result = "\n".join([
                        f"- {rel['subject']} {rel['predicate']} {rel['object']}"
                        for rel in relations
                    ])
                    return f"从知识图谱中查询到以下关系：\n{result}"
                else:
                    return "知识图谱中未找到相关实体关系"
            else:
                return f"查询失败：{data.get('message', '未知错误')}"
        else:
            return f"请求失败，状态码：{response.status_code}"
    except Exception as e:
        return f"查询知识图谱时发生错误：{str(e)}"


def extract_entities(question: str) -> list:
    """
    从问题中提取实体
    
    参数:
        question: 用户问题文本
    
    返回:
        list: 提取出的实体列表
    """
    # 获取实体提取服务地址
    extract_url = get_env_value("ENTITY_EXTRACT_URL")
    
    if not extract_url:
        return []
    
    try:
        payload = {"text": question}
        response = requests.post(
            extract_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data.get("entities", [])
        return []
    except Exception as e:
        print(f"实体提取失败：{str(e)}")
        return []