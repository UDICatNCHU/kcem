# -*- coding: utf-8 -*-
import requests, os.path, threading, multiprocessing, pymongo, logging, sys, subprocess, json_lines, os
from bs4 import BeautifulSoup
from collections import defaultdict
from opencc import OpenCC
from pyquery import PyQuery
from kcem.ignorelist import IGNORELIST
from pyquery import PyQuery as pq
from udic_nlp_API.settings_database import uri
from urllib import parse

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
        self.client = pymongo.MongoClient(uri)[database]
        self.Collect = self.client['wiki']
        self.reverseCollect = self.client['wikiReverse']
        self.queueLock = threading.Lock()
        self.visited, self.stack, self.urlStack = set(), [], []
            
    def crawl(self, root):
        self.stack.append(root)
        # 為了避免stack一開始就太空導致沒有工作做，先把stack塞多點工作
        self.dfs()
        self.dfs()
        self.dfs()
        self.dfs()
        self.dfs()

        self.thread_init(self.thread_job, self.dfs)

    def thread_init(self, thread_job, thread_func):
        logging.info("thread init start")
        workers = [threading.Thread(target=thread_job, args=(thread_func, ), name=str(i)) for i in range(multiprocessing.cpu_count())]
        for thread in workers:
           thread.start()
        # Wait for all threads to complete
        for thread in workers:
            thread.join()
        logging.info('finish init')

    def thread_job(self, thread_func):
        while True:
            # if return value of thread_func is True
            # means stack is empty.
            if thread_func():
                break
        logging.info("finish thread job") 

    @staticmethod
    def genUrl(category, disambiguation=False):
        if disambiguation:
            return 'https://zh.wikipedia.org/zh-tw/' + parse.quote(category)
        return 'https://zh.wikipedia.org/zh-tw/Category:' + parse.quote(category)

    @staticmethod
    def notInIgnore(lowerText):
        return True not in {i in lowerText for i in IGNORELIST}

    def dfs(self, parent=None, disambiguation=False):
        try:
            if not parent:
                self.queueLock.acquire()
                if self.stack:
                    parent = self.stack.pop()
                    self.queueLock.release()
                else:
                    self.queueLock.release()
                    logging.info("stack is empty!!")
                    # means the end of thread job
                    return True

            result = defaultdict(dict)
    
            res = requests.get(self.genUrl(parent)).text
            soup = BeautifulSoup(res, 'lxml')
    
            def push_2_stack(tradText):
                if tradText not in self.visited and self.notInIgnore(tradText.lower()):
                    self.stack.append(tradText)
    
            def node():
                # node
                nonlocal result
    
                # 代表這是一個重導向的頁面
                # 需要特殊邏輯去爬
                # e.q. https://zh.wikipedia.org/zh-tw/Category:馬爾維納斯羣島
                redirect = soup.select('#SoftRedirect a')
                if redirect:
                    childNode = redirect[0].text.replace('Category:', '')
                    result[parent].setdefault('node', []).append(childNode)
                    push_2_stack(childNode)
                    return

                    
    
                for childNode in soup.select('.CategoryTreeLabelCategory'):
                    tradText = parse.unquote(childNode['href'].split(':')[-1])
                    
                    # build dictionary
                    result[parent].setdefault('node', []).append(tradText)
    
                    # if it's a node hasn't been through
                    # append to stack
                    push_2_stack(tradText)
    
            def leafNode():
                def disAmb(childText):
                    disAmbResult = {'key':childText, 'leafNode':[]}
                    soup = pq(self.genUrl(childText, disambiguation=True))
                    if soup('#參考來源, #参考来源'):
                        disambiguationCandidates = soup('#參考來源, #参考来源').parent().prev_all().items()
                    elif soup('#參見, #参见'):
                        disambiguationCandidates = soup('#參見, #参见').parent().prev_all().items()
                    else:
                        disambiguationCandidates = soup('#mw-content-text a').items()
                    disambiguationCandidates = {parse.unquote(pq(j).attr('href').split('/')[-1]) for i in disambiguationCandidates for j in i('a').filter(lambda x: pq(this).attr('href') and pq(this).text() and '/wiki/' in pq(this).attr('href') and ':' not in pq(this).attr('href') and self.notInIgnore(pq(this).text().lower()))}
                    for candidate in disambiguationCandidates:
                        disAmbResult['leafNode'].append(candidate)
                    self.Collect.insert(disAmbResult)

                nonlocal result

                # leafNode (要注意wiki的leafNode有下一頁的連結，都要traverse完)
                leafNodeList = [soup.select('#mw-pages a')]
                while leafNodeList:
                    current = leafNodeList.pop(0)
    
                    # notyet 變數的意思是，因為wiki會有兩個下一頁的超連結
                    # 頂部跟底部
                    # 所以如果把頂部的bs4結果append到leafNodeLIst的話
                    # 底部就不用重複加
                    notyet = True
                    for child in current:
                        childText = parse.unquote(child['href'].split('/')[-1])
                        if self.notInIgnore(child.text.lower()) == False:continue
                        if notyet and child.text in ('下一頁', '下一页') and child.has_attr('href'):
                            notyet = False
                            leafNodeList.append(BeautifulSoup(requests.get(self.wikiBaseUrl + child['href']).text, 'lxml').select('#mw-pages a'))
                        elif child.text not in ['下一頁', '上一頁', '下一页', '上一页']:
                            print(childText)
                            result[parent].setdefault('leafNode', []).append(childText)

                            if disambiguation:
                                disAmb(childText)
                # insert
                result = [dict({'key':key}, **value) for key, value in result.items()]

            def grandParent():
                nonlocal result
                # 空的頁面，啥都沒有...
                # 這個時候就直接幫他把自己當作leafNode結束這個分支吧
                # e.q. https://zh.wikipedia.org/zh-tw/Category:特色級時間條目
                if not result:
                    result.append({'key': parent, 'leafNode':[parent]})

                # grandParent Node
                # 每個頁面的最底下都會說他們parent category是什麼
                # 也把它爬其來避免爬蟲有時候因為網路錯誤而漏掉
                parentOfNode = soup.select('#mw-normal-catlinks li a')
                if not parentOfNode:
                    logging.error("no grand parent: {}".format(self.genUrl(parent)))
                else:
                    for gdParent in parentOfNode:
                        result.append({'key':gdParent.text, 'node':[parent]})

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
        except Exception as e:
            logging.error('{} has occured an Exception. \n {}'.format(parent, e))
            raise e

    def checkMissing(self):
        def grepErrorFromLog():
            logging.info('start grepErrorFromLog')
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
            logging.info('end grepErrorFromLog')

        self.visited = set()
        while True:
            self.stack = []

            # 把WikiCrawler.log裏面發生error的頁面都再爬過一遍
            # 出錯的原因千百種，許多原因不明，那些頁面都是正常的wiki頁面
            # 少部份是因為該wiki為特殊頁面，如重導向頁面、圖片檔庫存頁等等，導致爬蟲邏輯並不適用
            grepErrorFromLog()

            # 把mongo所有點都看過，如果有一個名詞出現在node陣列中，但是在wiki裏面卻查不到該名詞，代表dfs因為不知名原因沒有繼續鑽進去爬，所以現在挑錯就把他挑出來，繼續爬
            for index, child in enumerate(self.Collect.find({}, {'_id':False}, no_cursor_timeout=True)):
                self.visited.add(child['key'])
                if 'node' in child:
                    for node in child["node"]:
                        if not self.Collect.find({'key':node}).limit(1).count():
                            self.stack.append(node)
            logging.warning('missing part is : {}'.format(self.stack))
            logging.info('miss : {}'.format(str(len(self.stack) / index)))
            if not self.stack:
                # 經過再三檢查，確定沒有漏掉的node沒有繼續dfs進去後，就可以結束了
                break
            # 把以前沒爬到的都放進stack中之後就起動thread去爬吧
            self.thread_init(self.thread_job, self.dfs)

    def mergeMongo(self):
        def buildInvertedIndex():
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
            self.reverseCollect.create_index([("key", pymongo.HASHED)])
            logging.info("buildInvertedIndex done")

        # merge Collect
        logging.info("merge begin")
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
        self.Collect.remove({'key':'分類'})
        self.Collect.create_index([("key", pymongo.HASHED)])

        logging.info("merge done")

        buildInvertedIndex()



    def CrawlFromDumpData(self):
        logging.info('start download wiki data')
        if not os.path.isfile('build/zhwiki-latest-pages-articles.xml.bz2'):
            subprocess.call(['wget', 'https://dumps.wikimedia.org/zhwiki/latest/zhwiki-latest-pages-articles.xml.bz2'])
        subprocess.call(['WikiExtractor.py', 'zhwiki-latest-pages-articles.xml.bz2', '-o', 'wikijson', '--json'])
        self.urlStack = []
        for (dir_path, dir_names, file_names) in os.walk('.'):
            if 'wikijson' in dir_path:
                for file_name in file_names:
                    with open(os.path.join(dir_path, file_name), 'r') as f:
                        for item in json_lines.reader(f):
                            self.urlStack.append(item['url'])

        def dumpDataFunc():
            try:
                self.queueLock.acquire()
                if self.urlStack:
                    url = self.urlStack.pop()
                    self.queueLock.release()
                else:
                    self.queueLock.release()
                    logging.info("urlStack is empty!!")
                    # means the end of thread job
                    return True

                soup = PyQuery(url)
                parent = soup('#firstHeading').text()
                logging.info('now dumpDataFunc is at {}, url: {} '.format(parent, url))
                result = [{'key':gdParent.text(), 'leafNode':[parent]} for gdParent in soup('#mw-normal-catlinks li a').items()]
                
                if result:
                    # [BUG] pymongo.errors.DocumentTooLarge: BSON document too large (39247368 bytes) - the connected server supports BSON document sizes up to 16777216 bytes.
                    # 會噴錯的都是大陸省份奇怪的資料，不處理並不影響效能
                    self.Collect.insert(result)
                else:
                    logging.error("no result at: {}".format(url))
            except Exception as e:
                logging.error('{} has occured an Exception. \n {}'.format(url, e))
        self.thread_init(self.thread_job, dumpDataFunc)