from bs4 import BeautifulSoup
import requests
import sys
import os
import time

class Biquge(object):
    def __init__(self):
        self.url = self.input_url()
        self.book_title = self.input_book_title()
        self.writer = self.input_writer()
        self.path_file = self.get_path_file()
        self.req = None
        self.html = None
        self.href = []
        self.catalog = []
        self.start = 0
        self.N_total = 0


    def input_url(self):
        url = input('请输入小说的url(例如http://www.biquyun.com/0_748/)：\n')
        return url

    def input_book_title(self):
        book_title = input('请输入书名：')
        return book_title
    
    def input_writer(self):
        writer = input('请输入作者名：')
        return writer

    def get_path_file(self):
        path_file = input("输入文件存储路径，默认路径为此py文件所在文件夹：")
        if path_file == "":
            path_file = '%s' % (os.path.dirname(
                os.path.realpath(__file__)))
        return path_file

    def create_file(self):
        if os.path.exists(os.path.join(self.path_file, self.book_title + ".txt")):
            pass
        else:
            with open(os.path.join(self.path_file, self.book_title + ".txt"), 'w', encoding='utf-8') as f:
                f.write(self.book_title + '\n' + self.writer + '\n')
        print("即将下载：\n" + '书名：' + self.book_title + '\n作者名：' + self.writer)        

    def connect(self):
        print("正在连接网站")
        self.req = requests.get(url=self.url)
        self.html = BeautifulSoup(self.req.text, features="html.parser")        

    def get_text_code(self):
        # 找到html中说明的编码格式
        location = str(self.req.text).find('charset=')
        codef = str(self.req.text)[location + 8]
        if codef == 'u':
            code = 'utf-8'
        elif codef == 'G'or'g':
            code = 'GBK'
        else:
            code = input('请输入网页编码格式（例如GBK）：')  # 若没有找到编码格式
        return code

    def get_catalog(self):
        # 查找章节名，章节链接
        temp_1 = self.html.find_all('dd')
        if len(temp_1) == 0:
            temp_1 = self.html.find_all('li')
            temp_1 = temp_1[11:]
        a = BeautifulSoup(str(temp_1), features="html.parser").find_all('a')
        print("正在获取各章节网址及标题")
        for i in range(len(a)):
            temp = a[i].get('href')
            temp = temp.split('/')
            temp = temp[-1].replace('\n', '')
            self.href.append(str(self.url.replace('index.html', '') + temp))
            self.catalog.append(a[i].text)
        print('标题获取完成')        
        # 判断是否有“最新章节”，若有则手动去除重复
        self.start = input('请输入小说开始章节（即去掉开头最新章节部分，默认值为0）：')  # 过滤掉开始的重复部分
        if self.start != '':
            self.start = int(self.start)
        else:
            self.start = 0
        self.N_total = len(a) - self.start
        print('小说共%d章' % self.N_total)

    def find_continue_point(self):
        index = 0
        with open(os.path.join(self.path_file, self.book_title + ".txt"), 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for i in range(len(lines)):
                if str(lines[len(lines) - 1 - i][:3]) == "gap":
                    #print(lines[len(lines) - 1 - i][4:])
                    index = int(lines[len(lines) - 1 - i][4:])
                    break
        return index
                    
    def download(self):
        self.connect()
        code = self.get_text_code()
        self.get_catalog()
        self.create_file()
        i = self.start
        j = 0
        while i < len(self.href):
            try:
                sys.stdout.write("正在下载第%d章，已下载%.3f%%" % (i, (i - self.start + 1) * 100 / self.N_total) + '\r')
                sys.stdout.flush()
                req = requests.get(url=self.href[i])
                req.encoding = code
                html_each = BeautifulSoup(req.text, features="html.parser")
                texts_each = html_each.find_all('div', id='content')
                # 清理空格
                if len(texts_each) > 0 and texts_each[0].text[1:6] != '正在加载中':
                    # 继续上次的下载
                    index_last = self.find_continue_point()
                    if index_last != 0 and index_last > i:
                        i = index_last + 1
                    with open(os.path.join(self.path_file, self.book_title + ".txt"), 'a', encoding='utf-8') as f:
                        f.write('\n\n' + self.catalog[i] + '\n' +
                                '\n'.join(texts_each[0].text.split()))
                        f.write('\ngap:%d' % i)
                    i = i + 1
                else:  # 防止应网络不畅通造成的错误
                    j = j + 1
                    time.sleep(1)
                    if j > 30:
                        print('\n网络连接中断或网站被封，跳过此章节')
                        print(self.catalog[i])
                        print(self.href[i])
                        with open(os.path.join(self.path_file, self.book_title + ".txt"), 'a', encoding='utf-8') as f:
                            f.write('\n\n' + self.catalog[i] + '\n' + '\n网络连接中断或网站被封，跳过此章节'
                                    '\n%s' % self.href[i])
                            f.write('\ngap:%d' % i)
                        j = 0
                        i = i + 1
                    pass
            except KeyboardInterrupt:
                print('\n用户中断')
                break
            except:
                print('\n发生未知错误，跳过此章节')
                print(self.catalog[i])
                print(self.href[i])

if __name__ == "__main__":
    test = Biquge()
    test.download()
