from django.core.management.base import BaseCommand, CommandError
from kcem.models import *
from django.db import connection
from django.db.utils import OperationalError
from collections import namedtuple
import pickle, tqdm, os

class Command(BaseCommand):
	help = 'PARSING WIKIPEDIA PAGE HIERARCHY'
		
	def handle(self, *args, **options):
		if not os.path.exists('categorylinks.pkl'):
			with connection.cursor() as cursor:
				cursor.execute("SELECT * FROM categorylinks")
				desc = [col[0] for col in cursor.description]
				result = cursor.fetchall()
				nt_result = namedtuple('Result', desc)
				result = [nt_result(*row) for row in result]
				# table = ['cl_from', 'cl_to', 'cl_sortkey', 'cl_timestamp', 'cl_sortkey_prefix', 'cl_collation', 'cl_type']
				value = []
				for i in tqdm.tqdm(result):
					# tmp = {
					# 	'cl_from':i.cl_from,
					# 	'cl_to':i.cl_to.decode('unicode_escape', 'ignore').encode('unicode_escape'),
					# 	'cl_sortkey':i.cl_sortkey.decode('unicode_escape', 'ignore').encode('unicode_escape'),
					# 	'cl_timestamp':str(i.cl_timestamp),
					# 	'cl_sortkey_prefix':i.cl_sortkey_prefix.decode('unicode_escape', 'ignore').encode('unicode_escape'),
					# 	'cl_collation':i.cl_collation.decode('unicode_escape', 'ignore').encode('unicode_escape'),
					# 	'cl_type':i.cl_type.decode('unicode_escape', 'ignore').encode('unicode_escape')
					# }
					tmp = {
						'cl_from':i.cl_from,
						'cl_to':i.cl_to.decode('unicode_escape', 'ignore').encode('unicode_escape'),
						'cl_sortkey':i.cl_sortkey.decode('unicode_escape', 'ignore').encode('unicode_escape'),
						'cl_timestamp':str(i.cl_timestamp),
						'cl_sortkey_prefix':i.cl_sortkey_prefix.decode('unicode_escape', 'ignore').encode('unicode_escape'),
						'cl_collation':i.cl_collation.decode('unicode_escape', 'ignore').encode('unicode_escape'),
						'cl_type':i.cl_type.decode('unicode_escape', 'ignore').encode('unicode_escape')
					}
					if not tmp['cl_from']:
						print(i.__dict__)
						print(tmp)
					value.append(Categorylinksnew(**tmp))
				del result
				pickle.dump(value, open('categorylinks.pkl', 'wb'))
		value = pickle.load(open('categorylinks.pkl', 'rb'))
		# max_cl_to = 0
		# max_cl_sortkey = 0
		# max_cl_timestamp = 0
		# max_cl_sortkey_prefix = 0
		# max_cl_collation = 0
		# max_cl_type = 0
		# for i in value:
		# 	if len(i.cl_to) > max_cl_to: max_cl_to = len(i.cl_to)
		# 	if len(i.cl_sortkey) > max_cl_sortkey: max_cl_sortkey = len(i.cl_sortkey)
		# 	if len(i.cl_timestamp) > max_cl_timestamp: max_cl_timestamp = len(i.cl_timestamp)
		# 	if len(i.cl_sortkey_prefix) > max_cl_sortkey_prefix: max_cl_sortkey_prefix = len(i.cl_sortkey_prefix)
		# 	if len(i.cl_collation) > max_cl_collation: max_cl_collation = len(i.cl_collation)
		# 	if len(i.cl_type) > max_cl_type: max_cl_type = len(i.cl_type)
		# print('max_cl_to:', max_cl_to)
		# print('max_cl_sortkey:', max_cl_sortkey)
		# print('max_cl_timestamp:', max_cl_timestamp)
		# print('max_cl_sortkey_prefix:', max_cl_sortkey_prefix)
		# print('max_cl_collation:', max_cl_collation)
		# print('max_cl_type:', max_cl_type)
		Categorylinksnew.objects.all().delete()
		# tmp = {'cl_sortkey': 'MOUNTAIN', 'cl_timestamp': '2015-09-02 13:44:06', 'cl_from': 9, 'cl_type': 'page', 'cl_sortkey_prefix': '', 'cl_collation': 'uppercase', 'cl_to': 'En-3_使用者'.encode('unicode_escape')}
		# a=Categorylinksnew(**tmp)
		# a.__dict__
		# Categorylinksnew(**tmp).save()
		values = [value[i:i+1000] for i in range(0, len(value), 1000)]

		for value in values:
			try:
				Categorylinksnew.objects.bulk_create(value)
			except OperationalError as e:
				print(e)
				connection.close()
				Categorylinksnew.objects.bulk_create(value)
		self.stdout.write(self.style.SUCCESS('transform success!!!'))
