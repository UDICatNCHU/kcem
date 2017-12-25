# Create your tests here.
from django.test import TestCase
from kcem.crawler.crawler import WikiCrawler

class OrderTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        wiki = WikiCrawler()

    def test_weird_wiki_page(self):
        assert wiki.crawl('馬爾維納斯羣島') == None
        assert wiki.crawl('xbox%20360遊戲封面') == None
        assert wiki.crawl('特色級時間條目') == None
        wiki.checkMissing()
        wiki.mergeMongo()
        
    def test_normal_page(self):
        assert wiki.crawl('中式麵條') == None
        wiki.checkMissing()
        wiki.mergeMongo()