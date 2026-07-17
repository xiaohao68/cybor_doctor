# 该函数用于对外界提供retreive服务，调用的是Internet_model 中的接口
from typing import List
from model.Internet.Internet_model import singleton
from langchain_core.documents import Document

def search_web(query:str) ->List[Document]:
    return singleton.retriever.invoke(query)
