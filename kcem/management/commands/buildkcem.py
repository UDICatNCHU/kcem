from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
from kcem import WikiKCEM
import multiprocessing, pymongo, logging, threading, math

logging.basicConfig(format='%(levelname)s : %(asctime)s : %(message)s', filename='buildKCEM.log', level=logging.INFO)
class Command(BaseCommand):
    help = 'use this to build kcem!'
    
    def build(self):
        k = WikiKCEM(uri)
        keywordList = [i['key'] for i in self.Query.find({}, {'key':1, '_id':False})]
        step = math.ceil(len(keywordList)/multiprocessing.cpu_count())
        keywordPieces = [keywordList[i:i + step] for i in range(0, len(keywordList), step)]
        logging.info('start building kcem')
        self.Collect.remove({})

        def activateKCEM(keywordThreadList):
            ThreadResult = []
            for index, keyword in enumerate(keywordThreadList):
                ThreadResult.append(k.buildParent(keyword))
                if index % 1000 == 0:
                    logging.info("已處理 %d 個單子" % index)
                    self.Collect.insert(ThreadResult)
                    ThreadResult = []

        workers = [threading.Thread(target=activateKCEM, kwargs={'keywordThreadList':keywordPieces[i]}, name=str(i)) for i in range(multiprocessing.cpu_count())]

        for thread in workers:
           thread.start()

        # Wait for all threads to complete
        for thread in workers:
            thread.join()
        self.Collect.create_index([("key", pymongo.HASHED)])

    def handle(self, *args, **options):
        self.client = pymongo.MongoClient(uri)
        self.db = self.client['nlp']
        self.Query = self.db['wikiReverse']
        self.Collect = self.db['kcem']
        self.build()
        self.stdout.write(self.style.SUCCESS('build kcem model success!!!'))