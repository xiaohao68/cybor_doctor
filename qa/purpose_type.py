from enum import Enum


# 意图名称到枚举类型的映射字典
# 用于将字符串形式的意图名称转换为对应的枚举值
intent_map = {
    "其他": None,           # 默认回退类型，下方类定义后回填
    "文本生成": None,       # 文本生成
    "音频生成": None,      # 语音生成
    "视频生成": None,      # 视频生成
    "图片描述": None, # 图生文
    "图片生成": None, # 文生图
    "基于知识库": None,      # 知识库检索
    "问候语": None,        # 问候语
    "PPT生成": None,         # PPT生成
    "Word生成": None,       # Word生成
    "网络搜索": None, # 联网搜索
}


class intent_type(Enum):
    """
    用户意图类型枚举
    
    定义了系统支持的所有用户意图类型，每个类型对应一个数值标识
    """
    
    text = 0                  # 未知问题/文本生成（默认类型）
    audio = 1                 # 语音生成（将文本转换为语音）
    video = 2                 # 视频生成（文生视频）
    image_gen = 3       # 文生图（根据文字描述生成图片）
    image_desc = 4         # 图生文（描述图片内容）
    rag = 5                   # 基于知识库检索（从向量数据库获取答案）
    greeting = 6                 # 问候语（特定回复）
    ppt = 7                   # PPT生成（生成演示文稿）
    web_search = 8        # 网络搜索（联网获取最新信息）
    docx = 9                  # Word生成（生成文档）


# 回填映射表
intent_map["其他"] = intent_type.text
intent_map["文本生成"] = intent_type.text
intent_map["音频生成"] = intent_type.audio
intent_map["视频生成"] = intent_type.video
intent_map["图片描述"] = intent_type.image_desc
intent_map["图片生成"] = intent_type.image_gen
intent_map["基于知识库"] = intent_type.rag
intent_map["问候语"] = intent_type.greeting
intent_map["PPT生成"] = intent_type.ppt
intent_map["Word生成"] = intent_type.docx
intent_map["网络搜索"] = intent_type.web_search
