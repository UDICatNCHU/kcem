from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding, Dropout
from keras.preprocessing import sequence
from gensim import models
import numpy as np
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
index_dict = wordVecmodel.vocab
punctuationList = {
    '，':models.keyedvectors.Vocab(index=len(index_dict)),
    '、':models.keyedvectors.Vocab(index=len(index_dict)+1),
    '。':models.keyedvectors.Vocab(index=len(index_dict)+2),
}
index_dict.update(punctuationList)
vocab_dim = 400 # dimensionality of your word vectors
n_symbols = len(index_dict) + 1 # adding 1 to account for 0th index (for masking)
embedding_weights = np.zeros((n_symbols+1,vocab_dim))

reverseTable = {}
for word, index in index_dict.items():
    index = index.index + 1 # make index start from 1, lear (0 is reserved for the masking).
    try:
        embedding_weights[index,:] = wordVecmodel[word]
    except Exception as e:
        # for ，、。
        embedding_weights[index,:] = np.ones(400)
    reverseTable[str(index)] = word

model = Sequential() # or Graph or whatever
model.add(Embedding(trainable=False, output_dim=400, input_dim=n_symbols + 1, mask_zero=True, weights=[embedding_weights])) # note you have to put embedding weights in a list by convention
model.add(LSTM(400, return_sequences=True))
model.add(LSTM(400, return_sequences=False))
model.add(Dense(400, activation='relu'))
model.add(Dense(50, activation='relu'))
model.add(Dense(2, activation='relu')) # for this is the architecture for predicting the next word, but insert your own here
model.compile(loss='binary_crossentropy',
              optimizer='rmsprop',
              metrics=['accuracy'])

import json
from sklearn.model_selection import train_test_split

Data = json.load(open('wiki.json', 'r'))
X = []
y = []
for i in Data:
    tmp = []
    tmpAns = []
    for d in i['key']:
        try:
            tmp.append(index_dict[d].index + 1)
        except Exception as e:
            print("ignore "+d)
    for ans in i['value']:
        try:
            tmpAns.append(index_dict[ans].index + 1)
        except Exception as e:
            print("ignore "+ans)
    X.append(tmp)
    y.append([tmp.index(tmpAns[0])/10, tmp.index(tmpAns[-1])/10])

X = sequence.pad_sequences(X, maxlen=50, padding='post', truncating='post')
# x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
x_train = np.array(X)
x_test = np.array(X)
y_train = np.array(y)
y_test = np.array(y)

history = model.fit(x_train, y_train, batch_size=2, epochs=3)
score = model.evaluate(x_test, y_test, batch_size=2)
print(history.history)

for (index, i), d, (answer1, answer2) in zip(enumerate(x_train), Data, y_train):
    print(answer1, answer2)
    print(''.join([reverseTable[str(j)] for j in i if j !=0]))
    print(''.join([reverseTable[str(j)] for j in i[int(answer1*10):int(answer2*10+1)]]))
    answer = sorted([int(model.predict(x_train)[index][0])*10-1,int(model.predict(x_train)[index][1])*10+1])
    print(answer)
    print("My ans:::::", ''.join([reverseTable[str(j)] for j in i if j!=0])[answer[0]:answer[1]])