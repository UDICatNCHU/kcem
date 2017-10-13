import requests, pyprind, json, sys
from gensim import models
from utils import criteria

def main(kcmNum, kemNum):
	loss = 0
	total = 0

	for key, ans in pyprind.prog_bar(data):
		myans = requests.get('http://140.120.13.244:10000/kcem/?keyword={}&kcm={}&kem={}&lang=cht'.format(key, kcmNum, kemNum)).json()

		if myans:
			myans = criteria(sys.argv[1], myans, key)
			try:
				total += 1
				loss += ((1-float(model.similarity(myans, ans)))*10)**2
			except Exception as e:
				print(e)
				continue
	return loss, total

if __name__ == '__main__':
	model = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
	data = json.load(open('Ontology_from_google.json', 'r')).items()
	file = {}

	for kcmNum in range(2, 30, 2):
		for kemNum in range(2, 30, 2):
			loss, total = main(kcmNum, kemNum)
			print("finish {} test, total loss is {}".format(total, loss / total))
			file['{}-{}'.format(kcmNum, kemNum)] = loss / total
	json.dump(file, open(sys.argv[2],'w'))