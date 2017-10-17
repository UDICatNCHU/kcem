from kcem.utils.utils import criteria
import json, requests
from pymongo import MongoClient
from kcmApp.views import kcm as kcmRequest
from kem.views import kem as kemRequest
from django.http import HttpRequest

class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, uri=None):
		self.client = MongoClient(uri)
		self.db = self.client['nlp']
		self.Collect = self.db['kcem']
		self.kcem_new_collect = self.db['kcem_new']

	def get(self, keyword, lang, num, kem_topn_num, kcm_topn_num):
		"""Generate list of term data source files
		Returns:
			if contains invalid queryString key, it will raise exception.
		"""
		result = self.Collect.find({'key':keyword, '{}-{}'.format(kcm_topn_num, kem_topn_num):{'$exists':True}}, {'{}-{}'.format(kcm_topn_num, kem_topn_num):1, '_id':False}).limit(1)
		if result.count()==0:
			kcm_lists = list()

			httpReq = HttpRequest()
			httpReq.method = 'GET'
			httpReq.GET['lang'] = 'cht'
			httpReq.GET['keyword'] = keyword
			httpReq.GET['num'] = kem_topn_num
			for kemtopn in json.loads(kemRequest(httpReq).getvalue().decode('utf-8')):

				httpReq.GET['num'] = kcm_topn_num
				httpReq.GET['keyword'] = kemtopn[0]				
				kcm_lists.append( list( kcmtopn 
					for kcmtopn in json.loads(kcmRequest(httpReq).getvalue().decode('utf-8'))
					) 
				)

			result={}
			for kcm_list in kcm_lists:#統計出現的字
				for word in kcm_list:
					result[word[0]] = result.setdefault(word[0], 0) + 1.0/float(kem_topn_num)

			result = sorted(result.items(), key = lambda x: -x[1])
			self.Collect.update({'key':keyword}, {"$set":{'{}-{}'.format(kcm_topn_num, kem_topn_num):result[:10]}}, upsert=True)
			return result[:num]
			
		return dict(list(result)[0])['{}-{}'.format(kcm_topn_num, kem_topn_num)][:num]

	def get_kcem_new(self, keyword, num):
		# 22, 12是目前實驗出最佳的參數組合
		kcm = 22
		kem = 12

		result = self.kcem_new_collect.find({'key':keyword}, {'value':1, '_id':False}).limit(1)
		if result.count() == 0:
			kcemAns = self.get(keyword, 'cht', num = 10, kem_topn_num=kem, kcm_topn_num=kcm)
			result = criteria('hybrid', kcemAns, keyword)
			self.kcem_new_collect.update({'key':keyword}, {'$set':{'value':result}}, upsert=True)
			return result[:num]

		return dict(list(result)[0])['value'][:num]


if __name__ == '__main__':
	import sys
	k = KCEM('mongodb://172.17.0.6:27017')
	print(k.get(sys.argv[1], 'cht', num=10, kem_topn_num=sys.argv[2], kcm_topn_num=sys.argv[3]))