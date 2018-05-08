from django.core.management.base import BaseCommand, CommandError
import subprocess
from kcem.models import *

class Command(BaseCommand):
	help = 'Download Wikipedia dump and insert into MySQL !'

	def add_arguments(self, parser):
		# Positional arguments
		parser.add_argument('--lang', type=str)
		
	def handle(self, *args, **options):
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-page.sql.gz'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-categorylinks.sql.gz'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-category.sql.gz'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-pagelinks.sql.gz'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-redirect.sql.gz'])

		subprocess.call(['gunzip', '*.sql.gz'])
		
		subprocess.call(['mysql', 'test', '<', '${1}wiki-latest-page.sql'])
		subprocess.call(['mysql', 'test', '<', '${1}wiki-latest-pagelinks.sql'])
		subprocess.call(['mysql', 'test', '<', '${1}wiki-latest-categorylinks.sql'])
		subprocess.call(['mysql', 'test', '<', '${1}wiki-latest-category.sql'])
		subprocess.call(['mysql', 'test', '<', '${1}wiki-latest-redirect.sql'])

		page.objects.filter(lang=None).update(lang=options['lang'])
		categorylinks.objects.filter(lang=None).update(lang=options['lang'])
		category.objects.filter(lang=None).update(lang=options['lang'])
		pagelinks.objects.filter(lang=None).update(lang=options['lang'])
		redirect.objects.filter(lang=None).update(lang=options['lang'])
		self.stdout.write(self.style.SUCCESS('Download Wikipedia dump success!!!'))