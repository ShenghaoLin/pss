import torch
import torch.nn as nn
import os
import sys
from nltk.tokenize import word_tokenize


# read from train/test data files and return the tuple as (label, original_sent, candsent, trendid)
def readInData(filename):

    data = []
    trends = set([])
    
    (trendid, trendname, origsent, candsent, judge, origsenttag, candsenttag) = (None, None, None, None, None, None, None)
    
    for line in open(filename):
        line = line.strip()
        #read in training or dev data with labels
        if len(line.split('\t')) == 7:
            (trendid, trendname, origsent, candsent, judge, origsenttag, candsenttag) = line.split('\t')
        #read in test data without labels
        elif len(line.split('\t')) == 6:
            (trendid, trendname, origsent, candsent, origsenttag, candsenttag) = line.split('\t')
        else:
            continue
        
        #if origsent == candsent:
        #    continue
        
        trends.add(trendid)
        
        if judge == None:
            data.append((judge, origsent, candsent, trendid))
            continue

        # ignoring the training/test data that has middle label 
        if judge[0] == '(':  # labelled by Amazon Mechanical Turk in format like "(2,3)"
            nYes = eval(judge)[0]            
            if nYes >= 3:
                amt_label = True
                data.append((amt_label, origsent, candsent, trendid))
            elif nYes <= 1:
                amt_label = False
                data.append((amt_label, origsent, candsent, trendid))   
        elif judge[0].isdigit():   # labelled by expert in format like "2"
            nYes = int(judge[0])
            if nYes >= 4:
                expert_label = True
                data.append((expert_label, origsent, candsent, trendid))
            elif nYes <= 2:
                expert_label = False
                data.append((expert_label, origsent, candsent, trendid))     
            else:
                expert_label = None
                data.append((expert_label, origsent, candsent, trendid))        
                
    return data, trends

def generate_dict(embedding_path):
    d = {}
    embedding_list = []
    with open(embedding_path, 'r', encoding='utf-8') as f:
        line = f.readline()
        idx = 1
        while line:
            try:
                k = line.split()
                embedding_dim = len(k[1:])
                a = [float(w) for w in k[1:]]
                d[k[0]] = idx
                idx += 1
                embedding_list.append(a)
            except:
                pass
            line = f.readline()
    tmp = []
    for i in range(len(embedding_list[0])):
        tmp.append(0)
    embedding_list = [tmp] + embedding_list
    embedding = nn.Embedding.from_pretrained(torch.tensor(embedding_list), padding_idx=0)

    print('Reading embedding finished.')
        
    return d, embedding


def padding(x, max_len=10000):
    max_len = 0
    for xx in x:
        if max_len < len(xx):
            max_len = len(xx)
    for i in range(len(x)):
        xx = x[i]
        kk = len(xx)
        x[i] = ([0] * (max_len - kk)) + xx
    return x


def preprocessing(embedding_path, input_path):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    d, embedding = generate_dict(embedding_path)
    x0 = []
    x1 = []
    y = []
    max_len = 0
    data, trends = readInData(input_path)

    for trend in trends:
        if trend[0] == True:
            x0.append(word_tokenize(trend[1]))
            x1.append(word_tokenize(trend[2]))
            y.append(0)
        elif trend[0] == False:
            x0.append(word_tokenize(trend[1]))
            x1.append(word_tokenize(trend[2]))
            y.append(1)

    max_len = 0
    for xx in x0 + x1:
        if max_len < len(xx):
            max_len = len(xx)
    print(x0)
    x0 = embedding.to(device)(torch.tensor(padding(x0, max_len=max_len)).to(device))    
    x1 = embedding.to(device)(torch.tensor(padding(x1, max_len=max_len)).to(device))    

    return x0, x1, torch.tensor(y, dtype=torch.float), embedding
