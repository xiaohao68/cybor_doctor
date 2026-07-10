'''Edge-TTS调用接口 - 用于将文本转换为语音'''
import os                                                         # 操作系统接口
import asyncio                                                     # 异步编程支持

from env import get_app_root                                       # 获取应用根目录
import hashlib                                                    # 哈希算法
import edge_tts                                                   # Edge-TTS库


# 音频文件保存目录
_OUTPUT_DIR = os.path.join(get_app_root(), "data/cache/audio")

# 如果目录不存在，先创建
if not os.path.exists(_OUTPUT_DIR):
    os.makedirs(_OUTPUT_DIR)


def get_file_path(text):
    """
    根据文本内容生成唯一的文件名（使用SHA256哈希）
    
    参数:
        text: 待转换的文本内容
    
    返回:
        str: 音频文件的完整路径
    """
    # 使用SHA256哈希生成唯一文件名
    file_name = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return os.path.join(_OUTPUT_DIR, f"{file_name}.mp3")


def audio_generate(text: str, model_name: str) -> str:
    """
    将文本转换为语音（使用Edge-TTS）
    
    流程：
    1. 根据文本生成唯一文件名
    2. 使用Edge-TTS异步生成语音
    3. 保存音频文件到指定目录
    
    参数:
        text: 待转换的文本内容
        model_name: TTS模型名称（如zh-CN-YunxiNeural）
    
    返回:
        str: 生成的音频文件路径
    """
    # 生成输出文件路径
    _output_file = get_file_path(text)

    # 异步生成函数
    async def _generating() -> None:
        import edge_tts  # Edge-TTS库
        # 创建Edge-TTS通信对象
        communicate = edge_tts.Communicate(text, model_name)
        # 保存音频文件
        await communicate.save(_output_file)

    # 执行异步任务
    asyncio.run(_generating())

    return _output_file

"""
支持的中文语音模型（部分）：
- zh-CN-YunxiNeural: 云希（女声，标准普通话）
- zh-CN-YunjianNeural: 云健（男声，标准普通话）
- zh-CN-YunxiaNeural: 云夏（女声，年轻）
- zh-CN-YunyangNeural: 云阳（男声）
- zh-CN-LiaoningNeural: 辽宁话
- zh-CN-ShanxiNeural: 山西话
- zh-HK-HiuMaanNeural: 粤语（女声）
- zh-HK-WanLungNeural: 粤语（男声）
- zh-TW-HsiaoChenNeural: 闽南语（女声）
- zh-TW-YunJheNeural: 闽南语（男声）
"""