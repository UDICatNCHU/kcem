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
from keras.layers.core import Dense, RepeatVector, Dropout, Flatten
from keras.preprocessing import sequence
from keras.preprocessing.text import Tokenizer
from itertools import chain

class KCEM_trainer(object):
    """docstring for KCEM_trainer"""
    MODEL_STRUCT_FILE = 'seq2seq.json'
    MODEL_WEIGHTS_FILE = 'seq2seq_weights_start.h5'
    def __init__(self, loss, optimizer, activation, epoch):
        self.loss = loss
        self.optimizer = optimizer
        self.activation = activation
        self.epoch = epoch

        self.history = ''

        Data = json.load(open('ttt.json','r'))
        self.token = Tokenizer(num_words=2000)
        self.token.fit_on_texts(map(lambda x:' '.join(x['key']), Data))
        random.shuffle(Data)
        self.trainData, self.testData = Data[:int(len(Data)*0.7)], Data[int(len(Data)*0.7):]



    def build_data(self, max_length):
        print('=======build data========')
        self.dimension = max(self.token.word_index.values(), key=lambda x:x)
        print('max dimension is ' + str(self.dimension))

        x_train_seq = self.token.texts_to_sequences(map(lambda x:' '.join(x['key']), self.trainData))
        x_test_seq = self.token.texts_to_sequences(map(lambda x:' '.join(x['key']), self.testData))

        x_train = sequence.pad_sequences(x_train_seq, maxlen=max_length, padding='post', truncating='post')
        x_test = sequence.pad_sequences(x_test_seq, maxlen=max_length, padding='post', truncating='post')

        y_train = np.array([ (i['start_normalize'], i['end_normalize']) for i in self.trainData])
        y_test = np.array([ (i['start_normalize'], i['end_normalize']) for i in self.testData])
        return x_train, x_test, y_train, y_test

    def build_model_from_file(self, struct_file, weights_file):
        model = model_from_json(open(struct_file, 'r').read())
        model.compile(loss=self.loss, optimizer=self.optimizer)
        model.load_weights(weights_file)
        return model


    def build_model(self, hidden_size, max_length):
        """建立一个 sequence to sequence 模型"""
        model = Sequential()
        model.add(Embedding(output_dim=hidden_size, input_dim=self.dimension+1, input_length=max_length))
        model.add(GRU(output_dim=hidden_size, return_sequences=True))
        model.add(GRU(output_dim=hidden_size, return_sequences=True))
        model.add(TimeDistributed(Dense(hidden_size)))
        model.add(Flatten())
        model.add(Dense(hidden_size, activation=self.activation))
        model.add(Dropout(0.5))
        model.add(Dense(hidden_size, activation=self.activation))
        model.add(Dropout(0.5))
        model.add(Dense(2, activation=self.activation))
        model.compile(loss=self.loss, optimizer=self.optimizer,
                  metrics=['accuracy'])
        return model

    @staticmethod
    def save_model_to_file(model, struct_file, weights_file):
        # save model structure
        model_struct = model.to_json()
        open(struct_file, 'w').write(model_struct)
        # save model weights
        model.save_weights(weights_file, overwrite=True)

    def train(self, max_length):
        from keras import backend as K
        x_train, x_test, y_train, y_test = self.build_data(max_length)
        model = self.build_model(200, max_length)
        print(model.summary())
        self.train_history = model.fit(x_train, y_train, validation_data=(x_test, y_test), batch_size=128, nb_epoch=self.epoch)
        struct_file = os.path.join('./', self.MODEL_STRUCT_FILE)
        weights_file = os.path.join('./', self.MODEL_WEIGHTS_FILE)
        self.save_model_to_file(model, struct_file, weights_file)

        pred = model.predict(x_test)

        for (start, end), sentence in zip(pred, self.testData):
            sentenceCut = [i.word for i in pseg.lcut(sentence['raw'])]
            print(''.join(sentenceCut[int(round(start*len(sentenceCut))):int(round(end*len(sentenceCut)))]), end="\n\n")
        K.clear_session()

    def test(sentence, max_length):
        from keras import backend as K

        struct_file = os.path.join('./', self.MODEL_STRUCT_FILE)
        weights_file = os.path.join('./', self.MODEL_WEIGHTS_FILE)
        model = self.build_model_from_file(struct_file, weights_file)

        newsentence = pseg.lcut(sentence)
        sentenceCut = [' '.join([i.flag for i in newsentence])]
        test = self.token.texts_to_sequences(sentenceCut)
        test = sequence.pad_sequences(test, maxlen=max_length, padding='post', truncating='post')
        pred = model.predict(test)[0]
        print(round(pred[0]*len(sentenceCut[0])))

        newsentence = [i.word for i in newsentence]
        print(''.join(newsentence[int(round(pred[0]*len(newsentence))):int(round(pred[1]*len(newsentence)))]))
        K.clear_session()

    def show_train_history(self, train_acc,test_acc):
        import matplotlib.pyplot as plt
        plt.plot(self.train_history.history[train_acc])
        plt.plot(self.train_history.history[test_acc])
        plt.title('Train History')
        plt.ylabel('Loss')
        plt.xlabel('Epoch')
        plt.legend(['train', 'test'], loc='upper left')
        plt.show()


if __name__ == '__main__':
    @click.group()
    def cli():
        pass

    @cli.command()
    @click.option('--maxlen', help='number of epoch to train model')
    @click.option('--sentence', help='number of epoch to train model')
    def test(maxlen, sentence):
        k = KCEM_trainer(loss='mse', optimizer='adam', activation='sigmoid')

    @cli.command()
    @click.option('--epoch', default=100, help='number of epoch to train model')
    @click.option('--maxlen', default=100, help='number of epoch to train model')
    def train(epoch, maxlen):
        k = KCEM_trainer(loss='mse', optimizer='adam', activation='sigmoid', epoch=epoch)
        k.train(int(maxlen))
        k.show_train_history('loss','val_loss')

    cli()