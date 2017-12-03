# -*- coding: utf-8 -*-
import jieba, pymongo, numpy, requests
from collections import defaultdict
from ngram import NGram
from itertools import dropwhile
from functools import reduce

class WikiKCEM(object):
    """docstring for WikiKCEM"""
    def __init__(self):
        self.client = pymongo.MongoClient(None)['nlp']
        self.Collect = self.client['wiki']
        self.reverseCollect = self.client['wikiReverse']
        
        from gensim import models
        self.model = models.KeyedVectors.load_word2vec_format('./med400.model.bin', binary=True)
        self.wikiNgram = NGram((i['key'] for i in self.reverseCollect.find({}, {'key':1, '_id':False})))
            
    @staticmethod
    def findPath(keyword):
        Collect = pymongo.MongoClient(None)['nlp']['wikiReverse']
        cursor = list(Collect.find({'key':keyword}).limit(1))[0]
        if 'ParentOfLeafNode' in cursor:
            cursor = cursor['ParentOfLeafNode']
        else:
            cursor = cursor['parentNode']

        queue = {(parent, (keyword, parent,)) for parent in set(cursor) - set(keyword)}

        while queue:
            (keyword, path) = queue.pop()
            cursor = Collect.find({'key':keyword}).limit(1)
            if cursor.count():
                parentNodes = list(cursor)[0]
                parentNodes = parentNodes['parentNode']
                for parent in parentNodes:
                    if parent in path:
                        yield path[:path.index(parent) + 1]
                    else:
                        queue.add((parent, path + (parent, )))
            else:
                yield path

    def findParent(self, keyword):
        # if not in wiki Category
        # use wiki Ngram to search
        cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)
        if not cursor.count():
            keyword = self.wikiNgram.find(keyword)
            cursor = self.reverseCollect.find({'key':keyword}, {'_id':False}).limit(1)

        cursor = list(cursor)[0]
        cursor = cursor.get('ParentOfLeafNode', []) + cursor.get('parentNode', [])
        candidate = {}
        for parent in cursor:
            if keyword not in parent:
                candidate[parent] = self.toxinomic_score(keyword, parent)
        return sorted(candidate.items(), key=lambda x:-x[1])

    def toxinomic_score(self, keyword, parent):
        def getSimilarity(keyword, term):
            try:
                return self.model.similarity(keyword, term) ** 2
            except KeyError as e:
                return 0

        jiebaCut = jieba.lcut(parent)
        scoreList = [getSimilarity(keyword, term) for term in jiebaCut]
        similarityScore = reduce(lambda x, y: x+y, scoreList)

        keywordKcm = dict(requests.get('http://140.120.13.244:10000/kcm/?keyword={}&lang=cht'.format(keyword)).json())
        keywordKcmMax = max(keywordKcm.items(), key=lambda x:x[1])[1]
        kcmScore = reduce(lambda x,y:x+y, [(keywordKcm.get(term, 0) / keywordKcmMax)**2 for term in jiebaCut])
        return (similarityScore + kcmScore) / len(jiebaCut)


if __name__ == '__main__':
    import argparse
    """The main routine."""
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, description='''
        build kcm model and insert it into mongoDB with command line.    
    ''')
    parser.add_argument('-k', metavar='keyword', help='keyword')
    args = parser.parse_args()
    wiki = WikiKCEM()
    if args.k:
        while True:
            keyword = input('\nplease input the keyword you want to query:\n')
            print(list(wiki.findParent(keyword)))
        # 新海誠
        # print(list(wiki.findPath(args.k)))
