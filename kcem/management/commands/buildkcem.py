from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
from kcem.apps import KCEM

class Command(BaseCommand):
	help = 'PARSING WIKIPEDIA PAGE HIERARCHY'
		
	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)

	def handle(self, *args, **options):
		k = KCEM(lang=options['lang'], uri=uri)
		k.build()
		self.stdout.write(self.style.SUCCESS('PARSING WIKIPEDIA PAGE HIERARCHY SUCCESS'))