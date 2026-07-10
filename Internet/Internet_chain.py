from Internet.Internet_prompt import extract_question
from Internet.retrieve_Internet import retrieve_html
from client.clientfactory import Clientfactory
from env import get_app_root

import re
import os

#shutil-用于文件操作，例如删除目录、复制文件等
#threading-用于创建线程，实现并行搜索
import shutil
import threading
from typing import List



_SAVE_PATH = os.path.join(get_app_root(), "data/cache/internet")

#InternetSearchChain-互联网搜索链
def InternetSearchChain(question, history):
    if os.path.exists(_SAVE_PATH):
        shutil.rmtree(_SAVE_PATH)

    if not os.path.exists(_SAVE_PATH):
        os.makedirs(_SAVE_PATH)
#whole_question-用户提问，包含多个问题
    whole_question = extract_question(question, history)
    question_list = re.split(r"[;；]", whole_question)
#urllib3-用于处理HTTP请求和响应  disable_warnings()方法用于忽略不安全的临时请求警告
#InsecureRequestWarning-用于忽略不安全的请求警告(request默认会验证服务器的SSL证书错误)
    import requests
    from urllib3.exceptions import InsecureRequestWarning
#requests.packages表示requests库的urllib3模块，用于处理HTTP请求和响应
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    threads = []

    #links-用于存储搜索到的链接信息，键是问题，值是链接列表
    links = {}

    # 为每个问题创建单独的线程 用多线程同时搜索
    for question in question_list:
#target表示 线程要执行的函数  args表示要传给函数的参数元组 links-用于存储搜索到的链接信息
        #用必应搜索
        thread = threading.Thread(target=search_bing, args=(question, links, 3))
        threads.append(thread)
        thread.start()#启动线程
        #用百度搜索
        thread = threading.Thread(target=search_baidu, args=(question, links, 3))
        threads.append(thread)
        thread.start()#启动线程

    # 等待所有线程完成，再合并所有搜索到的链接信息
    for thread in threads:
        thread.join()

    if has_html_files(_SAVE_PATH):
        docs, _context = retrieve_html(question)
        prompt = f"根据你现有的知识，辅助以搜索到的文件资料：\n{_context}\n 回答问题：\n{question}\n 尽可能多的覆盖到文件资料"
    else:
        prompt = question

    response = Clientfactory().get_client().chat_with_ai_stream(prompt)

    return response, links, has_html_files(_SAVE_PATH)

def has_html_files(directory_path):
    if os.path.exists(directory_path):
        # 遍历目录中的文件
        for file_name in os.listdir(directory_path):
            if file_name.endswith(".html"):
                return True
        return False
    else:
        return False


def search_bing(query, links, num_results=3):

    headers = {
        #Accept-服务器返回的文件类型 text/html,application/xhtml+xml,application/xml表示HTML、XML、XML文档等
        #q表示质量因子，0.9表示优先返回HTML文件，0.8表示如果HTML文件不可用，再返回XML文件
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        #Accept-Encoding-服务器返回的压缩编码 gzip, deflate, compress
        "Accept-Encoding": "gzip, deflate, compress",
        #Cache-Control-缓存控制，max-age=0表示不缓存响应，每次请求都从服务器获取最新响应
        #keep-alive-保持连接，避免每次请求都建立新连接
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive", 
        #User-Agent-浏览器的用户代理字符串，用于标识浏览器和操作系统
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0",
    }
    search_urls = [
        f"https://cn.bing.com/search?q={query}",
        f"https://www.bing.com/search?q={query}",
    ]
    for search_url in search_urls:
        flag = 0
        # 禁用 SSL 验证的警告   verify=False 表示不验证服务器的SSL证书，直接发送请求
        response = requests.get(search_url, headers=headers, verify=False)
        #response
#bs4-用于解析HTML文档
#BeautifulSoup-用于解析HTML文档，提取标签和文本
        from bs4 import BeautifulSoup
        if response.status_code == 200:
        #解析response.text为BeautifulSoup对象，用于提取标签和文本 html.parser-默认解析器
            soup = BeautifulSoup(response.text, "html.parser")
        #soup.find_all("li", class_="b_algo")-查找所有class为b_algo的li标签，用于提取搜索结果
        #item-每个搜索结果的li标签
        #返回结果类型是BeautifulSoup对象的列表，每个元素是一个li标签[<li>xxx</li>,<li>xxx</li>,..]
            for item in soup.find_all("li", class_="b_algo"):
                if flag >= num_results:
                    break
                #提取搜索结果的标题和链接  <h2>标题内容</h2>  <a>链接1</a >
                #find("h2")-查找h2标签，用于提取标题  结果就是标题内容
                #find("a")-查找a标签，用于提取链接    结果就是链接1  
                title = item.find("h2").text
                #查找li标签内的a标签的href属性，就是链接地址字符串 "https://xxx.com/abc#detail"
                link = item.find("a")["href"].split("#")[0]  # 删除 '#' 后的部分

                try:
                    response = requests.get(link, timeout=10)
                    if response.status_code == 200:
                        filename = f"{_SAVE_PATH}/{title}.html"
                #response.text-服务器返回的HTML文档内容，比如<html>
                        # │  <body>
                        # │      <ul>
                        # │          <li class="b_algo">...</li>
                        # │          <li class="b_algo">...</li>
                        # │          <li class="b_algo">...</li>
                        # │      </ul>
                        # │  </body>
                        # │  </html>
                        if response.text is not None:
                            with open(filename, "w", encoding="utf-8") as f:
                                links[link] = title
                                f.write(response.text)
                                flag += 1
                            print(f"Downloaded and saved: {link} as {filename}")
                        else:
                            print(f"Failed to download {link}: Empty content")
                    else:
                        print(
                            f"Failed to download {link}: Status code {response.status_code}"
                        )
                except Exception as e:
                    print(f"Error downloading {link}: {e}")
            # 检查是否达到了期望的结果数
            if flag < num_results:
                print("访问bing失败，请检查网络代理")
        else:
            print("Error: ", response.status_code)


def search_baidu(query, links, num_results=3):
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, compress",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0",
    }
    search_url = f"https://www.baidu.com/s?wd={query}"  # 百度搜索URL

    flag = 0
     # 禁用 SSL 验证的警告
    response = requests.get(search_url, headers=headers, verify=False)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")

        # 百度搜索结果的条目
        for item in soup.find_all("div", class_="result"):
            if flag >= num_results:
                break
            try:
                # 获取标题和链接
                title = item.find("h3").text
                link = item.find("a")["href"].split("#")[0]  # 删除 '#' 后的部分

                response = requests.get(link, timeout=10)

                if response.status_code == 200:
                    filename = f"{_SAVE_PATH}/{title}.html"
                    if response.text is not None:
                        with open(filename, "w", encoding="utf-8") as f:
                            links[link] = title
                            f.write(response.text)
                            flag += 1
                        print(f"Downloaded and saved: {link} as {filename}")
                    else:
                        print(f"Failed to download {link}: Empty content")
                else:
                    print(
                        f"Failed to download {link}: Status code {response.status_code}"
                    )
            except Exception as e:
                print(f"Error downloading {link}: {e}")

        # 检查是否达到了期望的结果数
        if flag < num_results:
            print("访问百度失败，请检查网络代理制")
    else:
        print("Error: ", response.status_code)