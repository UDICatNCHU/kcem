import re, pyprind
from train_punctuation import KCEM_trainer

k = KCEM_trainer(loss='mse', optimizer='adam', activation='sigmoid', epoch=None)

with open('wiki/KCM-Data-Source-Extractor/WikiPedia/wiki.txt.all', 'r') as f:
	file = f.read()
	data = re.findall(r'<.+?>.+?</doc>', file, re.S)
	del file
	result = []
	for article in data:
		vocab = re.search(r'title=\"(.+?)\"', article).group(1)
		sentence = re.search(r'\>(.*)\<', article,re.S).group(1).split('\n\n')[1]
		ans = k.test(int(168), sentence)

		result.append({vocab:ans})