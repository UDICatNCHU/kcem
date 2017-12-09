# -*- coding: utf-8 -*-
import requests, os.path, threading, multiprocessing, pymongo, logging, sys, subprocess
from bs4 import BeautifulSoup
from collections import defaultdict
from opencc import OpenCC

# develop = True
develop = False
if develop:
    database = 'test'
else:
    database = 'nlp'

class WikiCrawler(object):
    """docstring for WikiCrawler"""
    def __init__(self):
        self.logName = 'WikiCrawler.log'
        logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO, filename=self.logName)
        self.openCC = OpenCC('s2t')
        self.wikiBaseUrl = 'https://zh.wikipedia.org'
        self.client = pymongo.MongoClient(None)[database]
        self.Collect = self.client['wiki']
        self.reverseCollect = self.client['wikiReverse']
        self.queueLock = threading.Lock()
        self.visited, self.stack = set(), []
            
    def crawl(self, root):
        # 為了避免stack一開始就太空導致沒有工作做，先把stack塞多點工作
        self.dfs(root)
        self.dfs(self.stack.pop(0))
        self.dfs(self.stack.pop(0))
        self.dfs(self.stack.pop(0))
        self.dfs(self.stack.pop(0))

        self.thread_init()


    def thread_init(self):
        workers = [threading.Thread(target=self.thread_dfs, name=str(i)) for i in range(multiprocessing.cpu_count())]

        for thread in workers:
           thread.start()
        # Wait for all threads to complete
        for thread in workers:
            thread.join()
        logging.info('finish init')

    def thread_dfs(self):
        while True:
            try:
                self.queueLock.acquire()
                if self.stack:
                    parent = self.stack.pop()
                    self.queueLock.release()
                else:
                    self.queueLock.release()
                    logging.info("stack is empty!!")
                    break
                self.dfs(parent)
            except Exception as e:
                self.queueLock.acquire()
                self.stack.append(parent)
                self.queueLock.release()
                logging.info('{} has occured an Exception'.format(parent))
                logging.info(e)
                raise e
        logging.info("finish thread job") 

    @staticmethod
    def genUrl(category):
        return 'https://zh.wikipedia.org/zh-tw/Category:' + category

    def dfs(self, parent):
        result = defaultdict(dict)

        res = requests.get(self.genUrl(parent)).text
        res = BeautifulSoup(res, 'lxml')

        def push_2_stack(tradText):
            if tradText not in self.visited and True not in {i in tradText for i in ('維基人', '维基人', '總類模板', '维基百科', '維基百科')}:
                self.stack.append(tradText)

        def node():
            # node
            nonlocal result

            # 代表這是一個重導向的頁面
            # 需要特殊邏輯去爬
            # e.q. https://zh.wikipedia.org/zh-tw/Category:馬爾維納斯羣島
            redirect = res.select('#SoftRedirect a')
            if redirect:
                childNode = redirect[0].text.replace('Category:', '')
                result[parent].setdefault('node', []).append(childNode)
                push_2_stack(childNode)
                return

            for childNode in res.select('.CategoryTreeLabelCategory'):
                tradText = childNode.text
                
                # build dictionary
                result[parent].setdefault('node', []).append(tradText)

                # if it's a node hasn't been through
                # append these res to stack
                push_2_stack(tradText)

        def leafNode():
            nonlocal result
            # leafNode (要注意wiki的leafNode有下一頁的連結，都要traverse完)
            leafNodeList = [res.select('#mw-pages a')]
            while leafNodeList:
                current = leafNodeList.pop(0)

                # notyet 變數的意思是，因為wiki會有兩個下一頁的超連結
                # 頂部跟底部
                # 所以如果把頂部的bs4結果append到leafNodeLIst的話
                # 底部就不用重複加
                notyet = True
                for child in current:
                    tradChild = child.text
                    if notyet and tradChild in ('下一頁', '下一页') and child.has_attr('href'):
                        notyet = False
                        leafNodeList.append(BeautifulSoup(requests.get(self.wikiBaseUrl + child['href']).text, 'lxml').select('#mw-pages a'))
                    else:
                        if tradChild not in ['下一頁', '上一頁', '下一页', '上一页']:
                            result[parent].setdefault('leafNode', []).append(tradChild)
            # insert
            result = [dict({'key':key}, **value) for key, value in result.items()]

        def grandParent():
            nonlocal result
            # GrandParent Node
            # 每個頁面的最底下都會說他們parent category是什麼
            # 也把它爬其來避免爬蟲有時候因為網路錯誤而漏掉
            if not result:
                result = [{'key': parent, 'leafNode':[parent]}]

            for grandParent in res.select('#mw-normal-catlinks li a'):
                # 空的頁面，啥都沒有...
                # 這個時候就直接幫他把自己當作leafNode結束這個分支吧
                # e.q. https://zh.wikipedia.org/zh-tw/Category:特色級時間條目
                result.append({'key':grandParent.text, 'node':[parent]}) 
            if not res.select('#mw-normal-catlinks li a'):
                logging.error("no grand parent: {}".format(self.genUrl(parent)))

        node()
        leafNode()
        grandParent()
        
        if result:
            # [BUG] pymongo.errors.DocumentTooLarge: BSON document too large (39247368 bytes) - the connected server supports BSON document sizes up to 16777216 bytes.
            # 會噴錯的都是大陸省份奇怪的資料，不處理並不影響效能
            self.Collect.insert(result)
        else:
            logging.error("no result: {}".format(self.genUrl(parent)))
        self.visited.add(parent)
        logging.info('now is at {} url:{} result:{}'.format(parent, self.genUrl(parent), result))


    def checkMissing(self):
        self.visited = set()
        while True:
            self.stack = []

            # 把WikiCrawler.log裏面發生error的頁面都再爬過一遍
            # 出錯的原因千百種，許多原因不明，那些頁面都是正常的wiki頁面
            # 少部份是因為該wiki為特殊頁面，如重導向頁面、圖片檔庫存頁等等，導致爬蟲邏輯並不適用
            self.grepErrorFromLog()

            # 把mongo所有點都看過，如果有一個名詞出現在node陣列中，但是在wiki裏面卻查不到該名詞，代表dfs因為不知名原因沒有繼續鑽進去爬，所以現在挑錯就把他挑出來，繼續爬
            for index, child in enumerate(self.Collect.find({}, {'_id':False})):
                self.visited.add(child['key'])
                if 'node' in child:
                    for node in child["node"]:
                        if not self.Collect.find({'key':node}).limit(1).count():
                            self.stack.append(node)

            if not self.stack:
                # 經過再三檢查，確定沒有漏掉的node沒有繼續dfs進去後，就可以結束了
                break
            logging.info('miss : {}'.format(str(len(self.stack) / index)))
            # 把以前沒爬到的都放進stack中之後就起動thread去爬吧
            self.thread_init()

    def grepErrorFromLog(self):
        with open(self.logName, 'r') as f:
            result = set()
            for i in f:
                if ': ERROR :' in i:
                    if 'no grand parent: ' in i:
                        url = i.split('no grand parent: ')[1]
                    else:
                        url = i.split('no result: ')[1]
                    url = ''.join(url.rsplit('\n', 1))
                    parent = url.rsplit(':', 1)[-1]
                    result.add(parent)

        self.stack.extend(result)
        # emtpy log file
        open(self.logName, 'w').close()

    def mergeMongo(self):
        # merge Collect
        result = defaultdict(dict)
        for term in self.Collect.find({}, {'_id':False}):
            for key, value in term.items():
                if key != 'key':
                    result[self.openCC.convert(term['key']).lower()].setdefault(key, set()).update({self.openCC.convert(i).lower() for i in value})

        insertList = []
        for key, value in result.items():
            for k, s in value.items():
                value[k] = list(s)
            insertList.append(dict({'key':key}, **value))
        self.Collect.remove({})
        self.Collect.insert(insertList)
        self.Collect.create_index([("key", pymongo.HASHED)])

        logging.info("merge done")

        self.buildInvertedIndex()

    def buildInvertedIndex(self):
        # build reverseCollect
        reverseResult = defaultdict(dict)
        for parent in self.Collect.find({}, {'_id':False}):
            for leafNode in parent.get('leafNode', []):
                reverseResult[leafNode].setdefault('ParentOfLeafNode', []).append(parent['key'])
            for node in parent.get('node', []):
                reverseResult[node].setdefault('parentNode', []).append(parent['key'])
        reverseResult = [dict({'key':key}, **value) for key, value in reverseResult.items()]
        self.reverseCollect.remove({})
        self.reverseCollect.insert(reverseResult)
        logging.info("buildInvertedIndex done")


    def CrawlFromDumpData(self):
        subprocess.call(['wget', 'https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles.xml.bz2'])

if __name__ == '__main__':
    import argparse
    """The main routine."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
        build kcm model and insert it into mongoDB with command line.    
    ''')
    parser.add_argument('-crawl', metavar='mode of crawler', help='mode of crawler', type=bool)
    parser.add_argument('-fix', metavar='fix missing node', help='fix missing node', type=bool)
    args = parser.parse_args()
    wiki = WikiCrawler()
    if args.crawl:
        # wiki.crawl('特色級時間條目')
        # wiki.crawl('頁面分類')
        # wiki.crawl('中式麵條')
        # wiki.crawl('各国动画师')
        # wiki.crawl('中央大学校友')
        # wiki.crawl('日本動畫師')
        # wiki.crawl('媒體')
        wiki.crawl('日本電視動畫')
        # wiki.crawl('喜欢名侦探柯南的维基人')
        # wiki.crawl('日本原創電視動畫')
        # wiki.crawl('富士電視台動畫')
        # wiki.crawl('萌擬人化')
        wiki.checkMissing()
        wiki.mergeMongo()
    elif args.fix:
        wiki.checkMissing()
        wiki.mergeMongo()