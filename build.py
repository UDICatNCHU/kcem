import pyspark, re, json
import jieba.posseg as pseg
from train_punctuation import KCEM_trainer

conf = pyspark.SparkConf().setAll([('spark.rdd.compress', 'True'), ('spark.serializer.objectStreamReset', '100'), ('spark.master', 'local[*]'), ('spark.executor.id', 'driver'), ('spark.submit.deployMode', 'client'), ('spark.driver.port', '39042'), ('spark.driver.memory', '70g'), ('spark.driver.host', '172.17.0.8')]
)
sc = pyspark.SparkContext(conf=conf)

k = KCEM_trainer(loss='mse', optimizer='adam', activation='sigmoid', epoch=None)

with open('wiki.txt.all', 'r') as f:
    file = f.read()
    data = re.findall(r'<.+?>.+?</doc>', file, re.S)
    del file

def preprocess_article(article):
    vocab = re.search(r'title=\"(.+?)\"', article).group(1)
    sentence = re.search(r'\>(.*)\<', article,re.S).group(1).split('\n\n')[1]
    ans = k.test(int(168), sentence)
    return {vocab:ans}
rdd = sc.parallelize(data)
del data
result = rdd.map(preprocess_article).collect()
json.dump(result, open('wiki.keras.json'))
    # result = []
    # for article in data:
    #     vocab = re.search(r'title=\"(.+?)\"', article).group(1)
    #     sentence = re.search(r'\>(.*)\<', article,re.S).group(1).split('\n\n')[1]
    #     ans = k.test(int(168), sentence)

    #     result.append({vocab:ans})
