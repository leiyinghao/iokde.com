from bs4 import BeautifulSoup

# 假设 a.html 是你想要读取的本地文件
with open("a.html", "r", encoding="utf-8") as file:
    content = file.read()

# 使用BeautifulSoup解析HTML内容
soup = BeautifulSoup(content, "lxml")

# 查找所有ul下的li元素
lis = soup.find_all("ul", recursive=False)  # 避免递归查找，直接找顶级的ul
links_and_dates = []

for ul in lis:
    for li in ul.find_all("li"):
        # 提取<a>标签中的href属性和文本
        link = li.a.get("href")
        text = li.a.text.strip()
        # 提取class为'date'的<span>标签中的文本
        date_span = li.find("span", class_="date")
        date_text = date_span.text.strip() if date_span else ""
        
        links_and_dates.append({"link": link, "text": text, "date": date_text})

# 打印提取的信息
for item in links_and_dates:
    print(f"Link: {item['link']}, Text: {item['text']}, Date: {item['date']}")