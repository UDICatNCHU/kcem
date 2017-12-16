from gensim import models
model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)

def criteria(mode, myans, key):
	selectRange = 5
	def cosSimilarity(x):
		try:
			return (x[0], model.similarity(key, x[0]))
		except Exception as e:
			pass

	if mode == 'w2v':
		myans = [i for i in myans if i[0] != key]
		myans = list(map(cosSimilarity, myans[:selectRange]))
		myans = [i for i in myans if i != None]
		myans = sorted(myans, key=lambda x:-x[1])
		return myans
	elif mode == 'kcem':
		return myans
	elif mode == 'hybrid':
		result = {}
		myans = [i for i in myans if i[0] != key]
		w2v = list(map(cosSimilarity, myans[:selectRange]))
		result = {i[0]:float(i[1]) for i in w2v if i != None}
		for i in myans[:selectRange]:
			result[i[0]] = result.setdefault(i[0], 0) + i[1]
		myans = sorted(result.items(), key=lambda x:-x[1])
		return myans