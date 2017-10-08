import requests, pyprind, json, sys
from gensim import models

model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
kcmNum = sys.argv[1]
kemNum = sys.argv[2]
loss = 0
total = 0

for key, ans in pyprind.prog_bar(json.load(open('Ontology_from_google.json', 'r')).items()):
	myans = requests.get('http://140.120.13.244:10000/kcem/?keyword={}&kcm={}&kem={}&lang=cht'.format(key, kcmNum, kemNum)).json()
	print(myans)
	if myans:
		myans = myans[0][0]
		try:
			total += 1
			loss += (1 - model.similarity(myans, ans))
		except Exception as e:
			continue

print("finish {} test, total loss is {}".format(total, loss / total))