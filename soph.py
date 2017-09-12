import os, re, click
import numpy as np
from keras.layers.recurrent import GRU
from keras.layers.wrappers import TimeDistributed
from keras.models import Sequential, model_from_json
from keras.layers.core import Dense, RepeatVector
import json, jieba, pickle
from itertools import chain
jieba.load_userdict(os.path.join("dictionary", "NameDict_Ch_v2"))

MODEL_PATH = './'

MODEL_STRUCT_FILE = 'seq2seq.json'
MODEL_WEIGHTS_FILE = 'seq2seq_weights.h5'

BEGIN_SYMBOL = '^'
END_SYMBOL = '$'
MAX_INPUT_LEN = 100
MAX_OUTPUT_LEN = 60

from gensim import models
wordVecmodel = models.KeyedVectors.load_word2vec_format('med400.model.bin.punctuation', binary=True)
print(wordVecmodel['，'])
DIM_NUM = 400
def removeStopWords(key_and_value):
    value, key = key_and_value
    value = jieba.lcut(value.replace('\n', '').strip())
    return [{'key':jieba.lcut(k.replace('\n', '').strip()), 'value':value} for k in key]


def vectorize(sentence, seq_len):
    vec = np.zeros((seq_len, 400), dtype=int)
    for i, word in enumerate(sentence):
        try:
            vec[i,:] = wordVecmodel[word]
        except Exception as e:
            pass
    for i in range(len(sentence), seq_len):
        vec[i,:] = wordVecmodel[END_SYMBOL]
    return vec


def build_data():
    try:
        train_x, train_y = pickle.load(train_x, open('train_x.pickle', 'rb')), pickle.load(train_y, open('train_y.pickle', 'rb'))        
    except Exception as e:
        sentences = json.load(open('new.json','r'))
        print('=======start append begin symbol========')
        plain_x = []
        plain_y = []
        for word in sentences:
            plain_x.append([BEGIN_SYMBOL] + word['key'])
            plain_y.append([BEGIN_SYMBOL] + word['value'])

        SenLen = len(sentences)
        del sentences

        print('=======start building numpy array=======')
        # train_x 和 train_y 必须是 3-D 的数据
        train_x = np.zeros((SenLen, MAX_INPUT_LEN, 400), dtype=int)
        train_y = np.zeros((SenLen, MAX_OUTPUT_LEN, 400), dtype=int)
        for i in range(SenLen):
            train_x[i] = vectorize(plain_x[i], MAX_INPUT_LEN)
            train_y[i] = vectorize(plain_y[i], MAX_OUTPUT_LEN)

        del plain_x
        del plain_y

        pickle.dump(train_x, open('train_x.pickle', 'wb'))
        pickle.dump(train_y, open('train_y.pickle', 'wb'))
    return train_x, train_y


def build_model_from_file(struct_file, weights_file):
    model = model_from_json(open(struct_file, 'r').read())
    model.compile(loss="mse", optimizer='adam')
    model.load_weights(weights_file)
    return model


def build_model(input_size, seq_len, hidden_size):
    """建立一个 sequence to sequence 模型"""
    model = Sequential()
    model.add(GRU(input_dim=input_size, output_dim=hidden_size, return_sequences=True))
    model.add(GRU(output_dim=hidden_size, return_sequences=False))
    model.add(Dense(hidden_size, activation="relu"))
    model.add(RepeatVector(seq_len))
    model.add(GRU(hidden_size, return_sequences=True))
    model.add(GRU(hidden_size, return_sequences=True))
    model.add(TimeDistributed(Dense(output_dim=input_size, activation="linear")))
    model.compile(loss="mse", optimizer='adam',
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
    x, y = build_data()
    indices = int(len(x) / 10)
    test_x = x[:indices]
    test_y = y[:indices]
    train_x = x[indices:]
    train_y = y[indices:]
    model = build_model(DIM_NUM, MAX_OUTPUT_LEN, 200)
    model.fit(train_x, train_y, validation_data=(test_x, test_y), batch_size=128, nb_epoch=epoch)
    struct_file = os.path.join(model_path, MODEL_STRUCT_FILE)
    weights_file = os.path.join(model_path, MODEL_WEIGHTS_FILE)
    save_model_to_file(model, struct_file, weights_file)


@cli.command()
@click.option('-m', '--model_path', default=os.path.join(MODEL_PATH), help='model files to read')
@click.argument('sentence')
def test(model_path, sentence):
    struct_file = os.path.join(model_path, MODEL_STRUCT_FILE)
    weights_file = os.path.join(model_path, MODEL_WEIGHTS_FILE)
    model = build_model_from_file(struct_file, weights_file)
    x = np.array([vectorize(jieba.lcut(sentence.replace('\n', '').strip()), MAX_INPUT_LEN), ])
    pred = model.predict(x)[0]
    print(pred)
    for i in pred:
        print(wordVecmodel.similar_by_vector(i)[0][0], end='')

if __name__ == '__main__':
    cli()
