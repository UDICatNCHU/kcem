import pyspark, re, json, sys
# import jieba
import jieba.posseg as pseg

conf = pyspark.SparkConf().setAll([('spark.rdd.compress', 'True'), ('spark.serializer.objectStreamReset', '100'), ('spark.app.id', 'local-1506663742168'), ('spark.master', 'local[*]'), ('spark.executor.id', 'driver'), ('spark.submit.deployMode', 'client'), ('spark.driver.memory', '40g'), ('spark.driver.port', '39072'), ('spark.app.name', 'PySparkShell'), ('spark.driver.host', '172.17.0.8'), ('spark.driver.memory', '75g')])
sc = pyspark.SparkContext(conf=conf)

with open(sys.argv[1], 'r') as f:
    file = f.read()
    data = re.findall(r'<.+?>.+?</doc>', file, re.S)
    del file

def preprocess_article(article):
    vocab = re.search(r'title=\"(.+?)\"', article).group(1)
    sentence = re.search(r'\>(.*)\<', article,re.S).group(1).split('\n\n')[1]
    return {"key":vocab, "value":list(set([i.word for i in pseg.lcut(sentence) if (i.flag.startswith('n') or i.flag == 'l') and i.flag != 'nr']))}

rdd = sc.parallelize(data)
result = rdd.map(preprocess_article).collect()
json.dump(result, open(sys.argv[2], 'w'))