from gensim import models
from itertools import permutations
import json, pyprind, random, collections, jieba, os, sys
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)

jieba.load_userdict(os.path.join("dictionary", "NameDict_Ch_v2"))

result = []
data = json.load(open(sys.argv[2], 'r'))
keywordList1 = list(wordVecmodel.vocab.keys())
keywordList2 = list(wordVecmodel.vocab.keys())
random.shuffle(keywordList1)
random.shuffle(keywordList2)
keywordList1 = keywordList1[:100]
keywordList2 = keywordList2[:100]

for key, value in pyprind.prog_bar(data.items()):
	cutValue = jieba.lcut(value)
	cutKey = jieba.lcut(key[key.index(value)-1:key.index(value)+len(value)+1])
	for vocab1, vocab2 in zip(keywordList1, keywordList2):
		result.append({'key':[vocab1] + cutKey + [vocab2], 'value':cutValue})

json.dump(result, open('new.json', 'w'))