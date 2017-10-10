class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, uri=None):
		from pymongo import MongoClient
		self.client = MongoClient(uri)
		self.db = self.client['nlp']
		self.Collect = self.db['kcem']

	def get(self, keyword, lang, num, kem_topn_num, kcm_topn_num):
		import json, requests
		"""Generate list of term data source files
		Returns:
			if contains invalid queryString key, it will raise exception.
		"""
		result = self.Collect.find({'key':keyword, '{}-{}'.format(kcm_topn_num, kem_topn_num):{'$exists':True}}, {'{}-{}'.format(kcm_topn_num, kem_topn_num):1, '_id':False}).limit(1)
		if result.count()==0:
			kcm_lists = list()

			for kemtopn in json.loads(requests.get('http://140.120.13.244:10000/kem/?keyword={}&lang={}&num={}'.format(keyword, lang, kem_topn_num)).text):
				kcm_lists.append( list( kcmtopn 
					for kcmtopn in json.loads(requests.get('http://140.120.13.244:10000/kcm/?keyword={}&lang={}&num={}'.format(kemtopn[0], lang, kcm_topn_num)).text )
					) 
				)

			result={}
			for kcm_list in kcm_lists:#統計出現的字
				for word in kcm_list:
					result[word[0]] = result.setdefault(word[0], 0) + 1.0/float(kem_topn_num)

			result = sorted(result.items(), key = lambda x: -x[1])
			self.Collect.update({'key':keyword}, {"$set":{'{}-{}'.format(kcm_topn_num, kem_topn_num):result}}, upsert=True)
			return result[:num]
			
		return dict(list(result)[0])['{}-{}'.format(kcm_topn_num, kem_topn_num)][:num]

if __name__ == '__main__':
	import sys
	k = KCEM('mongodb://172.17.0.6:27017')
	print(k.get(sys.argv[1], 'cht', num=10, kem_topn_num=sys.argv[2], kcm_topn_num=sys.argv[3]))