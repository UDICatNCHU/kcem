from pymongo import MongoClient

class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, uri=None):
		self.client = MongoClient(uri)
		self.db = self.client['nlp']
		self.Collect = self.db['kcem']

	def get(self, keyword, num):
		"""Generate list of term data source files
		Returns:
			if contains invalid queryString key, it will raise exception.
		"""
		result = self.Collect.find({'key':keyword}, {'value':1, '_id':False}).limit(1)
		if result.count()==0:
			[]
		return dict(list(result)[0])['value'][:num]


if __name__ == '__main__':
	import sys
	k = KCEM('mongodb://172.17.0.6:27017')
	print(k.get(sys.argv[1], 'cht', num=10, kem_topn_num=sys.argv[2], kcm_topn_num=sys.argv[3]))