'''向外部构建不同大模型代理的接口，构建完成后返回一个大模型代理'''
from client.ourAPI.client import our_api                                            # 默认LLM客户端
from client.zhipuAPI.client import image_gen_client, image_desc_client               # 图片相关客户端
from client.zhipuAPI.client import video_gen_client                                  # 视频生成客户端
from env import env_value                                                            # 环境变量获取
from qa.purpose_type import intent_type                                              # 意图类型枚举


class client_broker:
    """
    客户端工厂类
    
    负责根据不同的任务类型返回对应的LLM客户端实例，实现客户端的统一管理和分发
    """
    
    # 初始化client字典（使用环境变量中的LLM_BASE_URL）
    client_map = {env_value("LLM_BASE_URL")}

    # 初始化client的url和apikey
    def __init__(self):
        """
        初始化客户端工厂
        
        从环境变量中获取LLM的基础URL和API密钥
        """
        self._base_url = env_value("LLM_BASE_URL")
        self._api_key = env_value("LLM_API_KEY")

    # @staticmethod是一个装饰器，用于将方法转换为静态方法，不依赖于类的实例，
    # 就是不用写client_broker()，直接调用client_broker.get_typed()方法
    @staticmethod
    def get_typed(client_type: str):
        """
        根据客户端类型获取特定的客户端实例
        
        参数:
            client_type: 客户端类型（intent_type枚举值）
        
        返回:
            对应的客户端实例
        """
        print("get_typed")
        
        # 根据任务类型返回对应的专用客户端
        if client_type == intent_type.image_gen:
            return image_gen_client              # 图片生成客户端
        if client_type == intent_type.image_desc:
            return image_desc_client             # 图片描述客户端
        if client_type == intent_type.video:
            return video_gen_client              # 视频生成客户端

        # 默认情况下使用文本生成模型
        return our_api()

    def get_default(self):
        """
        获取默认的文本LLM客户端实例
        
        返回:
            our_api: 默认的文本生成客户端
        """
        return our_api()
