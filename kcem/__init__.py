# -*- coding: utf-8 -*-
import jieba, pymongo, numpy, math
from collections import defaultdict
from ngram import NGram
from itertools import dropwhile, chain
from functools import reduce
from udicOpenData.stopwords import rmsw
from udic_nlp_API.settings import W2VMODEL
from KCM.__main__ import KCM
from kem import KEM
from udic_nlp_API.settings_database import uri
from scipy import spatial

class WikiKCEM(object):
    """docstring for WikiKCEM"""
    def __init__(self, uri=None):
        self.kcmObject = KCM('cht', 'cht', uri=uri)
        self.kemObject = KEM(uri)

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

    def get(self, keyword, docVec=None):
        def disambiguate(cursor):
            keyword = cursor[0]['key']
            def disambiguate_child():
                # Because cursor would has a key 全部消歧義頁面 or X字消歧義
                # these are all ambiguous keyword
                # so need some post-processing
                # that's the reason why this api exists !
                MaxProbability, BestCursor, bestChild = 0, None, ''

                for child in self.child(keyword).get('leafNode', []):
                    tmp = self.kcem.find({'key':child}, {'_id':False}).limit(1)
                    if tmp.count():
                        tmp = tmp[0]
                    else:
                        continue
                    for hypernymOfChild in tmp['value']:
                        if hypernymOfChild[1] > MaxProbability and hypernymOfChild[0] != keyword and '消歧義' not in hypernymOfChild[0]:
                            MaxProbability = hypernymOfChild[1]
                            BestCursor = tmp
                            bestChild = child

                            # 因為kcem的value已經排序過了
                            # 所以如果一遇到符合的一定是possibility最高的
                            # 找到就可以直接break了
                            break
                if not BestCursor:
                    # 找遍child的hypernym還是都只剩消歧義那就只能放棄了
                    return {'key':keyword, 'value':value, 'similarity':1, 'origin':keyword}
                return {**(BestCursor), 'similarity':self.wikiNgram.compare(keyword, bestChild), 'origin':keyword}

            def useDocVec2disambiguate_child():
                # use docvec to do disambiguate !
                docvec = json.loads(request.POST.dict()['docvec'])
                bestChild, MaxSimilarity  = '', 0

                for child in k.child(keyword)['leafNode']:
                    vec = self.kemObject.getVect(child)['value']
                    similarity = 1 - spatial.distance.cosine(vec, docvec) if vec != [0] * 400 and docvec != [0]*400 else -1
                    if similarity > MaxSimilarity and child != keyword:
                        bestChild = child
                        MaxSimilarity = similarity

                result = self.kcem.find({'key':bestChild}, {'_id':False}).limit(1)
                return {**(result[0]), 'similarity':self.wikiNgram.compare(keyword, bestChild), 'origin':keyword}

            def useDocVec2disambiguate_parent(value):
                # use docvec to do disambiguate !
                hypernymSimilarity = {}
                for hypernym in value:

                    # 把keyword的hypernym做斷詞，然後每個斷詞的結果跟docVec算similarity
                    # ，sum起來除以斷把keyword的hypernym做斷詞
                    # 然後每個斷詞的結果跟docVec算similarity，sum起來除以斷詞後的長度
                    # 這邊使用cut_all的斷詞模式是因為hypernym已經存在於udicOpenData字典中
                    # 所以斷詞不會把他斷開，所以才要cut_all，不過這樣會懲罰字數多的hypernym
                    # 所用count去紀錄，有存在於w2v字典裏面的才計算個數最後做平均
                    words = jieba.lcut(hypernym, cut_all=True)
                    count = 0
                    for word in words:
                        try:
                            wordvec = self.kemObject.getVect(child)['value']
                            similarity = 1 - spatial.distance.cosine(wordvec, docvec) if vec != [0] * 400 and docvec != [0]*400 else -1
                            hypernymSimilarity[hypernym] = hypernymSimilarity.setdefault(hypernym, 0) + similarity
                            count = count + 1
                        except Exception as e:
                            continue
                    hypernymSimilarity[hypernym] = hypernymSimilarity[hypernym] / count
                return {'key':keyword, 'value':sorted(hypernymSimilarity.items(), key=lambda x:-x[0]), 'similarity':1, 'origin':keyword}

            value = cursor[0].get('value', [])
            value = [v for v in value if '消歧義' not in v[0]]

            # 如果value[0][0], 也就是kcem回傳唯一一個的concept跟你說是消歧義
            # 就找他child的parent
            if not value:
                if docVec:
                    return useDocVec2disambiguate_child()
                else:
                    return disambiguate_child()
            else:
                if docVec:
                    return useDocVec2disambiguate_parent()
                else:
                    # 去掉消歧義還是有hypernym的就直接回傳
                    return {'key':keyword, 'value':value, 'similarity':1, 'origin':keyword}

        cursor = self.kcem.find({'key':keyword}, {'_id':False}).limit(1)
        if cursor.count():
            return disambiguate(cursor)
        else:
            ngramKeyword = self.wikiNgram.find(keyword)
            if ngramKeyword:
                cursor = self.kcem.find({'key':ngramKeyword}, {'_id':False}).limit(1)
                if cursor.count():
                    tmpResult = {**(disambiguate(cursor))}
                    return {**tmpResult, 'similarity':self.wikiNgram.compare(tmpResult['key'], keyword), 'origin':keyword}
            return {'key':keyword, 'value':[], 'similarity':0, 'origin':keyword}


    def buildParent(self, keyword):
        def toxinomic_score(keyword, parent):
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

            # 如果查詢的字不在word2vec裏面，那harmonic mean公式算出來都會是0
            # 這種情況其實還不少，這樣會導致整個harmonic mean都沒用
            # 所以這種情況就用kcm分數當作依據
            if keyword in W2VMODEL.wv.vocab:
                return harmonic_mean()
            else:
                return kcmScore()
        
        def minMaxNormalization(candidate):
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

        def buildCandidate(cursor):
            parents = cursor[0].get('ParentOfLeafNode', []) + cursor[0].get('parentNode', [])
            candidate = {parent: toxinomic_score(keyword, parent) for parent in parents}

            # 如果parent有多種選擇， 那就把跟keyword一模一樣的parent給剔除
            # 但是如果parent只有唯一的選擇而且跟關鍵字 一樣那就只能選他了
            if len(candidate) > 1 and keyword in candidate:
                del candidate[keyword]
            return candidate

        cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)
        if not cursor.count(): return

        candidate = buildCandidate(cursor)
        normalizedCandidate = minMaxNormalization(candidate)

        # 意思：key=lambda x:(-x[1], len(x[0]))
        # 先以分數排序，若同分則優先選擇字數少的category當答案
        result = {'key':keyword, 'value':sorted(normalizedCandidate.items(), key=lambda x:(-x[1], len(x[0]))), 'similarity':1}
        return result


    def child(self, keyword):
        cursor = self.Collect.find({'key':keyword}, {'leafNode':1, '_id':False}).limit(1)
        if cursor.count():
            return cursor[0]
        else:
            return {}

    def getList(self, keywords, docVec=None):
        return [self.get(keyword, docVec) for keyword in keywords]


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