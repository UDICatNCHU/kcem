# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models import Q
from kcm import KCM
from udic_nlp_API.settings_database import uri
from kcem.models import *


class KcemConfig(AppConfig):
    name = 'KCEM'

class KCEM(object):
    """docstring for KCEM"""
    def __init__(self, lang, uri=None):
        self.lang = lang
        self.kcmObject = KCM(lang=self.lang, uri=uri)
        self.model = gensim.models.KeyedVectors.load_word2vec_format('med400.model.bin.{}'.format(self.lang), binary=True)

    @staticmethod
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

        # 如果查詢的字不在word2vec裏面，那harmonic mean公式算出來都會是0
        # 這種情況其實還不少，這樣會導致整個harmonic mean都沒用
        # 所以這種情況就用kcm分數當作依據
        if keyword in W2VMODEL.wv.vocab:
            return harmonic_mean()
        else:
            return kcmScore()

    @staticmethod
    def minMaxNormalization(self, candidate):
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
        return candidate

    def build(self):
        for page in Page.objects.filter(Q(page_namespace=0) | Q(page_namespace=14))    :
            page_id = page.page_id
            page_title = page.page_title

            toxinomic_score_dict = {}
            for category in Categorylinks.objects.filter(cl_from=page_id):
                toxinomic_score_dict[category] = toxinomic_score(page_title, category)
            print(minMaxNormalization(toxinomic_score_dict))
            
    def get(self):
        pass