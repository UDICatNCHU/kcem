from kcem.wiki.crawler.crawler import WikiCrawler
import pytest
wiki = WikiCrawler()

def function():
	i = 1/0

def test_exception():
	assert function == None

# def test_weird_wiki_page():
#     assert wiki.crawl('馬爾維納斯羣島') == None
#     assert wiki.crawl('xbox%20360遊戲封面') == None
#     assert wiki.crawl('特色級時間條目') == None
#     wiki.checkMissing()
#     wiki.mergeMongo()

# def test_normal_page():
#     assert wiki.crawl('中式麵條') == None
#     wiki.checkMissing()
#     wiki.mergeMongo()