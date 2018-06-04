from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
from kcem.apps import KCEM
import pickle

class Command(BaseCommand):
	help = 'merge duplicate key of kcem'
		
	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)

	def handle(self, *args, **options):
		k = KCEM(options['lang'], uri, ngram=True)
		for index, key in enumerate(pickle.load(open('duplicate_key_{}.pkl'.format(options['lang']), 'rb'))):
			if index % 100 == 0:
				print('merge {} duplicate key {}'.format(index, key))
				k.get(key)
		self.stdout.write(self.style.SUCCESS('merge KCEM success!!!'))