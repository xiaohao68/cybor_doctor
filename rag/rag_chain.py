# RAG检索链入口文件 - 用于调用不同类型的RAG检索接口
from rag.retrieve.retrieve_document import retrieve_docs       # 文档检索函数
from typing import List                                        # 类型提示
from openai import Stream                                      # 流式响应类型
from openai.types.chat import ChatCompletionChunk              # 聊天完成块类型
from client.clientfactory import Clientfactory                 # 客户端工厂


def invoke(question: str, history: List[List]) -> Stream[ChatCompletionChunk]:
    """
    RAG检索增强生成主入口
    
    流程：
    1. 使用问题检索知识库文档
    2. 将检索到的文档内容构建成prompt
    3. 调用LLM生成基于文档的回答
    
    参数:
        question: 用户问题文本
        history: 对话历史记录
    
    返回:
        Stream[ChatCompletionChunk]: LLM的流式响应
    """
    try:
        # 检索相关文档，获取文档对象和处理后的文本内容
        docs, _context = retrieve_docs(question)
    except Exception as e:
        # 检索失败时，上下文置空
        _context = ""

    # 构建带有检索内容的prompt
    prompt = f"请根据搜索到的文件信息\n{_context}\n 回答问题：\n{question}"
    
    # 调用LLM进行流式回答
    response = Clientfactory().get_client().chat_with_ai_stream(prompt)

    return response