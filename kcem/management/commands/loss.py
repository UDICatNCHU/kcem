# author: Shane Yu  date: April 8, 2017
from django.core.management.base import BaseCommand, CommandError
import pyprind, json
from gensim import models
from utils import criteria
from django.http import HttpRequest
from kcem.views import kcem as kcemRequest

class Command(BaseCommand):
    help = 'use this to test kcem!'
    
    def loss(self):
        import json
        import numpy as np
        answer = json.load(open('answer.json', 'r'))
        power = []
        for i in np.arange(1.0, 1.5, 0.005):
            power.append(sum([dict(self.get(term, lambda jiebaCut:i ** len(jiebaCut))['value'])[answer[term]] for term in answer]))
        print(power)
        print('1 + lnN')
        print(sum([dict(self.get(term, lambda jiebaCut:len(jiebaCut) * math.log1p(len(jiebaCut)))['value'])[answer[term]] for term in answer]))
        print('1 + log10 N')
        print(sum([dict(self.get(term, lambda jiebaCut:1+math.log(len(jiebaCut), 10))['value'])[answer[term]] for term in answer]))
        print('1 + log2 N')
        print(sum([dict(self.get(term, lambda jiebaCut:1+math.log(len(jiebaCut), 2))['value'])[answer[term]] for term in answer]))
        print('N (1 + logN)')
        print(sum([dict(self.get(term, lambda jiebaCut: len(jiebaCut)*(1+math.log(len(jiebaCut), 2)))['value'])[answer[term]] for term in answer]))
        print('1 + NlogN')
        print(sum([dict(self.get(term, lambda jiebaCut:1+len(jiebaCut) * math.log(len(jiebaCut), 2))['value'])[answer[term]] for term in answer]))

        print('1 + NlogX N')
        power = []
        for i in np.arange(1.05, 10, 0.05):
            power.append(sum([dict(self.get(term, lambda jiebaCut:1+len(jiebaCut)*math.log(len(jiebaCut), i))['value'])[answer[term]] for term in answer]))
        print(power)

        print('N (1 + logX N)')
        power = []
        for i in np.arange(1.05, 10, 0.05):
            power.append(sum([dict(self.get(term, lambda jiebaCut: len(jiebaCut)*(1+math.log(len(jiebaCut), i)))['value'])[answer[term]] for term in answer]))
        print(power)


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