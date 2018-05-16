from django.core.management.base import BaseCommand, CommandError
from django.core.management import execute_from_command_line
import subprocess
from kcem.models import *

class Command(BaseCommand):
	help = 'Download Wikipedia dump and insert into MySQL !'

	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)
		
	def handle(self, *args, **options):
		lang = options['lang']
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${0}wiki/latest/${0}wiki-latest-page.sql.gz'.format(lang)])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${0}wiki/latest/${0}wiki-latest-categorylinks.sql.gz'.format(lang)])
		# subprocess.call(['wget', 'https://dumps.wikimedia.org/${0}wiki/latest/${0}wiki-latest-category.sql.gz'.format(lang)])
		# subprocess.call(['wget', 'https://dumps.wikimedia.org/${0}wiki/latest/${0}wiki-latest-pagelinks.sql.gz'.format(lang)])
		# subprocess.call(['wget', 'https://dumps.wikimedia.org/${0}wiki/latest/${0}wiki-latest-redirect.sql.gz'.format(lang)])

		subprocess.call(['gunzip', '*.sql.gz'])
		
		subprocess.call(['mysql', 'test', '<', '${0}wiki-latest-page.sql'.format(lang)])
		subprocess.call(['mysql', 'test', '<', '${0}wiki-latest-categorylinks.sql'.format(lang)])
		# subprocess.call(['mysql', 'test', '<', '${0}wiki-latest-pagelinks.sql'.format(lang)])
		# subprocess.call(['mysql', 'test', '<', '${0}wiki-latest-category.sql'.format(lang)])
		# subprocess.call(['mysql', 'test', '<', '${0}wiki-latest-redirect.sql'.format(lang)])
		self.stdout.write(self.style.SUCCESS('Download Wikipedia dump success!!!'))