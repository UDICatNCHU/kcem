from keras.models import Sequential
from keras.layers import Dense, LSTM, Embedding, Dropout
from keras.preprocessing import sequence
from gensim import models
import numpy as np
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin', binary=True)
index_dict = wordVecmodel.vocab
vocab_dim = 400 # dimensionality of your word vectors
n_symbols = len(index_dict) + 1 # adding 1 to account for 0th index (for masking)
embedding_weights = np.zeros((n_symbols+1,vocab_dim))

reverseTable = {}
for word, index in index_dict.items():
    index = index.index
    embedding_weights[index,:] = wordVecmodel[word]
    reverseTable[str(index)] = word

model = Sequential() # or Graph or whatever
model.add(Embedding(output_dim=400, input_dim=n_symbols + 1, mask_zero=True, weights=[embedding_weights])) # note you have to put embedding weights in a list by convention
model.add(LSTM(100, return_sequences=False))  
model.add(Dropout(0.5))
model.add(Dense(2, activation='relu')) # for this is the architecture for predicting the next word, but insert your own here
model.compile(loss='binary_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

import json
from sklearn.model_selection import train_test_split

Data = json.load(open('wiki知識圖譜.json', 'r'))
X = []
for i in Data:
    tmp = []
    for j in i['data']:
        try:
            tmp.append(index_dict[j].index)
        except Exception as e:
            pass
    X.append(tmp)

X = sequence.pad_sequences(X, maxlen=200, padding='post', truncating='post')
y = [i['answer'] for i in Data]
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
x_train = np.array(x_train)
x_test = np.array(x_test)
y_train = np.array(y_train)
y_test = np.array(y_test)

history = model.fit(x_train, y_train, batch_size=2, epochs=10)
score = model.evaluate(x_test, y_test, batch_size=2)
print(history.history)

print(''.join([reverseTable[str(i)] for i in x_test[5]])[int(model.predict(x_test)[5][0])-1:int(model.predict(x_test)[5][1])+1])
