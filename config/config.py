
import yaml                                                    # YAML配置解析
import os                                                      # 操作系统接口

from env import app_root                                       # 获取应用根目录


class config_manager(object):
    """
    配置管理类（单例模式）
    
    负责加载和管理应用配置，支持多环境配置切换
    """
    
    __singleton = None                                         # 单例实例
    import threading #适用于处理用户请求，加载知识库时，保证配置实例不会重复创建

    __mutex = threading.Lock() # 线程锁，保证多线程下不会重复创建配置实例（就是保证单例模式），保证线程安全

    def __init__(self):
        """初始化配置对象"""
        self._config = None                                     # 配置数据存储

    # 缓存装饰器，缓存配置查询结果，不用每次都遍历配置树，提升性能
    from functools import lru_cache                                # 缓存装饰器

    @lru_cache(maxsize=128)#maxsize缓存最大数量，默认128
    def nested_get(self, *params):
        """
        获取嵌套配置参数
        
        支持通过多个参数逐级访问嵌套配置
        使用lru_cache缓存查询结果，提高性能
        
        参数:
            *params: 可变参数，逐级指定配置路径
        
        返回:
            配置值
        
        异常:
            KeyError: 参数不存在时抛出
        """
        #assert params, "params为空，无法获取配置参数" assert是断言校验，如果params为空，就抛出错误提示
        # 1. 断言校验：如果_config没加载（还是None），直接抛出错误提示
        assert self._config is not None, "please load config first"

        # 2. 把根配置字典赋值给临时变量conf，用来逐级遍历
        conf = self._config

        # 3. 遍历传入的嵌套参数（比如传入("llm", "api_key")，就遍历"llm"→"api_key"）
        for param in params:
            # 4. 如果当前层级有这个配置项，就进入下一级
            if param in conf:
                conf = conf[param]
            # 5. 找不到就抛出清晰的KeyError，告诉你哪个配置项不存在
            else:
                raise KeyError(f"{param} not found in config")

        # 6. 遍历完所有层级，返回最终找到的配置值
        return conf

    @classmethod
    def _load_yaml(cls):
        """
        加载配置文件（私有方法）
        
        根据环境变量PY_ENVIRONMENT选择对应的配置文件
        配置文件路径: config/config-{env}.yaml
        
        返回:
            config_manager: 配置实例
        """
        instance = config_manager()
        root = app_root()                                       # 获取应用根目录
        env = os.environ.get("PY_ENVIRONMENT")                  # 获取环境变量
        print(env)
        # 加载对应环境的配置文件
        with open(os.path.join(root, "config", f"config-{env}.yaml"), "r", encoding="utf-8") as f:
        #setattr设置配置实例的_config属性为加载的配置数据  settr(对象，属性名，属性值)
        #yaml.load(f, Loader=yaml.FullLoader)  加载YAML文件，使用FullLoader解析器
            setattr(instance, "_config", yaml.load(f, Loader=yaml.FullLoader))

        return instance

#cls是类方法（@classmethod装饰的方法）的固定第一个参数，代表类本身，就是config_manager类
#cls表示类本身，self表示类创建出来的实例对象
    @classmethod
    def instance(cls):
        """
        获取配置单例实例（线程安全）
        
        返回:
            config_manager: 配置单例实例
        """
        with cls.__mutex:
            if cls.__singleton is None:
                cls.__singleton = cls._load_yaml()
            return cls.__singleton



# 测试入口
if __name__ == "__main__":
    print(app_root())
