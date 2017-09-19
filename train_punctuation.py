import os, re, click, json, pickle, random
import jieba.posseg as pseg
import jieba
stopwords = json.load(open('stopwords.json', 'r'))
jieba.load_userdict(os.path.join('dictionary', 'dict.txt.big.txt'))
jieba.load_userdict(os.path.join("dictionary", "NameDict_Ch_v2"))

import numpy as np
from keras.layers.embeddings import Embedding
from keras.layers.recurrent import GRU
from keras.layers.wrappers import TimeDistributed
from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, RepeatVector
from keras.preprocessing import sequence
from keras.preprocessing.text import Tokenizer
from itertools import chain

MODEL_PATH = './'

MODEL_STRUCT_FILE = 'seq2seq.json'
MODEL_WEIGHTS_FILE = 'seq2seq_weights_start.h5'
Data = json.load(open('ttt.json','r'))
token = Tokenizer(num_words=2000)
token.fit_on_texts(map(lambda x:' '.join(x['key']), Data))
random.shuffle(Data)
# train, test = Data, Data
trainData, testData = Data[:int(len(Data)*0.7)], Data[int(len(Data)*0.7):]

def build_data():
    print('=======build data========')
    dimension = max(token.word_index.values(), key=lambda x:x)
    print('max dimension is ' + str(dimension))

    x_train_seq = token.texts_to_sequences(map(lambda x:' '.join(x['key']), trainData))
    x_test_seq = token.texts_to_sequences(map(lambda x:' '.join(x['key']), testData))

    x_train = sequence.pad_sequences(x_train_seq, maxlen=125, padding='post', truncating='post')
    x_test = sequence.pad_sequences(x_test_seq, maxlen=125, padding='post', truncating='post')

    y_train = np.array([ (i['start']/len(i['key']), i['end']/len(i['key'])) for i in trainData])
    y_test = np.array([ (i['start']/len(i['key']), i['end']/len(i['key'])) for i in testData])
    return x_train, x_test, y_train, y_test, dimension


def build_model_from_file(struct_file, weights_file):
    model = model_from_json(open(struct_file, 'r').read())
    model.compile(loss="mean_squared_error", optimizer='adam')
    model.load_weights(weights_file)
    return model


def build_model(hidden_size):
    """建立一个 sequence to sequence 模型"""
    model = Sequential()
    model.add(Embedding(output_dim=hidden_size, input_dim=43+1, input_length=125))
    model.add(GRU(output_dim=hidden_size, return_sequences=True))
    model.add(GRU(output_dim=hidden_size, return_sequences=False))
    model.add(Dense(hidden_size, activation="sigmoid"))
    model.add(Dense(hidden_size, activation="sigmoid"))
    model.add(Dense(2, activation="sigmoid"))
    model.compile(loss="mean_squared_error", optimizer='adam',
              metrics=['accuracy'])
    return model


def save_model_to_file(model, struct_file, weights_file):
    # save model structure
    model_struct = model.to_json()
    open(struct_file, 'w').write(model_struct)
    # save model weights
    model.save_weights(weights_file, overwrite=True)


@click.group()
def cli():
    pass


@cli.command()
@click.option('--epoch', default=100, help='number of epoch to train model')
@click.option('-m', '--model_path', default=os.path.join(MODEL_PATH), help='model files to save')
def train(epoch, model_path):
    from keras import backend as K
    x_train, x_test, y_train, y_test, dimension = build_data()
    model = build_model(200)
    model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=128, nb_epoch=epoch)
    struct_file = os.path.join(model_path, MODEL_STRUCT_FILE)
    weights_file = os.path.join(model_path, MODEL_WEIGHTS_FILE)
    save_model_to_file(model, struct_file, weights_file)

    pred = model.predict(x_test)

    for (start, end), sentence in zip(pred, testData):
        sentenceCut = [i.word for i in pseg.lcut(sentence['raw'])]
        print(''.join(sentenceCut[int(round(start*len(sentenceCut))):int(round(end*len(sentenceCut)))]))
    K.clear_session()


@cli.command()
@click.option('-m', '--model_path', default=os.path.join(MODEL_PATH), help='model files to read')
@click.argument('sentence')
def test(model_path, sentence):
    from keras import backend as K

    struct_file = os.path.join(model_path, MODEL_STRUCT_FILE)
    weights_file = os.path.join(model_path, MODEL_WEIGHTS_FILE)
    model = build_model_from_file(struct_file, weights_file)

    newsentence = pseg.lcut(sentence)
    sentenceCut = [' '.join([i.flag for i in newsentence])]
    test = token.texts_to_sequences(sentenceCut)
    test = sequence.pad_sequences(test, maxlen=125, padding='post', truncating='post')
    pred = model.predict(test)[0]
    print(round(pred[0]*len(sentenceCut[0])))

    newsentence = [i.word for i in newsentence]
    print(''.join(newsentence[int(round(pred[0]*len(newsentence))):int(round(pred[1]*len(newsentence)))]))
    K.clear_session()

if __name__ == '__main__':
    cli()