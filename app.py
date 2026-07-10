from qa.answer import get_answer                                                      # 答案获取入口函数
from qa.question_parser import parse_question                                          # 问题类型解析函数
from qa.function_tool import process_image_describe_tool                               # 图片描述处理工具
from qa.purpose_type import userPurposeType                                            # 用户意图类型枚举
from audio.audio_generate import audio_generate                                        # 音频生成函数

import gradio as gr                                                                   # Gradio界面框架
from icecream import ic                                                               # 调试工具
import os                                                                             # 操作系统接口

# 定义头像路径（用户头像，机器人头像）
AVATAR = ("resource/user.png", "resource/bot.jpg")
# 设置环境变量，解决KMP库重复问题
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"


def convert_to_simplified(text):
    """将繁体中文转换为简体中文"""
    from opencc import OpenCC                                                             # 繁简体转换
    # t2s表示繁体转简体   s2t表示简体转繁体
    converter = OpenCC("t2s")  
    return converter.convert(text)


def convert_audio_to_wav(audio_file_path):
    """将其他音频格式转换为WAV格式（语音识别要求WAV格式）"""
    from pydub import AudioSegment                                                        # 音频格式转换
    #AudioSegment是pydub库中的一个类，用于表示音频文件 
    #from_file()方法读取音频文件，自动提取音频文件格式MP3/WAV/M4A等音频格式并存为AudioSegment对象
    audio = AudioSegment.from_file(audio_file_path)  
    #rsplit表示从右侧开始切割，只分割一次                                 # 自动识别输入格式
    wav_file_path = audio_file_path.rsplit(".", 1)[0] + ".wav"                        # 生成WAV文件路径
    #export(目标文件路径，导出格式)方法将音频文件导出为指定格式，这里导出为WAV格式
    audio.export(wav_file_path, format="wav")                                          # 导出为WAV格式
    return wav_file_path


def audio_to_text(audio_file_path):
    """将音频文件转换为文本（使用Whisper模型）"""
    # 如果不是WAV格式，先转换为WAV
    if not audio_file_path.endswith(".wav"):
        audio_file_path = convert_audio_to_wav(audio_file_path)
    import speech_recognition as sr                                                       # 语音识别库
    # sr.Recognizer()：实例化语音识别器
    recognizer = sr.Recognizer()         
    #sr.AudioFile(audio_file_path)：创建一个音频文件对象，用于读取音频文件
    with sr.AudioFile(audio_file_path) as source:       
         # 录制音频数据，把音频以二进制数据形式存入audio_data                              
        audio_data = recognizer.record(source)                                         
        # 使用Whisper进行语音识别,把语音转成文字  language="zh"表示识别中文语音
        text = recognizer.recognize_whisper(audio_data, language="zh")
        text_simplified = convert_to_simplified(text)
    return text_simplified


def pdf_to_str(pdf_file):
    """从PDF文件中提取文本内容"""
    import PyPDF2
    # PDF解析库   
    reader = PyPDF2.PdfReader(pdf_file)                                                # 创建PDF读取器
    text = ""
    #reader.pages：返回PDF文件的所有页面对象
    for page in reader.pages:
        # 遍历每一页 extract_text()方法从当前页面提取文本内容
        #page.extract_text()：从当前页面提取文本内容
        text += page.extract_text()                                                    # 提取文本
    return text


def docx_to_str(file_path):
    """从DOCX文件中提取文本内容"""
    from docx import Document                                                             # DOCX文档处理
    doc = Document(file_path)                                                          # 打开DOCX文档
    text = []
    for paragraph in doc.paragraphs:                                                   # 遍历每个段落
        text.append(paragraph.text)                                                     # 收集段落文本
    return "\n".join(text)                                                             # 拼接为完整文本


def text_file_to_str(text_file):
    """从文本文件中提取内容（自动检测编码）"""
    # 字符编码检测库
    import chardet                                                                        
    with open(text_file, "rb") as file:
        raw_data = file.read() # 读取原始字节
        # 检测编码格式  返回一个字典，包含编码类型和置信度信息
        result = chardet.detect(raw_data)                                               
        encoding = result["encoding"]

    # 使用检测到的编码读取文件
    with open(text_file, "r", encoding=encoding) as file:
        return file.read()


def image_to_base64(image_path):
    import base64  # Base64编码模块，用于图片处理

    """将图片文件转换为Base64编码字符串"""
    with open(image_path, "rb") as image_file:
        #base64.b64encode()方法将二进制数据编码为Base64字符串
        #就是将二进制字节转换成base64格式的字节
        # .decode()方法将Base64字节通过UTF-8编码转换成Base64字符串
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        return encoded_string
# # 传入的是网络收到的 Base64 字符串
# # 第一步先 encode 转回 Base64 字节
# b64_byte_data = base64_str.encode("utf-8")
# # 第二步 b64decode 把 Base64 字节还原成图片原始二进制
# origin_image_bytes = base64.b64decode(b64_byte_data)

# 核心函数：文本模式下处理用户输入
def grodio_view(chatbot, chat_input):

    # 用户消息立即显示到界面
    user_message = chat_input["text"]                                                   # 获取用户文本输入
    bot_response = "loading..."                                                         # 临时显示loading
    chatbot.append([user_message, bot_response])                                        # 添加到对话历史
    yield chatbot                                                                       # 立即更新界面

    # 处理用户上传的文件，按类型分类
    files = chat_input["files"]                                                         # 获取上传文件列表
    audios = []                                                                         # 音频文件列表
    images = []                                                                         # 图片文件列表
    pdfs = []                                                                           # PDF文件列表
    docxs = []                                                                          # DOCX文件列表
    texts = []                                                                          # 文本文件列表

    # 遍历文件，根据MIME类型分类
    for file in files:
        import mimetypes                                                                      # MIME类型识别
#mimetypes.guess_type(file)：根据文件路径猜文件类型，返回文件类型和编码信息
#比如，.png返回image/png；.mp3返回audio/mpeg；.pdf返回application/pdf；.txt返回text/plain；
# .docx返回application/vnd.openxmlformats-officedocument.wordprocessingml.document；
        file_type, _ = mimetypes.guess_type(file)                                        # 识别文件类型
        if file_type.startswith("audio/"):
            audios.append(file)
        elif file_type.startswith("image/"):
            images.append(file)
        elif file_type.startswith("application/pdf"):
            pdfs.append(file)
        elif file_type.startswith(
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        ):
            docxs.append(file)
        elif file_type.startswith("text/"):
            texts.append(file)
        else:
            user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'该文件为不支持的文件类型'"
            print(f"Unknown file type: {file_type}")

    # 图片文件处理：转换为Base64并显示到界面
    if images != []:
        image_url = images
        image_base64 = [image_to_base64(image) for image in image_url]

        for i, image in enumerate(image_base64):
            chatbot[-1][0] += f"""
                <div>
                    <img src="data:image/png;base64,{image}" alt="Generated Image" style="max-width: 100%; height: auto; cursor: pointer;" />
                </div>
                """
            yield chatbot                                                              # 实时更新界面
    else:
        image_url = None

    # 解析问题类型（意图识别）
    question_type = parse_question(user_message, image_url)
    from icecream import ic #ic自动打印变量值 
# file_path = "报告.pdf"   ic(file_path)   输出：ic| test.py:12 - file_path: '报告.pdf'

    ic(question_type)                                                                  # 调试输出

    # 音频文件处理：转换为文本
    if audios != []:
        for i, audio in enumerate(audios):
            audio_message = audio_to_text(audio)
            if audio_message == "":
                user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'音频识别失败，请稍后再试'"
            elif "作曲" in audio_message:
                user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'不好意思，我无法理解音乐'"
            else:
                user_message += f"音频{i+1}内容：{audio_message}"

    # PDF文件处理：提取文本
    if pdfs != []:
        for i, pdf in enumerate(pdfs):
            pdf_text = pdf_to_str(pdf)
            user_message += f"PDF{i+1}内容：{pdf_text}"

    # DOCX文件处理：提取文本
    if docxs != []:
        for i, docx in enumerate(docxs):
            docx_text = docx_to_str(docx)
            user_message += f"DOCX{i+1}内容：{docx_text}"

    # 文本文件处理：提取内容
    if texts != []:
        for i, text in enumerate(texts):
            text_string = text_file_to_str(text)
            user_message += f"文本{i+1}内容：{text_string}"

    if user_message == "":
        user_message = "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'请问您有什么想了解的，我将尽力为您服务'"
    answer = get_answer(user_message, chatbot, question_type, image_url)
    #chatbot格式：[用户消息, 机器人消息]
    bot_response = ""

    # 处理文本生成/其他/文档检索/知识图谱检索
    if (
        answer[1] == userPurposeType.text
        or answer[1] == userPurposeType.RAG
        or answer[1] == userPurposeType.KnowledgeGraph
    ):
        # 流式输出   response[大模型返回的对象1，大模型返回的对象2]
        #         chunk = {
        #     "id": "chatcmpl-xxxxxx",
        #     "object": "chat.completion.chunk",  # 标识：流式分片
        #     "created": 1718300000,
        #     "model": "xxx-model",
        #     "choices": [
        #         {
        #             "delta": {          # 流式增量字段，核心！
        #                 "role": "assistant",
        #                 "content": "单段文字片段"  # 本次返回的文本
        #             },
        #             "index": 0,
        #             "finish_reason": None  # 结束标记，最后一块为 stop
        #         }
        #     ],
        #     "usage": None
        # }
        for chunk in answer[0]:
            bot_response = bot_response + (chunk.choices[0].delta.content or "")
            chatbot[-1][1] = bot_response
            yield chatbot

    # 处理图片生成
    if answer[1] == userPurposeType.ImageGeneration:
        image_url = answer[0]
        describe = process_image_describe_tool(
            question_type=userPurposeType.ImageDescribe,
            question="描述这个图片，不要识别‘AI生成’",
            history="",
            image_url=[image_url],
        )
        #combined_message:合并图片和描述
        combined_message = f"""
            **生成的图片:**
            ![Generated Image]({image_url})
            {describe[0]}
            """
        chatbot[-1][1] = combined_message
        yield chatbot

    # 处理图片生成
    if answer[1] == userPurposeType.ImageGeneration:
        generation=process_images_tool(
            question_type=userPurposeType.ImageGeneration,
            question="请生成一张金毛和波斯猫打架的图片",
            history="",
            image_url=[],
        )
        image_url = generation[0]
        chatbot[-1][1] = image_url
        yield chatbot
        # for i in range(0, len(answer[0]), 1):
        #     bot_response += answer[0][i : i + 1]  # 累加当前chunk到combined_message
        #     chatbot[-1][1] = bot_response  # 更新chatbot对话中的最后一条消息
        #     yield chatbot  # 实时输出当前累积的对话内容

    # 处理视频
    if answer[1] == userPurposeType.Video:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0][0]
        else:
            chatbot[-1][1] = "抱歉，视频生成失败，请稍后再试"
        yield chatbot

    # 处理PPT
    if answer[1] == userPurposeType.PPT:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0][0]
        else:
            chatbot[-1][1] = "抱歉，PPT生成失败，请稍后再试"
        yield chatbot

    # 处理Docx
    if answer[1] == userPurposeType.Docx:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0][0]
        else:
            chatbot[-1][1] = "抱歉，文档生成失败，请稍后再试"
        yield chatbot

    # 处理音频生成
    if answer[1] == userPurposeType.Audio:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0][0]
        else:
            chatbot[-1][1] = "抱歉，音频生成失败，请稍后再试"
        yield chatbot

    # 处理联网搜索
    if answer[1] == userPurposeType.InternetSearch:
        if answer[3] == False:
            output_message = (
                "由于网络问题，访问互联网失败，下面由我根据现有知识给出回答："
            )
        else:
            #links搜集到的 {链接: 标题} 字典（links）
            #             {
            #     "https://example1.com": "Python入门教程",
            #     "https://example2.com": "Python实战技巧",
            #     "https://example3.com": "Python常见问题"
            # }
            # 将字典中的内容转换为 Markdown 格式的链接
            links = "\n".join(f"[{title}]({link})" for link, title in answer[2].items())
            links += "\n"
            output_message = f"参考资料：{links}"
        for i in range(0, len(output_message)):
            bot_response = output_message[: i + 1]
            # i=0 → [:1] → "参"
            # i=1 → [:2] → "参考"
            # i=2 → [:3] → "参考资"
            # ...
            # i=7 → [:8] → "参考资料：abc
            # 实现一个逐字打字机的效果
            chatbot[-1][1] = bot_response
            yield chatbot
        # 再流式显示回答内容
        for chunk in answer[0]:
            bot_response = bot_response + (chunk.choices[0].delta.content or "")
            chatbot[-1][1] = bot_response
            yield chatbot


# 语音模式下处理用户输入
def gradio_audio_view(chatbot, audio_input):

    # 用户消息立即显示
    if audio_input is None:
        user_message = ""
    else:
        user_message = (audio_input, "audio")                                           # 标记为音频输入
    bot_response = "loading..."
    chatbot.append([user_message, bot_response])
    yield chatbot

    # 将音频转换为文本
    if audio_input is None:
        audio_message = "无音频"
    else:
        audio_message = audio_to_text(audio_input)

    chatbot[-1][0] = audio_message                                                     # 更新显示识别结果

    # 处理音频识别结果
    user_message = ""
    if audio_message == "无音频":
        user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'欢迎与我对话，我将用语音回答您'"
    elif audio_message == "":
        user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'音频识别失败，请稍后再试'"
    elif "作曲 作曲" in audio_message:
        user_message += "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'不好意思，我无法理解音乐'"
    else:
        user_message += audio_message

    # 默认提示
    if user_message == "":
        user_message = "请你将下面的句子修饰后输出，不要包含额外的文字，句子:'请问您有什么想了解的，我将尽力为您服务'"

    # 解析问题类型
    question_type = parse_question(user_message)
    ic(question_type)
    answer = get_answer(user_message, chatbot, question_type)
    bot_response = ""

    # 处理文本生成/其他/文档检索/知识图谱检索（语音输出）
    if (
        answer[1] == userPurposeType.text
        or answer[1] == userPurposeType.RAG
        or answer[1] == userPurposeType.KnowledgeGraph
    ):
        # 先收集完整文本
        for chunk in answer[0]:
            chunk_content = chunk.choices[0].delta.content or ""
            bot_response += chunk_content

        # 尝试转换为语音输出
        try:
            chatbot[-1][1] = (
                audio_generate(
                    text=bot_response,
                    model_name="zh-CN-YunxiNeural",                                     # 云希中文女声
                ),
                "audio",
            )
        except Exception as e:
            print(f"音频生成失败，直接返回文本: {str(e)}")
            chatbot[-1][1] = bot_response
            
        yield chatbot

    # 处理图片生成（语音模式下也显示图片）
    if answer[1] == userPurposeType.ImageGeneration:
        image_url = answer[0]
        describe = process_image_describe_tool(
            question_type=userPurposeType.ImageDescribe,
            question="描述这个图片，不要识别‘AI生成’",
            history=" ",
            image_url=[image_url],
        )
        combined_message = f"""
            **生成的图片:**
            ![Generated Image]({image_url})
            {describe[0]}
            """
        chatbot[-1][1] = combined_message
        yield chatbot

    # 处理视频生成失败（语音提示）
    if answer[1] == userPurposeType.Video:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0]
        else:
            try:
                chatbot[-1][1] = (
                    audio_generate(
                        text="抱歉，视频生成失败，请稍后再试",
                        model_name="zh-CN-YunxiNeural",
                    ),
                    "audio",
                )
            except Exception as e:
                chatbot[-1][1] = "抱歉，视频生成失败，请稍后再试"
        yield chatbot

    # 处理PPT生成失败（语音提示）
    if answer[1] == userPurposeType.PPT:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0]
        else:
            try:
                chatbot[-1][1] = (
                    audio_generate(
                        text="抱歉，PPT生成失败，请稍后再试",
                        model_name="zh-CN-YunxiNeural",
                    ),
                    "audio",
                )
            except Exception as e:
                chatbot[-1][1] = "抱歉，PPT生成失败，请稍后再试"
        yield chatbot

    # 处理Docx生成失败（语音提示）
    if answer[1] == userPurposeType.Docx:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0]
        else:
            try:
                chatbot[-1][1] = (
                    audio_generate(
                        text="抱歉，文档生成失败，请稍后再试",
                        model_name="zh-CN-YunxiNeural",
                    ),
                    "audio",
                )
            except Exception as e:
                chatbot[-1][1] = "抱歉，文档生成失败，请稍后再试"
        yield chatbot

    # 处理音频生成失败（语音提示）
    if answer[1] == userPurposeType.Audio:
        if answer[0] is not None:
            chatbot[-1][1] = answer[0]
        else:
            try:
                chatbot[-1][1] = (
                    audio_generate(
                        text="抱歉，音频生成失败，请稍后再试",
                        model_name="zh-CN-YunxiNeural",
                    ),
                    "audio",
                )
            except Exception as e:
                chatbot[-1][1] = "抱歉，音频生成失败，请稍后再试"
        yield chatbot

    # 处理联网搜索（语音输出）
    if answer[1] == userPurposeType.InternetSearch:
        if answer[3] == False:
            bot_response = (
                "由于网络问题，访问互联网失败，下面由我根据现有知识给出回答："
            )
        # 收集完整回答文本
        for chunk in answer[0]:
            chunk_content = chunk.choices[0].delta.content or ""
            bot_response += chunk_content

        # 转换为语音
        try:
            chatbot[-1][1] = (
                audio_generate(
                    text=bot_response,
                    model_name="zh-CN-YunxiNeural",
                ),
                "audio",
            )
        except Exception as e:
            print(f"音频生成失败，直接返回文本: {str(e)}")
            chatbot[-1][1] = bot_response
        yield chatbot


import gradio as gr
# 切换到语音模式的函数
def toggle_voice_mode():
    return (
        #gr.update是更新组件的可见性
        gr.update(visible=False),   # 隐藏文本输入框
        gr.update(visible=True),    # 显示音频输入框
        gr.update(visible=False),   # 隐藏语音模式按钮
        gr.update(visible=True),    # 显示文本模式按钮
        gr.update(visible=True),    # 显示发送按钮
    )


# 切换回文本模式的函数
def toggle_text_mode():
    return (
        gr.update(visible=True),    # 显示文本输入框
        gr.update(visible=False),   # 隐藏音频输入框
        gr.update(visible=True),    # 显示语音模式按钮
        gr.update(visible=False),   # 隐藏文本模式按钮
        gr.update(visible=False),   # 隐藏发送按钮
    )


# 示例问题列表（供用户快速选择）
examples = [
    {"text": "您好", "files": []},
    {"text": "糖尿病的常见症状有哪些？", "files": []},
    {"text": "用语音重新回答我一次", "files": []},
    {"text": "帮我搜索一下养生知识", "files": []},
    {"text": "帮我生成一张老人练太极图片", "files": []},
    {
        "text": "帮我生成一份用于科普糖尿病发病原因，症状，治疗药物，预防措施的PPT",
        "files": [],
    },
    {"text": "请根据我给的参考资料，给我一个合理的饮食建议", "files": []},
    {"text": "请根据我给的参考资料，生成一个用于科普合理膳食的word", "files": []},
    {"text": "我最近想打太极养生，帮我生成一段老人打太极的视频吧", "files": []},
    {"text": "根据我的病历，给我一个合理的治疗方案", "files": []},
    {"text": "根据知识库介绍一下常见疾病", "files": []},
    {"text": "根据知识图谱告诉我糖尿病人适合吃的食物有哪些？", "files": []},
]


# 构建 Gradio 界面
with gr.Blocks() as demo:
    # 标题和描述
    gr.Markdown("# 「赛博华佗」🩺")

    # 创建聊天布局
    with gr.Row():
        with gr.Column(scale=10):
            #gr.Chatbot是创建聊天机器人组件的函数，聊天对话框
            chatbot = gr.Chatbot(
                height=600,#聊天框高度
                avatar_images=AVATAR,# 设置头像
                show_copy_button=True, # 每条消息右侧显示复制按钮
                latex_delimiters=[  # 支持LaTeX公式
                    {"left": "\\(", "right": "\\)", "display": True},
                    {"left": "\\[", "right": "\\]", "display": True},
                    {"left": "$$", "right": "$$", "display": True},
                    {"left": "$", "right": "$", "display": True},
                ],
                # 消息占位符，聊天框空白时的提示文案
                placeholder="\n## 欢迎与我对话 \n————本项目开源地址https://github.com/Warma10032/cyber-doctor",
            )

    # 输入区域布局
    with gr.Row():#gr.Row是创建行布局的函数，用于组织组件
        with gr.Column(scale=9):#gr.Column是创建列布局的函数，用于组织组件 scale是列的宽度比例
            #gr.MultimodalTextbox是创建多模态输入框的函数，支持文本和文件上传。图片等上传
            chat_input = gr.MultimodalTextbox(                                           # 多模态输入框
                interactive=True, # 交互式输入
                file_count="multiple", # 支持多文件上传
                placeholder="输入消息或上传文件...",
                show_label=False, # 不显示标签
            )
            #gr.Audio是创建音频输入组件的函数，支持麦克风和文件上传
            audio_input = gr.Audio(                                                     # 音频输入组件
                sources=["microphone", "upload"], # 麦克风和文件上传
                label="录音输入",# 标签
                visible=False ,# 默认隐藏
                type="filepath", # 返回音频文件路径
            )
        with gr.Column(scale=1):
            #gr.ClearButton是创建清除按钮组件的函数，点击后清除聊天记录，文本输入框，音频输入框的内容
            clear = gr.ClearButton([chatbot, chat_input, audio_input], value="清除记录") # 清除按钮
            toggle_voice_button = gr.Button("语音对话模式", visible=True)                 # 语音模式切换按钮
            toggle_text_button = gr.Button("文本交流模式", visible=False)                 # 文本模式切换按钮
            submit_audio_button = gr.Button("发送", visible=False)                        # 音频发送按钮

    # 示例问题展示
    with gr.Row() as example_row:
        #gr.Examples是创建示例组件的函数，展示示问题列表
        example_component = gr.Examples(

            examples=examples, inputs=chat_input, visible=True, examples_per_page=15
        )

    # 事件绑定：文本输入提交，触发grodio_view函数处理 chat.input表示文本输入框的内容 submit表示提交按钮
    chat_input.submit(fn=grodio_view, inputs=[chatbot, chat_input], outputs=[chatbot])

    # 事件绑定：切换到语音模式 ，触发toggle_voice_mode函数处理 click表示点击事件绑定(鼠标点击
    toggle_voice_button.click(
        fn=toggle_voice_mode,
        inputs=None,
        outputs=[
            chat_input,
            audio_input,
            toggle_voice_button,
            toggle_text_button,
            submit_audio_button,
        ],
    )

    # 事件绑定：切换到文本模式 ，触发toggle_text_mode函数处理
    toggle_text_button.click(
        fn=toggle_text_mode,
        inputs=None,
        outputs=[
            chat_input,
            audio_input,
            toggle_voice_button,
            toggle_text_button,
            submit_audio_button,
        ],
    )
    #click表示点击事件绑定 inputs输出参数 outputs输出参数
    # 事件绑定：音频发送，触发gradio_audio_view函数处理
    submit_audio_button.click(
        fn=gradio_audio_view, inputs=[chatbot, audio_input], outputs=[chatbot]
    )


# 启动应用函数
def start_gradio():
    demo.launch(server_port=10032, share=False)                                          # 端口10032，不共享


# 程序入口
if __name__ == "__main__":
    start_gradio()