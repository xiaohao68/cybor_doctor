'''调用model/Internet中的接口，检索搜索到的资料'''
from typing import List,Tuple
from langchain_core.documents import Document
from model.Internet.Internet_service import search_web

def fetch_web_docs(question:str)->Tuple[List[Document],str]:
    docs = search_web(question) # 这里的到的是文件
    _context = join_docs(docs) # 这里处理成文本
    print(_context)
    return (docs,_context)

def join_docs(docs:List[Document]):
    return "\n-------------分割线--------------\n".join(doc.page_content for doc in docs)
