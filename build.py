import pyspark, re, json, sys
import jieba.posseg as pseg
from train_punctuation import KCEM_trainer

conf = pyspark.SparkConf().setAll([('spark.driver.memory', '65g'), ('spark.driver.host', '172.17.0.21'), ('spark.app.id', 'local-1492693477461'), ('spark.rdd.compress', 'True'), ('spark.serializer.objectStreamReset', '100'), ('spark.master', 'local[*]'), ('spark.executor.id', 'driver'), ('spark.submit.deployMode', 'client'), ('spark.driver.port', '39274'), ('spark.app.name', 'PySparkShell')])
sc = pyspark.SparkContext(conf=conf)

k = KCEM_trainer(loss='mse', optimizer='adam', activation='sigmoid', epoch=None)

with open(sys.argv[1], 'r') as f:
    file = f.read()
    data = re.findall(r'<.+?>.+?</doc>', file, re.S)
    del file

def preprocess_article(article):
    vocab = re.search(r'title=\"(.+?)\"', article).group(1)
    sentence = re.search(r'\>(.*)\<', article,re.S).group(1).split('\n\n')[1]
    ans = k.test(int(168), sentence)
    return {vocab:ans}

rdd = sc.parallelize(data)
result = rdd.map(preprocess_article).collect()
json.dump(result, open(sys.argv[2], 'w'))