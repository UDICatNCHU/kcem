# author: Shane Yu  date: April 8, 2017
from django.core.management.base import BaseCommand, CommandError
import pyprind, json
from gensim import models
from utils import criteria
from django.http import HttpRequest
from kcem.views import kcem as kcemRequest

class Command(BaseCommand):
    help = 'use this to test kcem!'
    
    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            '--kcemMode',
            default='hybrid',
            type=str,
            help='mode of kcem, you can choose one from hybrid, w2v or kcem.',
        )
        parser.add_argument(
            '--ans',
            default='Ontology_from_google.json',
            type=str,
            help="a json file, which we crawled from Google's Ontology",
        )
        parser.add_argument(
            '--output',
            default='kcem.loss.json',
            type=str,
            help='output file of kcem loss.',
        )
        parser.add_argument(
            '--upperbound',
            default='5',
            type=int,
            help='Upper bound of kcm and kem parameters.',
        )

    def main(self, kcmNum, kemNum):
        loss = 0
        total = 0

        httpReq = HttpRequest()
        httpReq.method = 'GET'
        httpReq.GET['lang'] = 'cht'
        httpReq.GET['kcm'] = kcmNum
        httpReq.GET['kem'] = kemNum

        for key, ans in self.data:
            httpReq.GET['keyword'] = key

            myans = json.loads(kcemRequest(httpReq).getvalue().decode('utf-8'))
            if myans:
                myans = criteria(self.mode, myans, key)[0][0]
                try:
                    loss += ((1-float(self.model.similarity(myans, ans)))*10)**2
                    total += 1
                except Exception as e:
                    print(e)
                    continue
        return loss, total

    def handle(self, *args, **options):
        self.model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
        self.data = json.load(open(options['ans'], 'r')).items()
        self.mode = options['kcemMode']
        file = {}

        for kcmNum in pyprind.prog_bar(range(2, options['upperbound'], 2)):
            for kemNum in range(2, options['upperbound'], 2):
                loss, total = self.main(kcmNum, kemNum)
                print("finish {} test, total loss is {}".format(total, loss / total))
                file['{}-{}'.format(kcmNum, kemNum)] = loss / total

        show = sorted(file.items(), key=lambda x:x[1])
        print('min loss is {}, kcm-kem is : {}'.format(show[0][1], show[0][0]))
        json.dump(file, open(options['output'],'w'))

        self.stdout.write(self.style.SUCCESS('build kem model success!!!'))