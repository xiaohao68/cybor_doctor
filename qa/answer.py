'''根据问答类型选择对应的工具函数进行处理'''
from typing import Tuple, List, Any

from qa.function_tool import route_intent     # 导入函数映射工具
from qa.purpose_type import intent_type                # 导入意图类型枚举


def fetch_answer(
    question: str, history: List[List | None] = None, question_type=None, image_url=None
) -> Tuple[Any, intent_type]:
    """
    根据问题类型调用对应的函数获取结果
    
    参数:
        question: 用户输入的问题文本
        history: 对话历史记录（列表形式，每个元素是[用户输入, 机器人回复]）
        question_type: 问题类型（通过detect_intent解析得到）
        image_url: 图片URL列表（用于图片相关任务）
    
    返回:
        Tuple[Any, intent_type]: (处理结果, 问题类型)
    """

    # 根据问题类型获取对应的处理函数
    function = route_intent(question_type)

    # 构建函数参数列表
    args = [question_type, question, history, image_url]
    # 调用处理函数并获取结果
    result = function(*args)

    return result
