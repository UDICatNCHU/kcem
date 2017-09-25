import jieba
import jieba.posseg as pseg
import random, json, jieba, os, sys
from itertools import dropwhile
from gensim import models
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin.punctuation', binary=True)

stopwords = json.load(open('stopwrds/stopwords.json', 'r'))
jieba.load_userdict(os.path.join('dictionary', 'dict.txt.big.txt'))
jieba.load_userdict(os.path.join("dictionary", "NameDict_Ch_v2"))

data = json.load(open(sys.argv[1], 'r'))
use_word2vec = bool(sys.argv[3])

length = []
endIndex = []
result = []
for key, value in data.items():
	length.append(key.index(value)+len(value))

	tmp = {}
	if use_word2vec:
		tmp['key'] = [i for i in jieba.cut(key) if i in wordVecmodel]
		value = ''.join([i for i in jieba.cut(value) if i in wordVecmodel])
		tmp['raw'] = tmp['key']

		tmp['start'] = 0
		for i in range(len(tmp['key'])):
			if value not in ''.join(map(lambda x:x, tmp['key'][i:])): 
				tmp['start'] = i-1
				break

		tmp['end'] = 0
		for i in reversed(range(len(tmp['key']))):
			if value not in ''.join(map(lambda x:x, tmp['key'][:i+1])): 
				tmp['end'] = i+2
				break

		print(tmp['end'])
		endIndex.append(tmp['end'])

		if value != ''.join(map(lambda x:x, tmp['key'][tmp['start']:tmp['end']])):
			print(value, '-------------', ''.join(map(lambda x:x, tmp['key'][tmp['start']:tmp['end']])))
			raise "error"

	else:
		tmp['key'] = pseg.lcut(key)
		tmp['key'] = list(map(lambda x:x.flag, tmp['key']))
		tmp['raw'] = key

		tmp['start'] = 0
		for i in range(len(tmp['key'])):
			if value not in ''.join(map(lambda x:x.word, tmp['key'][i:])): 
				tmp['start'] = i-1
				break

		tmp['end'] = 0
		for i in reversed(range(len(tmp['key']))):
			if value not in ''.join(map(lambda x:x.word, tmp['key'][:i+1])): 
				tmp['end'] = i+2
				break
		endIndex.append(tmp['end'])

		if value != ''.join(map(lambda x:x.word, tmp['key'][tmp['start']:tmp['end']])):
			print(value, '-------------', ''.join(map(lambda x:x.word, tmp['key'][tmp['start']:tmp['end']])))
			raise "error"

	tmp['start_normalize'] = tmp['start'] / len(tmp['key'])
	tmp['end_normalize'] = tmp['end'] / len(tmp['key'])
	print(tmp['start_normalize'], tmp['end_normalize'])
	result.append(tmp)

json.dump(result, open(sys.argv[2], 'w'))
print("min length of characters need to be at least: {}".format(str(max(length))))
print("min length of lstm input need to be at least: {}".format(str(max(endIndex))))