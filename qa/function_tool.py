'''存放处理不同问答类型的工具函数，核心文件'''

import base64
from typing import Callable, List, Dict, Tuple
import time
import json
from client.clientfactory import Clientfactory           # 客户端工厂
from qa.purpose_type import userPurposeType              # 意图类型枚举
from pathlib import Path                                 # 文件路径处理
from ppt_docx.ppt_generation import generate as generate_ppt  # PPT生成函数
from ppt_docx.ppt_content import generate_ppt_content    # PPT内容生成
from ppt_docx.docx_generation import generate_docx_content as generate_docx  # DOCX生成
from ppt_docx.docx_content import generate_docx_content  # DOCX内容生成
from rag import rag_chain                                # RAG检索链
from audio.audio_extract import (                        # 音频提取工具
    extract_text,
    extract_language,
    extract_gender,
    get_tts_model_name,
)
from audio.audio_generate import audio_generate          # 音频生成函数
from model.KG.search_service import search               # 知识图谱搜索服务
from Internet.Internet_chain import InternetSearchChain  # 联网搜索链
from kg.Graph import GraphDao                            # 知识图谱DAO
from config.config import Config                         # 配置管理
from qa.purpose_type import userPurposeType              # 意图类型枚举（重复导入）
from env import get_env_value                            # 环境变量获取


# 初始化知识图谱DAO实例
_dao = GraphDao()


def is_file_path(path):
    """判断给定路径是否为有效的文件路径"""
    return Path(path).exists()


def relation_tool(entities: List[Dict] | None) -> str | None:
    """
    从知识图谱中检索实体之间的关系
    
    参数:
        entities: 实体列表（每个实体是字典形式）
    
    返回:
        str: 关系描述字符串（分号分隔），如果没有关系则返回None
    """
    if not entities or len(entities) == 0:
        return None

    relationships = set()  # 使用集合避免重复关系
    relationship_match = []

    # 从配置中获取知识图谱实体的搜索关键字段
    searchKey = Config.get_instance().get_with_nested_params("model", "graph-entity", "search-key")
    
    # 遍历每个实体并查询与其他实体的关系
    for entity in entities:
        entity_name = entity[searchKey]
        # 添加实体自身的属性信息
        for k, v in entity.items():
            relationships.add(f"{entity_name} {k}: {v}")

        # 查询该实体与其他实体的关系（a-r-b形式）
        relationship_match.append(_dao.query_relationship_by_name(entity_name))
    
    # 抽取并记录每个实体与其他实体的关系
    for i in range(len(relationship_match)):
        for record in relationship_match[i]:
            # 获取起始节点和结束节点的名称
            start_name = record["r"].start_node[searchKey]
            end_name = record["r"].end_node[searchKey]

            # 获取关系类型（如CAUSES、TREATS等）
            rel = type(record["r"]).__name__

            # 构建关系字符串并添加到集合
            relationships.add(f"{start_name} {rel} {end_name}")

    # 返回关系集合内容，如果为空则返回None
    if relationships:
        return "；".join(relationships)
    else:
        return None


def check_entity(question: str) -> List[Dict]:
    """
    从知识图谱中检查并提取问题中的实体
    
    参数:
        question: 用户问题文本
    
    返回:
        List[Dict]: 实体列表，如果失败返回None
    """
    code, result = search(question)
    if code == 0:
        return result
    else:
        return None


def KG_tool(
    question_type: userPurposeType,
    question: str,
    history: List[List | None] = None,
    image_url=None,
):
    """
    知识图谱问答工具
    
    流程：
    1. 从问题中提取实体
    2. 查询实体之间的关系
    3. 将关系信息融入问题，调用LLM生成回答
    
    参数:
        question_type: 问题类型
        question: 用户问题
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Stream, userPurposeType]: (流式回答, 问题类型)
    """
    kg_info = None
    try:
        # 检查问题中的实体
        entities = check_entity(question)
        # 查询实体关系
        kg_info = relation_tool(entities)
    except:
        pass

    # 如果获取到知识图谱信息，将其添加到问题中
    if kg_info is not None:
        print(f"KG_tool: \n {kg_info}")
        question = f"{question}\n从知识图谱中检索到的信息如下{kg_info}\n请你基于知识图谱的信息去回答,并给出知识图谱检索到的信息"

    # 调用LLM进行流式回答
    response = Clientfactory().get_client().chat_with_ai_stream(question, history)
    return (response, question_type)


# 处理文本生成问题的函数
def process_text_tool(
    question_type: userPurposeType,
    question: str,
    history: List[List | None] = None,
    image_url=None,
):
    """
    文本生成工具（直接调用LLM回答）
    
    参数:
        question_type: 问题类型
        question: 用户问题
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Stream, userPurposeType]: (流式回答, 问题类型)
    """
    response = Clientfactory().get_client().chat_with_ai_stream(question, history)
    return (response, question_type)


# 处理RAG问题的函数
def RAG_tool(
    question_type: userPurposeType,
    question: str,
    history: List[List | None] = None,
    image_url=None,
):
    """
    RAG检索增强生成工具
    
    流程：
    1. 使用问题检索知识库文档
    2. 将检索到的文档内容融入prompt
    3. 调用LLM生成基于文档的回答
    
    参数:
        question_type: 问题类型
        question: 用户问题
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Stream, userPurposeType]: (流式回答, 问题类型)
    """
    # 调用RAG链进行检索和回答
    response = rag_chain.invoke(question, history)
    return (response, question_type)


# 处理图片生成问题的函数
def process_images_tool(question_type, question, history, image_url=None):
    """
    文生图工具
    
    参数:
        question_type: 问题类型
        question: 图片描述文本
        history: 对话历史（未使用）
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[str, userPurposeType]: (生成的图片URL, 问题类型)
    """
    # 获取图片生成专用客户端
    client = Clientfactory.get_special_client(client_type=question_type)
    response = client.images.generations(
        model=get_env_value("IMAGE_GENERATE_MODEL"),  # 获取图片生成模型配置
        prompt=question,                               # 图片描述
    )
    print(response.data[0].url)
    return (response.data[0].url, question_type)


def process_image_describe_tool(question_type, question, history, image_url=None):
    """
    图生文工具（图片描述）
    
    参数:
        question_type: 问题类型
        question: 描述指令
        history: 对话历史（未使用）
        image_url: 图片URL列表
    
    返回:
        Tuple[str, userPurposeType]: (图片描述文本, 问题类型)
    """
    # 默认问题处理
    if question == "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'请问您有什么想了解的，我将尽力为您服务'":
        question = "描述这个图片，说明这个图片的主要内容"
    
    image_bases = []
    for img_url in image_url:
        # 如果是本地文件路径，转换为Base64编码
        if is_file_path(img_url):
            with open(img_url, "rb") as img_file:
    #base64.b64encode()函数将二进制数据编码为Base64字符串
    #decode("utf-8")将Base64字符串转换为UTF-8编码的字符串，方便后续处理
                image_base = base64.b64encode(img_file.read()).decode("utf-8")
                image_bases.append(image_base)
        else:
            # 已经是Base64或URL形式
            image_bases.append(img_url)

    # 构建messages内容（多模态输入）
    message_content = []
    for image_base in image_bases:
        message_content.append({"type": "image_url", "image_url": {"url": image_base}})
    # 添加问题文本
    message_content.append({"type": "text", "text": question})

    # 获取图片描述专用客户端
    client = Clientfactory.get_special_client(client_type=question_type)
    # 发送请求
    response = client.chat.completions.create(
        model=get_env_value("IMAGE_DESCRIBE_MODEL"),
        messages=[
            {
                "role": "user",
                "content": message_content,
            }
        ],
    )
    return (response.choices[0].message.content, question_type)


def process_ppt_tool(
    question_type, question: str, history: List[List[str] | None] = None, image_url=None
) -> Tuple[Tuple[str, str], userPurposeType]:
    """
    PPT生成工具
    
    流程：
    1. 调用LLM生成PPT内容结构（JSON格式）
    2. 使用生成的内容创建PPT文件
    
    参数:
        question_type: 问题类型
        question: PPT主题/需求描述
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Tuple[str, str], userPurposeType]: ((文件路径, "ppt"), 问题类型)
    """
    # 生成PPT内容结构
    raw_text: str = generate_ppt_content(question, history)
    try:
        ppt_content = json.loads(raw_text)
    except:
        # JSON解析失败，返回None
        return None, userPurposeType.PPT
    
    # 生成PPT文件
    ppt_file: str = generate_ppt(ppt_content)
    return (ppt_file, "ppt"), userPurposeType.PPT


def process_docx_tool(
    question_type, question: str, history: List[List[str] | None] = None, image_url=None
) -> Tuple[Tuple[str, str], userPurposeType]:
    """
    DOCX文档生成工具
    
    流程：
    1. 调用LLM生成文档内容结构（JSON格式）
    2. 使用生成的内容创建DOCX文件
    
    参数:
        question_type: 问题类型
        question: 文档主题/需求描述
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Tuple[str, str], userPurposeType]: ((文件路径, "docx"), 问题类型)
    """
    # 先生成Word文档内容
    raw_text: str = generate_docx_content(question, history)
    try:
        docx_content = json.loads(raw_text)
    except:
        # JSON解析失败，返回None
        return None, userPurposeType.Docx
    
    # 生成DOCX文件
    docx_file: str = generate_docx(docx_content)
    return (docx_file, "docx"), userPurposeType.Docx


def process_text_video_tool(question_type, question, history, image_url=None):
    """
    视频生成工具
    
    流程：
    1. 提交视频生成请求
    2. 轮询等待生成完成（最多120秒）
    3. 返回视频URL
    
    参数:
        question_type: 问题类型
        question: 视频描述文本
        history: 对话历史（未使用）
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Tuple[str, str], userPurposeType]: ((视频URL, "视频"), 问题类型)
    """
    client = Clientfactory.get_special_client(client_type=question_type)
    try:
        # 提交视频生成请求
        chatRequest = client.videos.generations(
            model=get_env_value("VIDEO_GENERATE_MODEL"),
            prompt=question,
        )
        #chatRequest是一个视频生成任务对象，包含任务ID、状态、视频URL等信息
        print(chatRequest)
        # chatRequest的实际内容
# {
#     "id": "vid-123456789abcdef",  # ✅ 核心：任务ID，轮询的时候必须用这个ID查
#     "model": "video-generate",
#     "task_status": "PENDING",  # 初始状态：排队中
#     "create_time": 1718200000
# }

        start_time = time.time()  # 开始计时
        video_url = None
        timeout = 600  # 超时时间600秒
        
        # 轮询等待视频生成完成
        while time.time() - start_time < timeout:
            print(chatRequest.id)
            #retrieve_videos_result方法用于查询视频生成任务的状态和结果
            response = client.videos.retrieve_videos_result(id=chatRequest.id)

            # 检查任务状态是否成功
#             {    response的样式
#     "id": "vid-123456789abcdef",  # 任务ID
#     "task_status": "SUCCESS",  # ✅ 任务状态：PENDING(排队)/RUNNING(生成中)/SUCCESS(成功)/FAILED(失败)
#     "video_result": [  # 生成成功才有值，失败/生成中是null
#         {
#             "url": "https://sfile.chatglm.cn/xxx/生成的视频.mp4",  # ✅ 最终的视频URL
#             "cover_url": "https://xxx/封面图.png",
#             "duration": 10  # 视频时长（秒）
#         }
#     ],
#     "error_msg": null,  # 失败的时候会有错误信息
#     "progress": 80  # 生成进度（百分比）
# }
            if response.task_status == "SUCCESS" and response.video_result:
                video_url = response.video_result[0].url
                print("视频URL:", video_url)
                return ((video_url, "视频"), question_type)
            else:
                print("任务未完成，请等待...")

            # 等待2秒后再次查询
            time.sleep(2)

    except:
        # 生成失败，返回None
        return (None, question_type)


# 处理音频生成问题的函数
def process_audio_tool(
    question_type: userPurposeType,
    question: str,
    history: List[List | None] = None,
    image_url=None,
):
    """
    语音生成工具
    
    流程：
    1. 调用LLM提取需要转换为语音的文本
    2. 检测语言类型（普通话/方言）
    3. 检测性别偏好（男声/女声）
    4. 选择合适的TTS模型生成语音
    
    参数:
        question_type: 问题类型
        question: 用户请求（可能包含语言和性别要求）
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Tuple[str, str], userPurposeType]: ((音频文件路径, "audio"), 问题类型)
    """
    # 提取需要转换为语音的文本
    text = extract_text(question, history)
    # 判断需要生成的语言（如东北话、陕西话、粤语等）
    lang = extract_language(question)
    # 判断需要生成的性别（男声/女声）
    gender = extract_gender(question)

    # 选择用于生成的TTS模型
    model_name, success = get_tts_model_name(lang=lang, gender=gender)
    if success:
        audio_file = audio_generate(text, model_name)
    else:
        # 目标语言包缺失，使用普通话替代
        audio_file = audio_generate(
            "由于目标语言包缺失，我将用普通话回复您。" + text, model_name
        )
    
    return ((audio_file, "audio"), question_type)


# 处理联网搜索问题的函数
def process_InternetSearch_tool(
    question_type: userPurposeType,
    question: str,
    history: List[List | None] = None,
    image_url=None,
):
    """
    联网搜索工具
    
    流程：
    1. 并行调用Bing和百度搜索
    2. 下载搜索结果页面
    3. 提取页面内容构建prompt
    4. 调用LLM基于搜索结果生成回答
    
    参数:
        question_type: 问题类型
        question: 用户搜索查询
        history: 对话历史
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[Stream, userPurposeType, Dict, bool]: (流式回答, 问题类型, 链接字典, 是否成功)
    """
    response, links, success = InternetSearchChain(question, history)
    return (response, question_type, links, success)


# 意图类型到处理函数的映射字典
# 核心路由表，根据用户意图类型分发到对应的处理函数
QUESTION_TO_FUNCTION = {
    userPurposeType.text: process_text_tool,              # 文本生成
    userPurposeType.RAG: RAG_tool,                        # RAG检索
    userPurposeType.ImageGeneration: process_images_tool,  # 图片生成
    userPurposeType.Audio: process_audio_tool,            # 语音生成
    userPurposeType.InternetSearch: process_InternetSearch_tool,  # 联网搜索
    userPurposeType.ImageDescribe: process_image_describe_tool,   # 图片描述
    userPurposeType.PPT: process_ppt_tool,                # PPT生成
    userPurposeType.Docx: process_docx_tool,              # DOCX生成
    userPurposeType.Video: process_text_video_tool,       # 视频生成
    userPurposeType.KnowledgeGraph: KG_tool,              # 知识图谱问答
}


# 根据用户不同的意图选择不同的函数
def map_question_to_function(purpose: userPurposeType) -> Callable:
    """
    根据意图类型获取对应的处理函数
    
    参数:
        purpose: 用户意图类型
    
    返回:
        Callable: 对应的处理函数
    
    异常:
        ValueError: 未找到对应的处理函数
    """
    if purpose in QUESTION_TO_FUNCTION:
        return QUESTION_TO_FUNCTION[purpose]
    else:
        raise ValueError("没有找到意图对应的函数")