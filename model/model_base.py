'''枚举可能用到的模型状态'''
from enum import Enum


class base_model(object):
    def __init__(self, id=None, *args, **kwargs):
        self._model_status = model_state.failed
        self._user_id = id 
    
    @property
    def status(self):
        return self._model_status
    
    @property
    def user_id(self):
        return self._user_id
    
    # 新增修改 user_id 的函数
    def set_user(self, new_id):
        self._user_id = new_id


class model_state(str, Enum):
    
    initial = "initial"
    building = "building"
    ready = "ready"
    failed = "failed"
    invalid = "invalid"
    deleted = "deleted"
    unknown = "unknown"
