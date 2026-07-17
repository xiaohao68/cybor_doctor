'''封装调用大模型代理的API接口的函数'''
from typing import List, Dict                                     # 类型提示

from openai.types.chat import ChatCompletion, ChatCompletionChunk  # OpenAI类型
from openai import Stream                                          # 流式响应类型

from client.LLMclientbase import llm_client_base                    # 基础客户端类
from overrides import override                                      # 方法重写装饰器


class llm_client_impl(llm_client_base):
    """
    LLM客户端通用实现
    
    继承自llm_client_base，实现具体的API调用方法
    """

    def __init__(self, *args, **kwargs):
        """初始化客户端，调用父类构造函数"""
        super().__init__()

    # 消息构造函数（提示词工程）
    @override
    def build_messages(
        self, prompt: str, history: List[List[str]] | None = None
    ) -> List[Dict[str, str]] | str | None:
        """
        构造对话消息列表
        
        将历史对话和当前输入组织成LLM期望的消息格式
        
        参数:
            prompt: 当前用户输入
            history: 对话历史记录
        
        返回:
            List[Dict[str, str]]: 消息列表
        """
        # 系统消息（定义AI角色）
        messages = [
            {
                "role": "system",
                "content": "你是一个乐于解答各种问题的助手，你的任务是为用户提供专业、准确、有见地的回答。",
            }
        ]

        # 添加历史对话
        for user_input, ai_response in history:
            messages.append({"role": "user", "content": user_input})
            messages.append({"role": "assistant", "content": ai_response.__repr__()})

        # 添加当前问题
        messages.append({"role": "user", "content": prompt})
        return messages

    # 直接消息对话函数（用于PPT/Word生成）
    @override
    def chat_messages(self, messages: List[Dict]) -> str | None:
        """
        直接消息对话接口
        
        接收已构造好的消息列表，用于PPT/Word生成等需要自定义消息结构的场景
        
        参数:
            messages: 消息列表
        
        返回:
            str | None: LLM的回答文本
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            top_p=0.7,
            temperature=0.95,
            max_tokens=1024,
        )

        return response.choices[0].message.content

    # 单轮对话函数（不支持流式输出，无历史输入）
    @override  #@override是一个装饰器，用于标记方法为重写，确保子类实现该方法
    def ask_model(self, prompt: str) -> str | None:
        """
        单轮对话接口
        
        用于简单的一次性问答，不支持对话历史和流式输出
        
        参数:
            prompt: 用户输入的提示词
        
        返回:
            str | None: LLM的回答文本，失败返回None
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "user", "content": prompt},
            ],
            top_p=0.7,                                            # 核采样参数
            temperature=0.95,                                      # 温度参数（控制随机性）
            max_tokens=1024,                                       # 最大生成token数
        )
        return response.choices[0].message.content

    # 流式对话函数（支持流式输出和历史记录）
    @override
    def ask_model_stream(
        self, prompt: str, history: List[List[str]] | None = None
    ) -> ChatCompletion | Stream[ChatCompletionChunk]:
    #ChatCompletionChunk是一个OpenAI的类型，用于表示流式响应的每个部分
    #ChatCompletion是一个OpenAI的类型，用于表示完整的对话响应
    #Stream是一个OpenAI的类型，用于表示流式响应,是一个生成器对象，每次迭代返回一个ChatCompletionChunk对象
        """
        流式对话接口（主要功能函数）
        
        支持流式输出和对话历史，是系统的主要对话接口
        
        参数:
            prompt: 当前用户输入
            history: 对话历史记录（列表形式）
        
        返回:
            Stream[ChatCompletionChunk]: 流式响应对象
        """
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=self.build_messages(prompt, history if history else []),
            top_p=0.7,
            temperature=0.95,
            max_tokens=1024,
            stream=True,                                          # 启用流式输出
        )
        return response
