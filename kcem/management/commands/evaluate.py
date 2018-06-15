from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
from kcem.apps import KCEM
from kcem.evaluation.label import label

class Command(BaseCommand):
	help = 'show precision of kcem'

	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)
		
	def handle(self, *args, **options):
		k = KCEM(options['lang'], uri, ngram=True)
		total = len(label)
		correct = 0
		for key, value in label.items():
			result = k.get(key)
			predict_raw = result['value']
			print(key, result, value)
			if predict_raw:
				predict = predict_raw[0][0]
			else:
				continue
			if predict in value:
				correct += 1
			else:
				print(key, predict, value)
		self.stdout.write(self.style.SUCCESS('precision is: {}'.format(correct/total)))
