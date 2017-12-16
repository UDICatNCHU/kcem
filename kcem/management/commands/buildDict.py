from django.core.management.base import BaseCommand, CommandError
from udic_nlp_API.settings_database import uri
import pymongo

class Command(BaseCommand):
    help = 'use this to test kcem!'

    def handle(self, *args, **options):
        client = pymongo.MongoClient(uri)['nlp']
        reverseCollect = client['wikiReverse']
        Collect = client['wiki']

        dictionary = {i['key'] for i in reverseCollect.find()}
        dictionary.update({i['key'] for i in Collect.find()})
        final = list(filter(lambda x:'template:' not in x and 'talk:' not in x and 'user:' not in x and 'category talk:' not in x and 'wikipedia:' not in x and 'draft:' not in x and 'portal:' not in x and 'wikipedia:' not in x and 're:start' not in x and '模塊:' not in x and 'help:' not in x, dictionary))

        with open('wiki.dict.txt', 'w') as f:
            for i in final:
                f.write('{} 999 n\n'.format(i))

        self.stdout.write(self.style.SUCCESS('dump wiki dictionary success!!!'))