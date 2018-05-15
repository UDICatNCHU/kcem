# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models import Q
from kcm import KCM
from udic_nlp_API.settings_database import uri
from udicOpenData.dictionary import *
from kcem.models import *
from django.db import connection
from collections import namedtuple
from opencc import OpenCC
from functools import reduce
from collections import defaultdict
from kcem.utils.fullwidth2halfwidth import *
import gensim, json, logging, math
import multiprocessing as mp

openCC = OpenCC('s2t')
logging.basicConfig(format='%(levelname)s : %(asctime)s : %(message)s', filename='buildKCEM.log', level=logging.INFO)

class KcemConfig(AppConfig):
	name = 'KCEM'

class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, lang, uri=None):
		self.lang = lang
		self.kcmObject = KCM(lang=self.lang, uri=uri)
		self.model = gensim.models.KeyedVectors.load_word2vec_format('med400.model.bin.{}'.format(self.lang), binary=True)
		self.keySet = set()
		self.cpus = math.ceil(mp.cpu_count() * 0.5)

	def build(self):
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
				keywordKcm = dict(((key, count) for key, pos, count in self.kcmObject.get(keyword, -1).get('value', [])))
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
			if keyword in self.model.wv.vocab:
				return harmonic_mean()
			else:
				return kcmScore()

		def minMaxNormalization(candidate):
			# Use Min-max normalization
			# 因為最後輸出的值為機率，而機率不能是負的
			# 所以先透過min-max轉成0~1的數值範圍
			# print(candidate)
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

		def categorylinks_query(page_id):
			with connection.cursor() as cursor:
				cursor.execute("SELECT * FROM categorylinks where cl_from = %s", [page_id])
				result = cursor.fetchall()
				desc = [col[0] for col in cursor.description]
				nt_result = namedtuple('Result', desc)
			return (nt_result(*row) for row in result)

		def merge_hypernym_and_insert(merge_insert_list):
			# merge those item having the same key
			# because wiki might have multiple page which describes the same topic
			# but only one page would have real contents
			# others might be redirect page or category
			# but they all have the same key...

			merge_table = defaultdict(set)

			for page_title, toxinomic_score_dict_json_str in merge_insert_list:
				# query duplicate key object from DB
				# and put it's key into merge_table for merge sake
				item_already_inserted = Hypernym.objects.get(key=page_title)
				merge_table[page_title].update(json.loads(item_already_inserted.value).keys())

				# also put another duplicate key object which isn't in DB
				# into merge_table for merge sake
				toxinomic_score_dict = json.loads(toxinomic_score_dict_json_str)
				merge_table[page_title].update(toxinomic_score_dict.keys())

			# use merge_table which having all the categorys of a key
			# and then use toxinomic_score and minMaxNormalization to calculate real probability
			for page_title, category_key_set in merge_table:
				merge_table[page_title] = minMaxNormalization({toxinomic_score(page_title, category) for category in category_key_set})

			# insert to DB
			for page_title, toxinomic_score_dict in merge_table:
				obj, created = Hypernym.objects.update_or_create(
				    key=page_title, defaults={'value':json.dumps(toxinomic_score_dict)})

		# empty table kcem_Hypernym first
		Hypernym.objects.all().delete()

		insert_list = []
		merge_insert_list = []
		for page in Page.objects.filter(Q(page_namespace=0) | Q(page_namespace=14))    :
			page_id = page.page_id

			# turn it into lower case or it'll raise Duplicate Key in DB
			page_title = openCC.convert(page.page_title.decode('utf-8')).lower()
			# turn fullwidth to halfwidth to prevent it from having Duplicate Key again...
			page_title = f2h(page_title)
			toxinomic_score_dict = {}
			for category in categorylinks_query(page_id):
				parent = openCC.convert(category.cl_to.decode('utf-8'))
				print(page_title, parent)
				toxinomic_score_dict[parent] = toxinomic_score(page_title, parent)

			if not toxinomic_score_dict:
				# this kind of error comes from redirect page
				# here's an example
				# 1. https://zh.wikipedia.org/w/index.php?title=%E7%A3%81%E5%81%8F%E8%A7%92&redirect=no
				# 2. https://zh.wikipedia.org/zh-tw/%E5%9C%B0%E7%A3%81%E5%81%8F%E8%A7%92
				continue
			else:
				value = minMaxNormalization(toxinomic_score_dict)
				if page_title in self.keySet:
					merge_insert_list.append(Hypernym(
						key=page_title,
						value=json.dumps(value)
					))
				else:
					print(len(insert_list))
					self.keySet.add(page_title)
					insert_list.append(Hypernym(
						key=page_title,
						value=json.dumps(value)
					))
				if len(insert_list) > 1000:
					logging.info("already inserted %d keyword" % len(insert_list))
					############## MySQL Bug ####################
					# e.g. ñ = n, so when i do bulk_create 
					# it would occur Duplicate Key Error 
					# so these multiple try/except is trying handle this issue....            
					############## MySQL Bug ####################
					try:
						Hypernym.objects.bulk_create(insert_list)
					except Exception as e:
						print(e + "only insert len == 1")
						try:
							Hypernym.objects.bulk_create([j for j in insert_list if len(j.key) != 1])
						except Exception as e:
							# this is a weird error
							# maybe some item which has already been inserted before
							# has a key called n123,
							# and the bulk_create we do above might have a item with key ñ123
							# MySQL thinks ñ123 == n123 is True
							# and it cannot be filtered out by removing items with key length less than 1
							# so i do merge. This merge_hypernym_and_insert would merge Categorys of ñ123 with n123's, which might cause a little harm to accuracy of model... 
							print(e + "use merge to insert len == 1")
							merge_hypernym_and_insert([j for j in insert_list if len(j.key) != 1])
					insert_list = []

		merge_hypernym_and_insert(merge_insert_list)

	def get(self, keyword):
		return {
			'key':keyword,
			'value':sorted(json.loads(Hypernym.objects.get(key=keyword).value).items(), key=lambda x:-x[1])
		}