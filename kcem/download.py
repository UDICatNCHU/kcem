#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, subprocess
lang = sys.argv[1]
subprocess.call(['wget', 'https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-page.sql.gz'.format(lang)])
subprocess.call(['wget', 'https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-categorylinks.sql.gz'.format(lang)])
# subprocess.call(['wget', 'https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-category.sql.gz'.format(lang)])
# subprocess.call(['wget', 'https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-pagelinks.sql.gz'.format(lang)])
# subprocess.call(['wget', 'https://dumps.wikimedia.org/{0}wiki/latest/{0}wiki-latest-redirect.sql.gz'.format(lang)])

subprocess.call(['gunzip', '*.sql.gz'])

print('Start insert sql into MySQL')
subprocess.call(['mysql', 'test', '<', '{0}wiki-latest-page.sql'.format(lang)])
subprocess.call(['mysql', 'test', '<', '{0}wiki-latest-categorylinks.sql'.format(lang)])
# subprocess.call(['mysql', 'test', '<', '{0}wiki-latest-pagelinks.sql'.format(lang)])
# subprocess.call(['mysql', 'test', '<', '{0}wiki-latest-category.sql'.format(lang)])
# subprocess.call(['mysql', 'test', '<', '{0}wiki-latest-redirect.sql'.format(lang)])
print('Download Wikipedia dump success!!!')