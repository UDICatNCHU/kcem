import json, sys, pymongo, requests, pyprind
from gensim import models
from itertools import takewhile

model = models.KeyedVectors.load_word2vec_format('../med400.model.bin', binary=True)
stopwords = json.load(open('stopwords.json','r'))
class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, file, uri=None):
		from pymongo import MongoClient
		self.client = MongoClient('mongodb://172.17.0.17:27017')
		self.db = self.client['nlp']
		self.kcm_collect = self.db['kcm_new']
		self.kcem_collect = self.db['kcem']
		self.file = file

	def insert(self):
		with open(self.file, 'r') as f:
			data = json.load(f)
			record = {}
			for i in data:
				if i['key'] not in record:
					record[i['key']] = i['value']
				else:
					print(i)
					print('==============')
					print(record[i['key']])
			self.kcm_collect.insert(data)
			self.kcm_collect.create_index([("key", pymongo.HASHED)])			

	def get(self, keyword, kcmNum, kemNum):
		result = self.kcem_collect.find({'key':keyword}, {'value':1, '_id':False}).limit(1)
		if result.count()==0:
			kcm_lists = []
			kcm = self.kcm_collect.find({"key":keyword}, {'value':1, '_id':False}).limit(1)
			if kcm.count() != 0:
				found = 1
				kcm_lists.append(set(list(kcm)[0]['value'][:kcmNum]))
			else:
				found = 0

			for kemtopn in requests.get('http://140.120.13.244:10000/kem/?keyword={}&num={}'.format(keyword, kemNum)).json():
				kcm = self.kcm_collect.find({"key":kemtopn[0]}, {'value':1, '_id':False}).limit(1)
				if kcm.count() == 0:
					# print("{} not found".format(kemtopn[0]))
					continue
				found += 1

				kcm_lists.append(set(list(kcm)[0]['value'][:kcmNum]))
			if kcm_lists == []:
				return []

			result={}
			for kcm_list in kcm_lists:#統計出現的字
				for word in kcm_list:
					result[word] = result.setdefault(word, 0) + 1.0/float(found)

			result = sorted(result.items(), key = lambda x: -x[1])
			result = [i for i in result if i not in stopwords and len(i) > 1]

			self.pointer = 0
			def take(x):
				if result[self.pointer][1] < result[:4][-1][1]:
					return False
				else:
					self.pointer += 1
					return True

			def cosSimilarity(x):
				try:
					return (x[0], model.similarity(keyword, x[0]))
				except Exception as e:
					pass

			result = list(takewhile(take, result))
			result = list(map(cosSimilarity, result))
			result = [i for i in result if i != None]
			result = sorted(result, key=lambda x:-x[1])
			if result==[]:
				return []
			return result[0][0]

		return dict(list(result)[0])['value'][0]

if __name__ == '__main__':
	model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
	data = json.load(open('Ontology_from_google.json', 'r')).items()
	file = {}
	loss = 0
	total = 0

	def main(kcmNum, kemNum):
		loss = 0
		total = 0

		for key, ans in pyprind.prog_bar(data):
			myans = k.get(key, kcmNum, kemNum)

			if myans:
				try:
					total += 1
					loss += ((1-float(model.similarity(myans, ans)))*10)**2
				except Exception as e:
					print(e)
					continue
		return loss, total

	k = KCEM(sys.argv[1])

	for kcmNum in range(2, 30, 2):
		for kemNum in range(2, 30, 2):
			loss, total = main(kcmNum, kemNum)
			print("finish {} test, total loss is {}".format(total, loss / total))
			file['{}-{}'.format(kcmNum, kemNum)] = loss / total
	json.dump(file, open(sys.argv[2],'w'))