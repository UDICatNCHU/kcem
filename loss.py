import requests, pyprind, json, sys
from gensim import models

model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
data = json.load(open('Ontology_from_google.json', 'r')).items()
file = {}

def criteria(mode, myans):
	if mode == 'w2v':
		myans = [i for i in myans if i[0] != key]
		myans = list(map(cosSimilarity, myans[:3]))
		myans = [i for i in myans if i != None]
		myans = sorted(myans, key=lambda x:-x[1])
		return myans[0][0]
	elif mode == 'kcem':
		return myans[0][0]
	elif mode == 'hybrid':
		result = {}
		myans = [i for i in myans if i[0] != key]
		w2v = list(map(cosSimilarity, myans[:3]))
		result = {i[0]:float(i[1]) for i in w2v if i != None}
		for i in myans[:3]:
			result[i[0]] = result.setdefault(i[0], 0) + i[1]
		myans = sorted(result.items(), key=lambda x:-x[1])
		return myans[0][0]


for kcmNum in range(2, 30):
	for kemNum in range(1, 30):
		loss = 0
		total = 0

		for key, ans in pyprind.prog_bar(data):
			myans = requests.get('http://140.120.13.244:10000/kcem/?keyword={}&kcm={}&kem={}&lang=cht'.format(key, kcmNum, kemNum)).json()

			def cosSimilarity(x):
				global key
				try:
					return (x[0], model.similarity(key, x[0]))
				except Exception as e:
					pass
			if myans:
				print(myans)
				myans = criteria(sys.argv[1], myans)
				try:
					total += 1
					loss += ((1-float(model.similarity(myans, ans)))*10)**2
				except Exception as e:
					print(e)
					continue

		print("finish {} test, total loss is {}".format(total, loss / total))
		file['{}-{}'.format(kcmNum, kemNum)] = loss / total

json.dump(file, open('kcem.loss.json','w'))