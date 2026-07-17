'''问答类型判断函数，根据特定输入和大模型进行分类。'''
from typing import List, Dict

from client.clientfactory import client_broker           # 导入客户端工厂

from qa.prompt_templates import build_classifier_prompt  # 导入问题解析提示词模板
from qa.purpose_type import intent_map                  # 导入意图映射字典
from qa.purpose_type import intent_type              # 导入意图类型枚举

from icecream import ic                                 # 调试工具


def detect_intent(question: str, image_url=None) -> intent_type:
    """
    解析用户问题的意图类型
    
    参数:
        question: 用户输入的问题文本
        image_url: 图片URL列表（如果有图片输入）
    
    返回:
        intent_type: 识别出的意图类型枚举值
    """

    # 规则5：有图片输入 → 图片描述
    if image_url is not None:
        return intent_map["图片描述"]

    # 规则1：检测"根据知识库"关键词 → 知识库检索
    if "根据知识库" in question:
        return intent_map["基于知识库"]
    
    # 规则2：检测"搜索"关键词 → 联网搜索
    if "搜索" in question:
        return intent_map["网络搜索"]
    
    # 规则3：检测Word生成相关关键词 → Word文档生成
    if ("word" in question or "Word" in question or "WORD" in question) and ("生成" in question or "制作" in question):
        return intent_map["Word生成"]
    
    # 规则4：检测PPT生成相关关键词 → PPT生成
    if ("ppt" in question or "PPT" in question) and ("生成" in question or "制作" in question):
        return intent_map["PPT生成"]
    

    # 规则6：使用大模型进行意图分类（处理复杂情况）
    prompt = build_classifier_prompt(question)           # 获取分类提示词
    response = client_broker().get_default().ask_model(prompt)  # 调用LLM进行分类
    ic("大模型分类结果：" + response)                      # 调试输出分类结果

    # 根据LLM返回结果映射到对应的意图类型
    if response == "图片生成" and len(question) > 0:
        return intent_map["图片生成"]
    if response == "视频生成" and len(question) > 0:
        return intent_map["视频生成"]
    if response == "PPT生成" and len(question) > 0:
        return intent_map["PPT生成"]
    if response == "Word生成" and len(question) > 0:
        return intent_map["Word生成"]
    if response == "音频生成" and len(question) > 0:
        return intent_map["音频生成"]
    if response == "文本生成":
        return intent_map["文本生成"]
    
    # 默认返回"其他"类型（文本生成）
    return intent_map["其他"]
