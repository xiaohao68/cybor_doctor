from abc import ABC, abstractmethod                              # 抽象基类支持
from openai import OpenAI                                        # OpenAI客户端
from typing import List, Dict                                     # 类型提示

from env import env_value                                         # 环境变量获取


class llm_client_base(ABC):
    """
    LLM客户端基类（抽象类）
    
    定义所有LLM客户端必须实现的接口方法，提供统一的客户端初始化逻辑
    """

    # @abstractmethods 是所有子类必须实现的方法，不能直接调用，只能通过子类实例调用
    # 这是ABC（抽象基类）的一个重要特性，用于强制子类实现必要的方法
    @abstractmethod
    def ask_model(self, prompt: str) -> str | None:
        """
        单轮对话接口（抽象方法）
        
        参数:
            prompt: 用户输入的提示词
        
        返回:
            str | None: LLM的回答文本
        """
        pass

    @abstractmethod
    def ask_model_stream(
        self, prompt: str, history: List[List[str]] | None = None
    ):
        """
        流式对话接口（抽象方法）
        
        参数:
            prompt: 当前用户输入
            history: 对话历史记录
        
        返回:
            流式响应对象
        """
        pass

    @abstractmethod
    def build_messages(
        self, prompt: str, history: List[List[str]] | None = None
    ) -> List[Dict[str, str]] | str | None:
        """
        消息构造函数（抽象方法）
        
        参数:
            prompt: 当前用户输入
            history: 对话历史记录
        
        返回:
            消息列表
        """
        pass

    @abstractmethod
    def chat_messages(self, messages: List[Dict]) -> str | None:
        """
        直接消息对话接口（抽象方法）
        
        参数:
            messages: 已构造好的消息列表
        
        返回:
            str | None: LLM的回答文本
        """
        pass

    #@property是一个装饰器，用于将方法转换为属性调用
    @property
    def model_name(self):
        """
        获取模型名称属性
        
        返回:
            str: 当前使用的模型名称
        """
        return self._model

    def __init__(self) -> None:
        """
        初始化LLM客户端
        
        从环境变量获取配置并创建OpenAI客户端实例
        """
        # 获取LLM服务地址（默认为OpenAI官方地址）
        self._base_url = env_value("LLM_BASE_URL") or "https://api.openai.com/v1"
        # 获取API密钥
        self._api_key = env_value("LLM_API_KEY")
        # 获取模型名称
        self._model = env_value("MODEL_NAME") or "gpt-4o"
        
        # 创建OpenAI客户端实例
        self.client = OpenAI(
            base_url=self._base_url,
            api_key=self._api_key,
        )
