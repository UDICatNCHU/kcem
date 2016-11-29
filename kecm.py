# -*- coding: utf-8 -*-
import argparse,os.path,sys,re,subprocess
import requests
import time
import json
from datetime import datetime
import sys
import gensim
import multiprocessing
import time,operator

def kcm_search(word,kcmtop):#回傳kcm結果，由大到小排序，回傳kcmtop個字
	returnword=subprocess.check_output(['grep -w '+word+' ../Correlation_pair_20161110.model'], shell=True)
	returnword=returnword.split('\n')
	topic_dic={}
	sum=0
	for line in returnword:
		triple = line.split()
		if(len(triple)==3):
			if (triple[0]!=word.encode('utf8')):
				if(triple[0] in topic_dic):
					topic_dic[triple[0]]=topic_dic[triple[0]]+int(triple[2])
					sum=sum+int(triple[2])
				else:
					topic_dic[triple[0]]=int(triple[2])
					sum=sum+int(triple[2])
			else:
				if(triple[1] in topic_dic):
					topic_dic[triple[1]]=topic_dic[triple[1]]+int(triple[2])
					sum=sum+int(triple[2])
				else:
					topic_dic[triple[1]]=int(triple[2])
					sum=sum+int(triple[2])
	sorted_topic_dic = sorted(topic_dic.items(), key=operator.itemgetter(1),reverse=True)
	return sorted_topic_dic[0:kcmtop]

def kem_search(word):#回傳kem結果
	return model.most_similar(word.decode('utf8'),topn=50)



if __name__ == '__main__':
	model = gensim.models.Word2Vec.load('../kem/w2v_ch.model')
	parser = argparse.ArgumentParser(prog=os.path.basename(sys.argv[0]),
		formatter_class=argparse.RawDescriptionHelpFormatter,
		description=__doc__)

	parser.add_argument("input",help="input file.")
	kem_topn_num=30
	kcm_topn_num=50

	args = parser.parse_args()
	kcm_lists=[]
	count=0
	entity_word=args.input
	for kemtopn in kem_search(entity_word):#找kem前n個字，並丟入kcm
		temp=[]
		if count!=kem_topn_num:
			try:
				for kcmtopn in kcm_search(kemtopn[0],kcm_topn_num):
					temp.append(kcmtopn[0])
				count=count+1
			except:
				print 'not found'
			if len(temp)!=0:
				kcm_lists.append(temp)
		else:
			break
	entity={}
	for kcm_list in kcm_lists:#統計出現的字
		for word in kcm_list:
			if word in entity:
				entity[word]=entity[word]+1.0/float(kem_topn_num)
			else :
				entity[word]=1.0/float(kem_topn_num)
	sorted_entity = sorted(entity.items(), key=operator.itemgetter(1),reverse=True)
	for x in sorted_entity[0:10]:
		print x[0],x[1]