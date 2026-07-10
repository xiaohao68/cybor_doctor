'''向外部构建不同大模型代理的接口，构建完成后返回一个大模型代理'''
from client.ourAPI.client import OurAPI                                             # 默认LLM客户端
from client.zhipuAPI.client import Image_generate_client, Image_describe_client      # 图片相关客户端
from client.zhipuAPI.client import Video_generate_client                             # 视频生成客户端
from env import get_env_value                                                       # 环境变量获取
from qa.purpose_type import userPurposeType                                          # 意图类型枚举


class Clientfactory:
    """
    客户端工厂类
    
    负责根据不同的任务类型返回对应的LLM客户端实例，实现客户端的统一管理和分发
    """
    
    # 初始化client字典（使用环境变量中的LLM_BASE_URL）
    map_client_dict = {get_env_value("LLM_BASE_URL")}

    # 初始化client的url和apikey
    def __init__(self):
        """
        初始化客户端工厂
        
        从环境变量中获取LLM的基础URL和API密钥
        """
        self._client_url = get_env_value("LLM_BASE_URL")
        self._api_key = get_env_value("LLM_API_KEY")

    def get_client(self):
        """
        获取默认的文本LLM客户端实例
        
        返回:
            OurAPI: 默认的文本生成客户端
        """
        return OurAPI()
    # @staticmethod是一个装饰器，用于将方法转换为静态方法，不依赖于类的实例，
    # 就是不用写Clientfactory()，直接调用Clientfactory.get_special_client()方法
    @staticmethod
    def get_special_client(client_type: str):
        """
        根据客户端类型获取特定的客户端实例
        
        参数:
            client_type: 客户端类型（userPurposeType枚举值）
        
        返回:
            对应的客户端实例
        """
        print("get_special_client")
        
        # 根据任务类型返回对应的专用客户端
        if client_type == userPurposeType.ImageGeneration:
            return Image_generate_client           # 图片生成客户端
        if client_type == userPurposeType.ImageDescribe:
            return Image_describe_client           # 图片描述客户端
        if client_type == userPurposeType.Video:
            return Video_generate_client           # 视频生成客户端

        # 默认情况下使用文本生成模型
        return OurAPI()