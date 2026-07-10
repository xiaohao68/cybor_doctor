from openai import OpenAI                                      # OpenAI客户端
from client.LLMclientgeneric import LLMclientgeneric            # LLM客户端基类


class OurAPI(LLMclientgeneric):
    """
    默认LLM客户端实现
    
    继承自LLMclientgeneric，使用OpenAI兼容接口与自定义LLM服务通信
    
    通过环境变量配置：
    - LLM_BASE_URL: LLM服务地址
    - LLM_API_KEY: API密钥
    - MODEL_NAME: 模型名称
    """
    
    def __init__(self, *args, **kwargs):
        """
        初始化客户端
        
        调用父类构造函数，自动从环境变量加载配置
        """
        super().__init__(*args, **kwargs)