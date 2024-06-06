# 本文件用于将eiblog的归档内容wget保存的网页到本地解析本地HTML文件，提取文章的标题、作者、创建日期、内容等信息，并将其保存到MongoDB数据库中。
# 背景服务器被黑，mongodb 数据被清除；本脚本仅供参考，不保证可用性。

import os
import pymongo
from datetime import datetime,timezone
from bs4 import BeautifulSoup
import json
import re

class Article:
    def __init__(self, id, author, slug, title, count, content, created_at=None):
        if id is not None:
           self.id = id 
        self.author = author
        self.slug = slug
        self.title = title
        self.count = count
        self.content = content
        self.is_draft = False
        self.deleted_at = None
        self.created_at = created_at if created_at else datetime.now()
    def to_json(self):
        return json.dumps(self.__dict__)

# MongoDB 连接字符串
uri = "mongodb://127.0.0.1:27017/eiblog"
client = pymongo.MongoClient(uri)

# 获取数据库
#db = client['eiblog_physicalno']
db = client['eiblog']
# 获取集合（表）
collection = db['article']

def extract_slug_from_link(link):
    match = re.search(r'/([\w-]+)\.html$', link)
    if match:
        return match.group(1)
    else:
        return link  # 如果不匹配，返回原始的链接数据

# 调用示例
link = "post/redis-stack-with-json-set.html"
slug = extract_slug_from_link(link)
print(slug)  # 输出提取的数据


# 假设 a.html 是你想要读取的本地文件
with open("a.html", "r", encoding="utf-8") as file:
    content = file.read()

# 使用BeautifulSoup解析HTML内容
soup = BeautifulSoup(content, "lxml")

# 查找所有ul下的li元素
lis = soup.find_all("ul", recursive=True)  # 避免递归查找，直接找顶级的ul
links_and_dates = []
#将字符串(Jan 13, 2021)转换为Python的可格式化日期时间字符串
def convert_to_formatted_date(date_str):
    """
    尝试将形如'(Jan 13, 2021)'的字符串转换为'2021-01-13'格式。
    如果转换失败，则返回原始字符串。
    """
    try:
        # 去掉括号并使用strptime解析
        cleaned_date_str = date_str.strip("()")
        date_obj = datetime.strptime(cleaned_date_str, "%b %d, %Y")
        
        # 使用strftime转换为目标格式
        formatted_date_str = date_obj.strftime("%Y-%m-%d %H:%M:%S")
        return formatted_date_str
    except ValueError:
        # 如果转换失败（例如，格式不匹配），返回原始字符串
        print(f"无法转换日期: {date_str}")
        return date_str

def convert_date_string(date_str, date_format):
    """
    将日期字符串根据指定的格式转换为datetime对象。
    
    参数:
    - date_str: 日期字符串。
    - date_format: 日期格式字符串，如'%Y-%m-%d' / '%Y-%m-%d %H:%M:%S' 。
    
    返回:
    - datetime对象，表示解析成功的日期；如果解析失败，则返回None。
    
    异常:
    - 如果日期字符串或格式字符串无效，或者无法解析日期字符串，则会打印错误信息。
    """
    try:
        # 验证date_format的有效性
        #datetime.strptime('123', date_format)  # 尝试解析一个简单的字符串，用于隐式验证date_format是否有效

        # 尝试将date_str转换为datetime对象
        date_object = datetime.strptime(date_str, date_format)
        return date_object

    except ValueError as e:
        # 如果发生ValueError，意味着date_str或date_format无效，或者date_str不符合date_format
        print(f"错误：无法解析日期字符串'{date_str}'。请确保其符合格式'{date_format}'。")
        return None

    except Exception as e:
        # 捕获其他异常，可能与date_format有关
        print(f"发生意外错误：{e}")
        return None
    
 # 封装插入数据的函数
def insert_article(article_data):
    article_data_dict = vars(article_data)
    article_data_dict["created_at"] = convert_date_string(article_data.created_at, '%Y-%m-%d %H:%M:%S' )
    article_data_dict["deleted_at"] = datetime(1, 1, 1, 0, 0, 0) # 使用定义的最早日期作为删除时间的空值
    result = collection.insert_one(article_data_dict)

    print(f"Inserted new article: {result.inserted_id}")
   
# 测试函数
original_str = "(Jan 13, 2021)"
formatted_date = convert_to_formatted_date(original_str)
print(formatted_date)  # 应输出: 2021-01-13

# 测试不匹配格式的情况
invalid_str = "(Invalid Date, 2021)"
formatted_invalid = convert_to_formatted_date(invalid_str)
print(formatted_invalid)  # 应输出原始字符串: (Invalid Date, 2021)
for ul in lis:
    for li in ul.find_all("li"):
        # 提取<a>标签中的href属性和文本
        link = li.a.get("href")
        text = li.a.text.strip()
        # 提取class为'date'的<span>标签中的文本
        date_span = li.find("span", class_="date")
        date_text = date_span.text.strip() if date_span else ""
        date_text   = convert_to_formatted_date(date_text)
        links_and_dates.append({"link": link, "text": text, "date": date_text})

# 打印提取的信息
for item in links_and_dates:
    print(f"Link: {item['link']}, Text: {item['text']}, Date: {item['date']}")


#遍历文章列表，打开文件，提取文章内容 
def read_file_if_exists(file_path):
    if not os.path.isfile(file_path):
        print(f"文件 {file_path} 不存在，跳过.")
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            soup = BeautifulSoup(content, 'html.parser')
            #这里有个错误，我要找一个 class = entry-content 的 div ，并获取 div 下的 text 内容
            entry_content = soup.find("div", class_="entry-content")  # 查找具有'.entry-content'类的元素
            if entry_content:
                # 尝试找到"本文链接"的文本节点
                index = entry_content.text.find( "本文链接")
                if index != -1:  # 如果找到了"本文链接"
                    # 获取"本文链接"前的文本内容并去除两侧空白
                    text_before_link = entry_content.text[:index].strip()
                    return text_before_link
                else:
                    # 如果没找到"本文链接"，直接返回原有内容
                    return entry_content.get_text().strip()
            else:
                print(f"未找到 '.entry-content' 类的内容 in {file_path}")
                return None
    except Exception as e:
        print(f"读取文件 {file_path} 或提取内容时发生错误: {e}")
        return None

print("---------------------content-------------------------------------------")
#links_and_dates = links_and_dates[:1]
links_and_dates = reversed(links_and_dates)    
for id,item in enumerate(links_and_dates):
    link = item.get('link', '').strip()
    id = id +1 
    if not link:
        continue
    print(f"link is {slug}")
    #读取文章内容
    article_content = read_file_if_exists(link)
    item["content"] = article_content
    if article_content is None:
        continue
    #link 数据是"post/redis-stack-with-json-set.html" 这个格式 如何提取【redis-stack-with-json-set】 这部分数据 最好用正则表达式
    #item['date'] = ''
    slug_name= extract_slug_from_link(link)
    title = item['text']
    #create_date = convert_date_string( item['date'] , '%Y-%m-%d %H:%M:%S')
    create_date =  item['date']
    new_article = Article(id=id, author="lavin", slug=slug_name, title=title, count=0,created_at= create_date , content=article_content)
    print(f"Link: {item['link']}, Text: {item['text']}, Date: {item['date']} ")
    insert_article(new_article)
    #print(f"content {item['content']}")
    # break
    # if article_content is not None:
    #     # 在这里处理文章内容
    #     pass


 

