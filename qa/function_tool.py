'''存放处理不同问答类型的工具函数，核心文件'''

import base64
from typing import Callable, List, Dict, Tuple
import time
import json
from client.clientfactory import client_broker           # 客户端工厂
from qa.purpose_type import intent_type              # 意图类型枚举
from pathlib import Path                                 # 文件路径处理
from ppt_docx.ppt_generation import render_ppt  # PPT生成函数
from ppt_docx.ppt_content import build_ppt_json    # PPT内容生成
from ppt_docx.docx_generation import render_docx  # DOCX生成
from ppt_docx.docx_content import build_docx_json  # DOCX内容生成
from rag import rag_chain                                # RAG检索链
from audio.audio_extract import (                        # 音频提取工具
    pull_text,
    detect_lang,
    detect_gender,
    pick_voice,
)
from audio.audio_generate import synthesize          # 音频生成函数
from Internet.Internet_chain import run_web_search  # 联网搜索链
from config.config import config_manager                         # 配置管理
from env import env_value                            # 环境变量获取


def is_local_path(path):
    """判断给定路径是否为有效的文件路径"""
    return Path(path).exists()


# 处理图片生成问题的函数
def handle_image_gen(question_type, question, history, image_url=None):
    """
    文生图工具
    
    参数:
        question_type: 问题类型
        question: 图片描述文本
        history: 对话历史（未使用）
        image_url: 图片URL（未使用）
    
    返回:
        Tuple[str, intent_type]: (生成的图片URL, 问题类型)
    """
    # 获取图片生成专用客户端
    client = client_broker.get_typed(client_type=question_type)
    response = client.images.generations(
        model=env_value("IMAGE_GENERATE_MODEL"),  # 获取图片生成模型配置
        prompt=question,                               # 图片描述
    )
    print(response.data[0].url)
    return (response.data[0].url, question_type)


def handle_image_desc(question_type, question, history, image_url=None):
    """
    图生文工具（图片描述）
    
    参数:
        question_type: 问题类型
        question: 描述指令
        history: 对话历史（未使用）
        image_url: 图片URL列表
    
    返回:
        Tuple[str, intent_type]: (图片描述文本, 问题类型)
    """
    # 默认问题处理
    if question == "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'请问您有什么想了解的，我将尽力为您服务'":
        question = "描述这个图片，说明这个图片的主要内容"
    
    image_bases = []
    for img_url in image_url:
        # 如果是本地文件路径，转换为Base64编码
        if is_local_path(img_url):
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
    client = client_broker.get_typed(client_type=question_type)
    # 发送请求
    response = client.chat.completions.create(
        model=env_value("IMAGE_DESCRIBE_MODEL"),
        messages=[
            {
                "role": "user",
                "content": message_content,
            }
        ],
    )
    return (response.choices[0].message.content, question_type)


def handle_video(question_type, question, history, image_url=None):
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
        Tuple[Tuple[str, str], intent_type]: ((视频URL, "视频"), 问题类型)
    """
    client = client_broker.get_typed(client_type=question_type)
    try:
        # 提交视频生成请求
        video_task = client.videos.generations(
            model=env_value("VIDEO_GENERATE_MODEL"),
            prompt=question,
        )
        #video_task是一个视频生成任务对象，包含任务ID、状态、视频URL等信息
        print(video_task)
        # video_task的实际内容
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
            print(video_task.id)
            #retrieve_videos_result方法用于查询视频生成任务的状态和结果
            response = client.videos.retrieve_videos_result(id=video_task.id)

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
def handle_audio(
    question_type: intent_type,
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
        Tuple[Tuple[str, str], intent_type]: ((音频文件路径, "audio"), 问题类型)
    """
    # 提取需要转换为语音的文本
    text = pull_text(question, history)
    # 判断需要生成的语言（如东北话、陕西话、粤语等）
    lang = detect_lang(question)
    # 判断需要生成的性别（男声/女声）
    gender = detect_gender(question)

    # 选择用于生成的TTS模型
    model_name, success = pick_voice(lang=lang, gender=gender)
    if success:
        audio_file = synthesize(text, model_name)
    else:
        # 目标语言包缺失，使用普通话替代
        audio_file = synthesize(
            "由于目标语言包缺失，我将用普通话回复您。" + text, model_name
        )
    
    return ((audio_file, "audio"), question_type)


def handle_ppt(
    question_type, question: str, history: List[List[str] | None] = None, image_url=None
) -> Tuple[Tuple[str, str], intent_type]:
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
        Tuple[Tuple[str, str], intent_type]: ((文件路径, "ppt"), 问题类型)
    """
    # 生成PPT内容结构
    raw_text: str = build_ppt_json(question, history)
    try:
        ppt_content = json.loads(raw_text)
    except:
        # JSON解析失败，返回None
        return None, intent_type.ppt
    
    # 生成PPT文件
    ppt_file: str = render_ppt(ppt_content)
    return (ppt_file, "ppt"), intent_type.ppt


def handle_docx(
    question_type, question: str, history: List[List[str] | None] = None, image_url=None
) -> Tuple[Tuple[str, str], intent_type]:
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
        Tuple[Tuple[str, str], intent_type]: ((文件路径, "docx"), 问题类型)
    """
    # 先生成Word文档内容
    raw_text: str = build_docx_json(question, history)
    try:
        docx_content = json.loads(raw_text)
    except:
        # JSON解析失败，返回None
        return None, intent_type.docx
    
    # 生成DOCX文件
    docx_file: str = render_docx(docx_content)
    return (docx_file, "docx"), intent_type.docx


# 处理联网搜索问题的函数
def handle_web_search(
    question_type: intent_type,
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
        Tuple[Stream, intent_type, Dict, bool]: (流式回答, 问题类型, 链接字典, 是否成功)
    """
    response, links, success = run_web_search(question, history)
    return (response, question_type, links, success)


# 处理文本生成问题的函数
def handle_text(
    question_type: intent_type,
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
        Tuple[Stream, intent_type]: (流式回答, 问题类型)
    """
    response = client_broker().get_default().ask_model_stream(question, history)
    return (response, question_type)


# 处理RAG问题的函数
def handle_rag(
    question_type: intent_type,
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
        Tuple[Stream, intent_type]: (流式回答, 问题类型)
    """
    # 调用RAG链进行检索和回答
    response = rag_chain.run(question, history)
    return (response, question_type)


# 意图类型到处理函数的映射字典
# 核心路由表，根据用户意图类型分发到对应的处理函数
intent_router = {
    intent_type.text: handle_text,              # 文本生成
    intent_type.rag: handle_rag,                        # RAG检索
    intent_type.image_gen: handle_image_gen,  # 图片生成
    intent_type.audio: handle_audio,            # 语音生成
    intent_type.web_search: handle_web_search,  # 联网搜索
    intent_type.image_desc: handle_image_desc,   # 图片描述
    intent_type.ppt: handle_ppt,                # PPT生成
    intent_type.docx: handle_docx,              # DOCX生成
    intent_type.video: handle_video,       # 视频生成
}


# 根据用户不同的意图选择不同的函数
def route_intent(purpose: intent_type) -> Callable:
    """
    根据意图类型获取对应的处理函数
    
    参数:
        purpose: 用户意图类型
    
    返回:
        Callable: 对应的处理函数
    
    异常:
        ValueError: 未找到对应的处理函数
    """
    if purpose in intent_router:
        return intent_router[purpose]
    else:
        raise ValueError("没有找到意图对应的函数")
