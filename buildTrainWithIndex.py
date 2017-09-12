from gensim import models
import json, pyprind, random
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)


result = []
data = json.load(open('wiki.json', 'r'))
keywordList1 = list(wordVecmodel.vocab.keys())
keywordList2 = list(wordVecmodel.vocab.keys())
random.shuffle(keywordList1)
random.shuffle(keywordList2)
keywordList1 = keywordList1[:100]
keywordList2 = keywordList2[:100]

for i in pyprind.prog_bar(data):
	for vocab1, vocab2 in zip(keywordList1, keywordList2):
		tmp = {}
		tmp['key'] = [vocab1] + i['key'][1:] + [vocab2]
		tmp['start'] = i['start']/10
		tmp['end'] = i['end']/10
		print(tmp)

		result.append(tmp)

result += data
json.dump(result, open('new.json', 'w'))