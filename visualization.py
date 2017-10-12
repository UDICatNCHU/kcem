import matplotlib.pyplot as plt
import json

def function(mode, color, label=''):
	tmp = {}
	for key, item in json.load(open(mode, 'r')).items():
		tmp.setdefault(key.split('-')[0], []).append(item)
	for index, i in enumerate(tmp):
		if index == 0:
			plt.plot(range(2, 30, 2), tmp[i], color = color, label=label)
		plt.plot(range(2, 30, 2), tmp[i], color = color)


function('kcemLoss/kcem.loss.hybrid.json', 'b', 'hybrid')
function('kcemLoss/kcem.loss.kcem.json', 'r', 'kcem')
function('kcemLoss/kcem.loss.w2v.json', 'y', 'w2v')
function('kcemLoss/kcem.new.method.json', 'g', 'new method')
plt.title('Train History')
plt.ylabel('Loss')
plt.xlabel('kem')
plt.legend(loc='upper left')
plt.show()