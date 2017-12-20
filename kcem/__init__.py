# -*- coding: utf-8 -*-
import jieba, pymongo, numpy, math, pyprind
from collections import defaultdict
from ngram import NGram
from itertools import dropwhile
from functools import reduce
from udicOpenData.stopwords import rmsw
from udic_nlp_API.settings import W2VMODEL

DEBUG = True
# DEBUG = False
if DEBUG:
    import requests
else:
    from KCM.__main__ import KCM

class WikiKCEM(object):
    """docstring for WikiKCEM"""
    def __init__(self, uri=None):
        if not DEBUG:
            self.kcmObject = KCM('cht', 'cht', uri=uri)

        self.client = pymongo.MongoClient(uri)['nlp']
        self.Collect = self.client['wiki']
        self.reverseCollect = self.client['wikiReverse']
        self.kcem = self.client['kcem']
        
        self.model = W2VMODEL
        self.wikiNgram = NGram((i['key'] for i in self.reverseCollect.find({}, {'key':1, '_id':False})))
            
    @staticmethod
    def findPath(keyword):
        Collect = pymongo.MongoClient(None)['nlp']['wikiReverse']
        cursor = Collect.find({'key':keyword}).limit(1)[0]
        if 'ParentOfLeafNode' in cursor:
            cursor = cursor['ParentOfLeafNode']
        else:
            cursor = cursor['parentNode']

        queue = {(parent, (keyword, parent,)) for parent in set(cursor) - set(keyword)}

        while queue:
            (keyword, path) = queue.pop()
            cursor = Collect.find({'key':keyword}).limit(1)
            if cursor.count():
                parentNodes = cursor[0]
                parentNodes = parentNodes['parentNode']
                for parent in parentNodes:
                    if parent in path:
                        yield path[:path.index(parent) + 1]
                    else:
                        queue.add((parent, path + (parent, )))
            else:
                yield path

    def findParent(self, keyword, denominator=None):
        # if not in wiki Category
        # use wiki Ngram to search
        cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)
        if not cursor.count():
            keyword = self.wikiNgram.find(keyword)
            if keyword:
                cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)
            else:
                self.kcem.insert({'key':keyword, 'value':[]})

        kcem = self.kcem.find({'key':keyword}, {'_id':False}).limit(1)
        if kcem.count():
            return kcem[0]

        cursor = cursor[0].get('ParentOfLeafNode', []) + cursor[0].get('parentNode', [])
        candidate = {}
        for parent in cursor:
            candidate[parent] = self.toxinomic_score(keyword, parent, denominator)

        # 如果parent有多種選擇， 那就把跟keyword一模一樣的parent給剔除
        # 但是如果parent只有唯一的選擇而且跟關鍵字 一樣那就只能選他了
        if len(candidate) > 1 and keyword in candidate:
            del candidate[keyword]

        # Use Min-max normalization
        # 因為最後輸出的值為機率，而機率不能是負的
        # 所以先透過min-max轉成0~1的數值範圍
        M, m = max(candidate.items(), key=lambda x:x[1])[1], min(candidate.items(), key=lambda x:x[1])[1]
        if M == m or len(candidate) == 0:
            M, m = 1, 0

        summation = 0
        for k, v in candidate.items():
            candidate[k] = (v - m) / (M - m)
    
            # 算機率
            summation += candidate[k]

        # calculate possibility, and the sum of possibility is 1.
        if summation:
            for k, v in candidate.items():
                candidate[k] = v / summation
        # 意思：key=lambda x:(-x[1], len(x[0]))
        # 先以分數排序，若同分則優先選擇字數少的category當答案
        result = {'key':keyword, 'value':sorted(candidate.items(), key=lambda x:(-x[1], len(x[0])))}
        self.kcem.insert(result)
        return result

    def toxinomic_score(self, keyword, parent, denominator):
        jiebaCut = jieba.lcut(parent)
        def similarityScore():
            def getSimilarity(keyword, term):
                try:
                    similarity = self.model.similarity(keyword, term)
                    # sign = 1 if similarity > 0 else -1
                    # return sign * (similarity ** 2)
                    return similarity ** 2
                except KeyError as e:
                    return 0
            scoreList = [getSimilarity(keyword, term) for term in jiebaCut]
            return reduce(lambda x, y: x+y, scoreList)

        def kcmScore():
            if DEBUG:
                keywordKcm = dict(requests.get('http://140.120.13.244:10000/kcm/?keyword={}&lang=cht&num=-1'.format(keyword)).json()['value'])
            else:
                keywordKcm = dict(self.kcmObject.get(keyword, -1).get('value', []))
            if keywordKcm:
                keywordKcmTotal = sum(keywordKcm.values())
                return reduce(lambda x,y:x+y, [(keywordKcm.get(term, 0) / keywordKcmTotal)**2 for term in jiebaCut])
            else:
                return 0

        def harmonic_mean():
            cosine, kcm = similarityScore() , kcmScore()
            if cosine and kcm:
                return 2 * (cosine/len(jiebaCut) * kcm/len(jiebaCut)) / (cosine/len(jiebaCut) + kcm/len(jiebaCut))
            else:
                return 0

        if denominator:
            return (similarityScore() + kcmScore()) / denominator(jiebaCut)
        else:
            # default mode
            # return (similarityScore() + kcmScore()) / 1.17 ** len(jiebaCut)
            return harmonic_mean()

    def classify(self, file):
        import json
        kcemTable = {}
        context = ''.join(i['context'] for i in json.load(open(file, 'r')))
        result = defaultdict(list)
        # for key in rmsw(context, 'n'):
        for key in pyprind.prog_bar(list(rmsw(context, 'n'))):
            rawParent = self.findParent(key)
            parent = kcemTable.setdefault(key, rawParent['value'][0][0] if rawParent['value'] and rawParent['key'] == key else None)
            if parent:
                result[parent].append(key)
        result = {k:len(v) for k,v in result.items()}
        return sorted(result.items(), key=lambda x:-x[1])


    def loss(self):
        import json
        import numpy as np
        answer = json.load(open('answer.json', 'r'))
        power = []
        for i in np.arange(1.0, 1.5, 0.005):
            power.append(sum([dict(self.findParent(term, lambda jiebaCut:i ** len(jiebaCut))['value'])[answer[term]] for term in answer]))
        print(power)
        print('1 + lnN')
        print(sum([dict(self.findParent(term, lambda jiebaCut:len(jiebaCut) * math.log1p(len(jiebaCut)))['value'])[answer[term]] for term in answer]))
        print('1 + log10 N')
        print(sum([dict(self.findParent(term, lambda jiebaCut:1+math.log(len(jiebaCut), 10))['value'])[answer[term]] for term in answer]))
        print('1 + log2 N')
        print(sum([dict(self.findParent(term, lambda jiebaCut:1+math.log(len(jiebaCut), 2))['value'])[answer[term]] for term in answer]))
        print('N (1 + logN)')
        print(sum([dict(self.findParent(term, lambda jiebaCut: len(jiebaCut)*(1+math.log(len(jiebaCut), 2)))['value'])[answer[term]] for term in answer]))
        print('1 + NlogN')
        print(sum([dict(self.findParent(term, lambda jiebaCut:1+len(jiebaCut) * math.log(len(jiebaCut), 2))['value'])[answer[term]] for term in answer]))

        print('1 + NlogX N')
        power = []
        for i in np.arange(1.05, 10, 0.05):
            power.append(sum([dict(self.findParent(term, lambda jiebaCut:1+len(jiebaCut)*math.log(len(jiebaCut), i))['value'])[answer[term]] for term in answer]))
        print(power)

        print('N (1 + logX N)')
        power = []
        for i in np.arange(1.05, 10, 0.05):
            power.append(sum([dict(self.findParent(term, lambda jiebaCut: len(jiebaCut)*(1+math.log(len(jiebaCut), i)))['value'])[answer[term]] for term in answer]))
        print(power)


if __name__ == '__main__':
    import argparse
    """The main routine."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
        build kcm model and insert it into mongoDB with command line.    
    ''')
    parser.add_argument('-k', metavar='keyword', help='keyword')
    parser.add_argument('-t', help='test which benchmark is better')
    parser.add_argument('-c', help='use classfiy mode')
    parser.add_argument('-f', help='file used to classfiy')
    args = parser.parse_args()
    wiki = WikiKCEM()
    if args.k:
        while True:
            keyword = input('\nplease input the keyword you want to query:\n')
            keyword = keyword.encode('utf-8').decode('utf-8', errors='ignore')
            print(wiki.findParent(keyword))
    if args.t:
        wiki.loss()
    if args.c:
        print(wiki.classify(args.f))