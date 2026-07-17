from zhipuai import ZhipuAI                                      # 智谱AI客户端
from env import env_value                                         # 环境变量获取


# 视频生成客户端实例（使用独立的API密钥）
video_gen_client = ZhipuAI(api_key=env_value("VIDEO_GENERATE_API"))

# 图片描述客户端实例（使用独立的API密钥）
image_desc_client = ZhipuAI(api_key=env_value("IMAGE_DESCRIBE_API"))

# 图片生成客户端实例（使用独立的API密钥）
image_gen_client = ZhipuAI(api_key=env_value("IMAGE_GENERATE_API"))

"""
说明：
- 本文件创建了三个专用客户端实例，分别用于不同的多模态任务
- 每个客户端使用独立的API密钥，便于权限管理和计费
- 通过环境变量配置API密钥，避免硬编码敏感信息

使用示例：
    # 图片生成
    response = image_gen_client.images.generations(
        model="cogview-3",
        prompt="一只可爱的猫咪"
    )
    
    # 图片描述
    response = image_desc_client.chat.completions.create(
        model="glm-4v",
        messages=[{"role": "user", "content": 
        [{"type": "image_url", "image_url": {"url": "base64..."}}, 
        {"type": "text", "text": "描述这张图片"}
        ]
        }]
    )
    
    # 视频生成
    response = video_gen_client.videos.generations(
        model="video-generate",
        prompt="一个美丽的日落"
    )
"""
