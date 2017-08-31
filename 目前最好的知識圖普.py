import seq2seq
from seq2seq.models import SimpleSeq2Seq

model = SimpleSeq2Seq(batch_input_shape=(1, 150, 400), hidden_dim=1, output_length=150, output_dim=400, depth=4)
model.compile(loss='mse', optimizer='rmsprop', metrics=['accuracy'])

import json, numpy
from sklearn.model_selection import train_test_split
X = json.load(open('wikiVecdata.json', 'r'))[:30]

y = json.load(open('wikiVeclabel.json', 'r'))[:30]
x_train, x_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=42)
x_train = numpy.array(x_train)
x_test = numpy.array(x_test)
y_train = numpy.array(y_train)
y_test = numpy.array(y_test)

history = model.fit(x_train, y_train,
          batch_size=1, epochs=5, shuffle=False,
          validation_data=(x_test, y_test))
print(history.history)