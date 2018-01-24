# -*- coding: utf-8 -*-
import jieba, pymongo, numpy, math
from collections import defaultdict
from ngram import NGram
from itertools import dropwhile, chain
from functools import reduce
from udicOpenData.stopwords import rmsw
from udic_nlp_API.settings import W2VMODEL
from KCM.__main__ import KCM


class WikiKCEM(object):
    """docstring for WikiKCEM"""
    def __init__(self, uri=None):
        self.kcmObject = KCM('cht', 'cht', uri=uri)

        self.client = pymongo.MongoClient(uri)['nlp']
        self.Collect = self.client['wiki']
        self.reverseCollect = self.client['wikiReverse']
        self.kcem = self.client['kcem']
        
        self.model = W2VMODEL
        self.wikiNgram = NGram((i['key'] for i in self.reverseCollect.find({}, {'key':1, '_id':False})))
        self.WikiEntitySet = set(chain(*[ i['leafNode'] for i in self.Collect.find({"leafNode":{"$exists": True}})]))
            
    @staticmethod
    def findPath(keyword):
        cursor = self.reverseCollect.find({'key':keyword}).limit(1)[0]
        if 'ParentOfLeafNode' in cursor:
            cursor = cursor['ParentOfLeafNode']
        else:
            cursor = cursor['parentNode']

        queue = {(parent, (keyword, parent,)) for parent in set(cursor) - set(keyword)}

        while queue:
            (keyword, path) = queue.pop()
            cursor = self.reverseCollect.find({'key':keyword}).limit(1)
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

    def get(self, keyword):
        # if not in wiki Category
        # use wiki Ngram to search

        def disambiguate(ambKeyword, cursor):
            value = cursor[0].get('value', [])
            value = [v for v in value if '消歧義' not in v[0]]

            # 如果value[0][0], 也就是kcem回傳唯一一個的concept跟你說是消歧義
            # 就找他child的parent
            if not value:
                # Because cursor would has a key 全部消歧義頁面 or X字消歧義
                # these are all ambiguous keyword
                # so need some post-processing
                # that's the reason why this api exists !
                MaxProbability, BestCursor, bestChild = 0, None, ''

                for child in self.child(ambKeyword)['leafNode']:
                    tmp = self.kcem.find({'key':child}, {'_id':False}).limit(1)
                    if tmp.count():
                        tmp = tmp[0]
                    else:
                        continue
                    for hypernymOfChild in tmp['value']:
                        if hypernymOfChild[1] > MaxProbability and hypernymOfChild[0] != ambKeyword and '消歧義' not in hypernymOfChild[0]:
                            MaxProbability = hypernymOfChild[1]
                            BestCursor = tmp
                            bestChild = child

                            # 因為kcem的value已經排序過了
                            # 所以如果一遇到符合的一定是possibility最高的
                            # 找到就可以直接break了
                            break
                if not BestCursor:
                    # 找遍child的hypernym還是都只剩消歧義那就只能放棄了
                    return {'key':ambKeyword, 'value':value, 'similarity':1}
                return {**(BestCursor), 'similarity':self.wikiNgram.compare(ambKeyword, bestChild)}
            else:
                # 去掉消歧義還是有hypernym的就直接回傳
                return {'key':ambKeyword, 'value':value, 'similarity':1}

        result = self.kcem.find({'key':keyword}, {'_id':False}).limit(1)
        if result.count():
            return disambiguate(keyword, result)
        else:
            ngramKeyword = self.wikiNgram.find(keyword)
            if ngramKeyword:
                result = self.kcem.find({'key':ngramKeyword}, {'_id':False}).limit(1)
                if result.count():
                    tmpResult = {**(disambiguate(ngramKeyword, result))}
                    return {**tmpResult, 'similarity':self.wikiNgram.compare(tmpResult['key'], keyword)}
            return {'key':keyword, 'value':[], 'similarity':0}

    def buildParent(self, keyword):
        cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)
        if not cursor.count(): return
        cursor = cursor[0].get('ParentOfLeafNode', []) + cursor[0].get('parentNode', [])
        candidate = {parent: self.toxinomic_score(keyword, parent) for parent in cursor}

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
        result = {'key':keyword, 'value':sorted(candidate.items(), key=lambda x:(-x[1], len(x[0]))), 'similarity':1}
        return result

    def toxinomic_score(self, keyword, parent):
        jiebaCut = jieba.lcut(parent, cut_all=True)
        def similarityScore():
            def getSimilarity(keyword, term):
                try:
                    similarity = self.model.similarity(keyword, term)
                    sign = 1 if similarity > 0 else -1
                    return sign * (similarity ** 2)
                except KeyError as e:
                    return 0
            scoreList = [getSimilarity(keyword, term) for term in jiebaCut]
            return reduce(lambda x, y: x+y, scoreList)

        def kcmScore():
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

        # default mode
        # return (similarityScore() + kcmScore()) / 1.17 ** len(jiebaCut)
        if keyword in W2VMODEL.wv.vocab:
            return harmonic_mean()
        else:
            return kcmScore()

    def counterKCEM(self, wordcount, EntityOnly=False):
        # 接受的參數是一個counter
        # 把counter裏面所有的字都用kcem轉換
        result = defaultdict(dict)

        for key, count in wordcount.items():
            if EntityOnly and key not in self.WikiEntitySet:
                continue
            parent = self.get(key)
            if parent['key'] == key and parent['value']:
                if key not in result[parent['value'][0][0]].setdefault('key', {}):
                    result[parent['value'][0][0]]['key'][key] = count
                result[parent['value'][0][0]]['count'] = result[parent['value'][0][0]].setdefault('count', 0) + count
        return sorted(result.items(), key=lambda x:-x[1]['count'])

    def child(self, keyword):
        result = self.Collect.find({'key':keyword}, {'leafNode':1, '_id':False}).limit(1)
        if result.count():
            return result[0]
        else:
            return {}

if __name__ == '__main__':
    import argparse
    """The main routine."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
        build kcm model and insert it into mongoDB with command line.    
    ''')
    parser.add_argument('-k', metavar='keyword', help='keyword')
    parser.add_argument('-c', help='use classfiy mode')
    parser.add_argument('-f', help='file used to classfiy')
    args = parser.parse_args()
    wiki = WikiKCEM()
    if args.k:
        while True:
            keyword = input('\nplease input the keyword you want to query:\n')
            keyword = keyword.encode('utf-8').decode('utf-8', errors='ignore')
            print(wiki.get(keyword))
    elif args.c:
        print(wiki.topn(args.f))