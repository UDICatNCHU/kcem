from django.core.management.base import BaseCommand, CommandError
import subprocess

class Command(BaseCommand):
	help = 'Download Wikipedia dump and insert into MySQL !'
		
	def handle(self, *args, **options):
		subprocess.call(['apt', 'install', '-y', 'opencc'])
		subprocess.call(['gunzip', '*.sql.gz'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-category.sql.gz'])
		subprocess.call(['mysql', '-uroot', '-e', "create database category"])
		subprocess.call(['mysql', 'category${1}', '<', '${1}wiki-latest-category.sql'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-categorylinks.sql.gz'])
		subprocess.call(['mysql', '-uroot', '-e', "create database categorylinks"])
		subprocess.call(['mysql', 'categorylinks${1}', '<', '${1}wiki-latest-categorylinks.sql'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-page.sql.gz'])
		subprocess.call(['mysql', '-uroot', '-e', "create database page"])
		subprocess.call(['mysql', 'page${1}', '<', '${1}wiki-latest-page.sql'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-pagelinks.sql.gz'])
		subprocess.call(['mysql', '-uroot', '-e', "create database pagelinks"])
		subprocess.call(['mysql', 'pagelinks${1}', '<', '${1}wiki-latest-pagelinks.sql'])
		subprocess.call(['wget', 'https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-redirect.sql.gz'])
		subprocess.call(['mysql', '-uroot', '-e', "create database redirect"])
		subprocess.call(['mysql', 'redirect${1}', '<', '${1}wiki-latest-redirect.sql'])
		self.stdout.write(self.style.SUCCESS('Download Wikipedia dump success!!!'))