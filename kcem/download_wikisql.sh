#!/usr/bin/env bash
wget https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-page.sql.gz
wget https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-categorylinks.sql.gz
# wget https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-category.sql.gz
# wget https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-pagelinks.sql.gz
# wget https://dumps.wikimedia.org/${1}wiki/latest/${1}wiki-latest-redirect.sql.gz

gunzip *.sql.gz

echo 'Start insert sql into MySQL'
mysql test < ${1}wiki-latest-page.sql
mysql test < ${1}wiki-latest-categorylinks.sql
# mysql test < ${1}wiki-latest-pagelinks.sql
# mysql test < ${1}wiki-latest-category.sql
# mysql test < ${1}wiki-latest-redirect.sql
echo 'Download Wikipedia dump success!!!'