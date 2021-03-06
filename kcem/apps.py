# -*- coding: utf-8 -*-
from django.apps import AppConfig
from django.db.models import Q
from kcm import KCM
from udic_nlp_API.settings_database import uri
from udicOpenData.dictionary import *
from kcem.models import *
from django.db import connection, connections
from collections import namedtuple
from opencc import OpenCC
from functools import reduce
from collections import defaultdict
from kcem.utils.fullwidth2halfwidth import f2h
import gensim, json, logging, math, pickle, os, psutil, subprocess, time, pymysql
import multiprocessing as mp
from ngram import NGram
from django.db.utils import OperationalError

openCC = OpenCC('s2t')
logging.basicConfig(format='%(levelname)s : %(asctime)s : %(message)s', filename='buildKCEM.log', level=logging.INFO)

class KcemConfig(AppConfig):
	name = 'KCEM'

class KCEM(object):
	"""docstring for KCEM"""
	def __init__(self, lang='zh', uri=uri, ngram=False, cpus=6):
		self.lang = lang
		self.dir = 'kcem_{}'.format(self.lang)
		# because med400.model.bin.{}.True, aka using ontology to train a new word2vec
		# relies on kcem. So when building kcem mode, we only have med400.model.bin.{}.False to use
		# After that, we can use kcem to build med400.model.bin.{}.True
		self.model = gensim.models.KeyedVectors.load_word2vec_format('med400.model.bin.{}.False'.format(self.lang), binary=True)
		self.kcmObject = KCM(lang=self.lang, uri=uri, ngram=True)
		self.cpus = cpus

		if ngram:
			try:
				self.kcemNgram = pickle.load(open('kcem_ngram.{}.pkl'.format(self.lang), 'rb'))
			except FileNotFoundError as e:
				print(str(e)+', if this happened in building steps, then ignore it!')

	def calculateProbability(self, kcmObject, keyword, category_set):
		def toxinomic_score(keyword, category):
			jiebaCut = jieba.lcut(category, cut_all=True)
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
				# valueFlag is pos according to ttps://gist.github.com/luw2007/6016931
				keywordKcm = dict(((key, count) for key, pos, count in kcmObject.get(keyword, -1, valueFlag=['n', 'nr', 'nr1', 'nr2', 'nrj', 'nrf', 'ns', 'nsf', 'nt', 'nz', 'nl', 'ng']).get('value', [])))
				if keywordKcm:
					keywordKcmTotal = sum(keywordKcm.values())
					return reduce(lambda x,y:x+y, [(keywordKcm.get(term, 0) / keywordKcmTotal)**2 for term in jiebaCut])
				else:
					return 0
			def harmonic_mean():
				'''
				formula:
					2 * kcmScore x similarityScore
					______________________________
					    kcmScore + similarityScore
				'''

				denominator = len(jiebaCut)
				cosine, kcm = similarityScore()/denominator , kcmScore()/denominator
				if cosine and kcm:
					return 2 * cosine * kcm / (cosine + kcm)
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
			try:
				M, m = max(candidate.items(), key=lambda x:x[1])[1], min(candidate.items(), key=lambda x:x[1])[1]
			except Exception as e:
				print('=================================')
				print(keyword, category_set)
				print(e)
				print('=================================')
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

		value = minMaxNormalization({category:toxinomic_score(keyword, category) for category in category_set})
		# Explanation：key=lambda x:(-x[1], len(x[0]))
		# use score as top priority, if score ties then prefer hypernym with less length.
		return sorted(value.items(), key=lambda x:(-x[1], len(x[0])))


	def build(self):

		def process_job(page_list):
			# cause database connection is not thread-safe
			# so need to create their own connection object in each process
			databases = connections.databases
			cursor = pymysql.connect(connections.databases['default']['HOST'], connections.databases['default']['USER'], connections.databases['default']['PASSWORD'], connections.databases['default']['NAME']).cursor()

			def categorylinks_query(cursor, page_id):
				cursor.execute("SELECT * FROM categorylinks where cl_from = %s", [page_id])
				desc = [col[0] for col in cursor.description]
				result = cursor.fetchall()
				nt_result = namedtuple('Result', desc)
				return (nt_result(*row) for row in result)
			
			insert_list = []
			kcmObject = KCM(lang=self.lang, uri=uri, ngram=True)
			process_id = os.getpid()
			for index, page in enumerate(page_list):
				page_id = page.page_id
				# turn it into lower case or it'll raise Duplicate Key in DB
				page_title = openCC.convert(page.page_title.decode('utf-8')).lower()

				# turn fullwidth to halfwidth to prevent it from having Duplicate Key again...
				page_title = f2h(page_title)
				category_set = set()
				for category in categorylinks_query(cursor, page_id):
					category = openCC.convert(category.cl_to.decode('utf-8'))
					category_set.add(category)

				if not category_set:
					# this kind of error comes from redirect page
					# here's an example
					# 1. https://zh.wikipedia.org/w/index.php?title=%E7%A3%81%E5%81%8F%E8%A7%92&redirect=no
					# 2. https://zh.wikipedia.org/zh-tw/%E5%9C%B0%E7%A3%81%E5%81%8F%E8%A7%92
					continue
				value = self.calculateProbability(kcmObject, page_title, category_set)
				insert_list.append(Hypernym(
					key=page_title,
					value=json.dumps(value)
				))
				if len(insert_list) > 5000:
					pickle.dump(insert_list, open(os.path.join(self.dir, '{}-{}.pkl'.format(process_id, index)), 'wb'))
					insert_list = []

			# there's some other data in buffer, so flush it into pkl file
			pickle.dump(insert_list, open(os.path.join(self.dir, '{}-{}.pkl'.format(process_id, index)), 'wb'))

			# close cursor of this process
			cursor.close()
			logging.info('{} done'.format(process_id))
					

		if not os.path.exists(os.path.join(self.dir, 'done')):
			# create self.dir to store kcem pickle
			subprocess.call(['mkdir', self.dir])

			# select Main page("Real" content; articles) and Category description pages
			page_list = Page.objects.filter(Q(page_namespace=0) | Q(page_namespace=14))
			amount = math.ceil(len(page_list)/self.cpus)
			page_list = [page_list[i:i + amount] for i in range(0, len(page_list), amount)]
			processes = [mp.Process(target=process_job, kwargs={'page_list':page_list[i]}) for i in range(self.cpus)]
			for process in processes:
				process.start()
			for process in processes:
				process.join()

			# mark processes job are all done
			open(os.path.join(self.dir, 'done'), 'w')

		# insert those pickle files into MySQL
		# the reason why i dump datas into pickle and then insert it back into MySQL
		# is that use multiprocessing to insert into MySQL would cause disconnection
		# i don't know how to fix...
		logging.info('start merge pickle files')
		insert_list = []

		try:
			# empty table kcem_Hypernym first
			Hypernym.objects.all().delete()
		except OperationalError:
			connection.close()
			Hypernym.objects.all().delete()

		num_of_concepts = set()
		duplicate_key = {}
		for pickle_file in os.listdir(self.dir):
			if pickle_file.endswith('pkl'):
				data = pickle.load(open(os.path.join(self.dir, pickle_file), 'rb'))
				insert_list.extend(data)

				# calculate how many concepts are there in this kcem model
				num_of_concepts.update([category for item in data for category in json.loads(item.value)])

				# duplicate key need to be merge later
				for item in data:
					duplicate_key[item.key] = duplicate_key.get(item.key, 0) + 1

				# insert
				if psutil.virtual_memory().percent > 90:
					Hypernym.objects.bulk_create(insert_list)
					insert_list = []
				elif len(insert_list) > 5000:
					Hypernym.objects.bulk_create(insert_list)
					logging.info('finish insert 5000 rows')
					insert_list = []
		# insert the rest of insert_list
		Hypernym.objects.bulk_create(insert_list)

		pickle.dump([key for key, value in duplicate_key.items() if value > 1], open('duplicate_key_{}.pkl'.format(self.lang), 'wb'))
		pickle.dump(NGram( ( i['key'] for i in Hypernym.objects.values('key') ) ), open('kcem_ngram.{}.pkl'.format(self.lang), 'wb'))
		logging.info('finish kcem insert, there\'s {} concept in kcem model !'.format(len(num_of_concepts)))

	def get(self, keyword):
		if keyword in self.kcemNgram:
			try:
				return {
					'key': keyword,
					'origin': keyword,
					'similarity': 1,
					'value':json.loads(Hypernym.objects.get(key=keyword).value)
				}
			except Exception as e:
				############## MySQL Bug ####################	
				# the original Hypernym schema is:
				# class Hypernym(models.Model):
				#     key = models.CharField(primary_key=True, max_length=255)
				#     value = models.TextField()
				# However, MySQK take ñ = n, so when i do bulk_create 	
				# it would occur Duplicate Key Error 	
				# but i don't know how to set the right binary comparison in MySQL
				# so cancel primary_key=True of Hypernym schema
				# and fix these problem using try/except in get function....
				############## MySQL Bug ####################
				pass

		ngram_keyword = self.kcemNgram.find(keyword)
		if not ngram_keyword:
			return {
				'key': ngram_keyword,
				'origin': keyword,
				'similarity': self.kcemNgram.compare(keyword, ngram_keyword),
				'value':[]
			}

		hypernyms = Hypernym.objects.filter(key=ngram_keyword)

		category_set = set()
		for h in hypernyms:
			for category in json.loads(h.value):
				category_set.add(category)

		value = self.calculateProbability(self.kcmObject, ngram_keyword, category_set)
		Hypernym.objects.filter(key=ngram_keyword).delete()
		Hypernym.objects.create(key=ngram_keyword, value=json.dumps(value))
		return {
			'key': ngram_keyword,
			'origin':keyword,
			'similarity':self.kcemNgram.compare(keyword, ngram_keyword),
			'value':value
		}

	def find_trash_category(self):
		with connection.cursor() as cursor:
			correct = True
			cursor.execute("SELECT * FROM categorylinks where cl_to = '總類'")
			desc = [col[0] for col in cursor.description]
			result = cursor.fetchall()
			nt_result = namedtuple('Result', desc)
		return (nt_result(*row) for row in result)	