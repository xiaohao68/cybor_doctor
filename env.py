import os                                                        # 操作系统接口
from dotenv import load_dotenv, dotenv_values                      # 环境变量加载工具
import gradio as gr                                               # Gradio框架
print(gr.__version__)                                             # 打印Gradio版本

# 加载.env文件中的环境变量（不覆盖已有变量）
load_dotenv(".env", override=False)
#dotenv_values()函数将.env文件里的环境变量加载为字典，键为变量名，值为变量值
print(f"setting environment variables: {dotenv_values('.env')}")   # 打印加载的环境变量


def get_app_root():
    """
    获取应用程序根目录
    
    返回:
        str: 当前工作目录路径
    """
    return os.getcwd()


def get_env_value(key):
    """
    获取环境变量值
    
    参数:
        key: 环境变量名称
    
    返回:
        str | None: 环境变量值，如果不存在返回None
    """
    return os.environ.get(key)


# 测试入口
if __name__ == '__main__':
    print("app root is: " + get_app_root())
    print("your API key is: " + get_env_value('LLM_API_KEY'))
    print("your url is: " + get_env_value('MODEL_NAME'))