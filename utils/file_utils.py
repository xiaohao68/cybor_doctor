'''文件处理工具函数 - 用于处理上传的文件'''
import os                                                         # 操作系统接口
import shutil                                                     # 文件操作工具

from env import app_root                                          # 获取应用根目录

# 支持的文件类型及其对应的处理方式
supported_types = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "doc": "application/msword",
    "txt": "text/plain",
    "md": "text/markdown",
}

# 文件上传目录
upload_dir = os.path.join(app_root(), "data/upload")

# 确保上传目录存在
if not os.path.exists(upload_dir):
    os.makedirs(upload_dir)


def clear_old_uploads(older_than_hours: int = 24):
    """
    清理过期的上传文件
    
    参数:
        older_than_hours: 过期时间（小时），默认为24小时
    """
    import time
    
    now = time.time()
    cutoff_time = now - (older_than_hours * 3600)  # 转换为秒
    
    if not os.path.exists(upload_dir):
        return
    
    for filename in os.listdir(upload_dir):
        file_path = os.path.join(upload_dir, filename)
        try:
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    os.remove(file_path)
                    print(f"已删除过期文件：{filename}")
        except Exception as e:
            print(f"删除文件失败 {filename}: {str(e)}")


def file_ext(file_name: str) -> str:
    """
    获取文件扩展名（不含点）
    
    参数:
        file_name: 文件名
    
    返回:
        str: 扩展名（小写）
    """
    _, ext = os.path.splitext(file_name)
    return ext[1:].lower() if ext else ""


def is_supported(file_name: str) -> bool:
    """
    检查文件是否支持处理
    
    参数:
        file_name: 文件名
    
    返回:
        bool: 是否支持
    """
    ext = file_ext(file_name)
    return ext in supported_types


def mime_type(file_name: str) -> str | None:
    """
    获取文件的MIME类型
    
    参数:
        file_name: 文件名
    
    返回:
        str | None: MIME类型
    """
    ext = file_ext(file_name)
    return supported_types.get(ext)


def save_upload(file_obj, file_name: str) -> str:
    """
    保存上传的文件到本地
    
    参数:
        file_obj: 文件对象（如Gradio的FileData）
        file_name: 原始文件名
    
    返回:
        str: 保存后的文件路径
    """
    # 生成保存路径
    save_path = os.path.join(upload_dir, file_name)
    
    # 如果文件已存在，添加时间戳避免覆盖
    counter = 1
    while os.path.exists(save_path):
        name, ext = os.path.splitext(file_name)
        save_path = os.path.join(upload_dir, f"{name}_{counter}{ext}")
        counter += 1
    
    try:
        # 保存文件
        if hasattr(file_obj, 'name'):
            # 如果是文件路径
            shutil.copy(file_obj.name, save_path)
        elif hasattr(file_obj, 'read'):
            # 如果是文件对象
            with open(save_path, 'wb') as f:
                f.write(file_obj.read())
        elif hasattr(file_obj, 'path'):
            # 如果是Gradio的FileData对象
            shutil.copy(file_obj.path, save_path)
        
        return save_path
    except Exception as e:
        raise ValueError(f"文件保存失败：{str(e)}")
