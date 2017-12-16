import matplotlib.pyplot as plt
import json, sys
import numpy as np
from collections import *

def function(mode, color, label='', Mission='separate'):
	tmp = defaultdict(OrderedDict)
	for key, item in json.load(open(mode, 'r')).items():
		tmp[key.split('-')[0]][key] = item

	for i in tmp:
		print(i, sorted(tmp[i].items(), key=lambda x:int(x[0].split('-')[-1])))
		tmp[i] = [j[1] for j in sorted(tmp[i].items(), key=lambda x:int(x[0].split('-')[-1]))]

	if Mission == 'separate':
		for index, i in enumerate(tmp):
			plt.plot(range(2, 30, 2), tmp[i], label=i)
	elif Mission == 'all':
		for index, i in enumerate(tmp):
			if index == 0:
				plt.plot(range(2, 30, 2), tmp[i], color=color, label=label)
			plt.plot(range(2, 30, 2), tmp[i], color=color)

	else:
		zeros = np.zeros(len(range(2, 30, 2)))
		for index, i in enumerate(tmp):
			zeros += np.array(tmp[i])
		zeros /= len(range(2, 30, 2))
		plt.plot(range(2, 30, 2), zeros, color = color, label=label)


function('kcemLoss/kcem.loss.hybrid.json', 'b', 'hybrid', sys.argv[1])
function('kcemLoss/kcem.loss.kcem.json', 'r', 'kcem', sys.argv[1])
function('kcemLoss/kcem.loss.w2v.json', 'y', 'w2v', sys.argv[1])
function('kcemLoss/kcem.new.method.json', 'g', 'new method', sys.argv[1])
plt.title('Train History')
plt.ylabel('Loss')
plt.xlabel('kem')
plt.legend(loc='upper left')
plt.show()