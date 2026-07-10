from enum import Enum

class userPurposeType(Enum):
    """
    用户意图类型枚举
    
    定义了系统支持的所有用户意图类型，每个类型对应一个数值标识
    """
    
    text = 0                  # 未知问题/文本生成（默认类型）
    Audio = 1                 # 语音生成（将文本转换为语音）
    Video = 2                 # 视频生成（文生视频）
    ImageGeneration = 3       # 文生图（根据文字描述生成图片）
    ImageDescribe = 4         # 图生文（描述图片内容）
    RAG = 5                   # 基于知识库检索（从向量数据库获取答案）
    Hello = 6                 # 问候语（特定回复）
    PPT = 7                   # PPT生成（生成演示文稿）
    InternetSearch = 8        # 网络搜索（联网获取最新信息）
    Docx = 9                  # Word生成（生成文档）
    KnowledgeGraph = 10       # 基于知识图谱的问答（从知识图谱获取关系信息）


# 意图名称到枚举类型的映射字典
# 用于将字符串形式的意图名称转换为对应的枚举值
purpose_map = {
    "其他": userPurposeType.text,           # 默认回退类型
    "文本生成": userPurposeType.text,       # 文本生成
    "音频生成": userPurposeType.Audio,      # 语音生成
    "视频生成": userPurposeType.Video,      # 视频生成
    "图片描述": userPurposeType.ImageDescribe, # 图生文
    "图片生成": userPurposeType.ImageGeneration, # 文生图
    "基于知识库": userPurposeType.RAG,      # 知识库检索
    "问候语": userPurposeType.Hello,        # 问候语
    "PPT生成": userPurposeType.PPT,         # PPT生成
    "Word生成": userPurposeType.Docx,       # Word生成
    "网络搜索": userPurposeType.InternetSearch, # 联网搜索
    "基于知识图谱": userPurposeType.KnowledgeGraph, # 知识图谱问答
}