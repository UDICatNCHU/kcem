from django.core.management.base import BaseCommand, CommandError
from kcem.crawler import WikiCrawler

class Command(BaseCommand):
    help = 'use this to crawl Wikipedia !'
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('--crawl', type=bool)
        parser.add_argument('--fix', type=bool)
        parser.add_argument('--disambiguation', type=bool)
    
    def handle(self, *args, **options):
        wiki = WikiCrawler()
        if options['crawl']:
            wiki.CrawlFromDumpData()
            wiki.crawl('頁面分類')
            wiki.dfs('全部消歧義頁面', disambiguation=True)
            wiki.dfs('二字消歧义', disambiguation=True)
            # wiki.crawl('日本動畫師')
            # wiki.crawl('特色級時間條目')
            # wiki.crawl('中式麵條')
            # wiki.crawl('各国动画师')
            # wiki.crawl('中央大学校友')
            # wiki.crawl('媒體')
            # wiki.crawl('xbox%20360遊戲封面')
            # wiki.crawl('喜欢名侦探柯南的维基人')
            # wiki.crawl('日本原創電視動畫')
            # wiki.crawl('富士電視台動畫')
            # wiki.crawl('萌擬人化')
            # wiki.checkMissing()
            wiki.mergeMongo()
        elif options['fix']:
            wiki.checkMissing()
            wiki.mergeMongo()
        elif options['disambiguation']:
            wiki.dfs('全部消歧義頁面', disambiguation=True)
        self.stdout.write(self.style.SUCCESS('crawl Wikipedia success!!!'))