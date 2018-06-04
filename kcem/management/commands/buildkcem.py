from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
from kcem.apps import KCEM

class Command(BaseCommand):
	help = 'PARSING WIKIPEDIA PAGE HIERARCHY'
		
	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)
		parser.add_argument('--cpus', type=int, default=6)

	def handle(self, *args, **options):
		self.stdout.write(self.style.SUCCESS('start building KCEM model'))
		k = KCEM(lang=options['lang'], uri=uri, cpus=int(options['cpus']))
		k.build()
		self.stdout.write(self.style.SUCCESS('build KCEM success!!!'))