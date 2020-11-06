import sys
import time
import os 
import re
from collections import defaultdict
import math
import Stemmer
import nltk
import unicodedata
from nltk.corpus import stopwords

nltk.download('stopwords')
stop_words = stopwords.words('english')
stemmer = Stemmer.Stemmer('english')

f = open('titles.txt','r')
all_lines = f.readlines()
f.close()
doc_info = {}
for line in all_lines:
    doc_id, doc_name, max_freq = line.strip().split(" ~~ ")
    doc_info[doc_id] = [doc_name, max_freq]

N_doc = len(doc_info)
print("|N_doc|:"+str(N_doc))

field_weight = {'t': 500, 'b':25, 'c':10, 'i':100, 'r':2, 'e':1}
#field_weight = {'t' : 0.5, 'b': 0.1, 'c':0.08, 'i':0.25 , 'r':0.06 , 'e':0.01 }

def strip_accents(text):
    try:
        text = unicode(text, 'utf-8')
    except (TypeError, NameError):
        pass
    text = unicodedata.normalize('NFD', text)
    text = text.encode('ascii', 'ignore')
    text = text.decode("utf-8")
    return str(text)

def tokenize(text):
    tokens = re.split(r'[^A-Za-z0-9]+', text)
    curated = []
    for token in tokens:
        word = stemmer.stemWord(token.lower())
        if len(word) <= 1 or word in stop_words:
            continue
        curated.append(word)
    return curated

def get_id(text):
    ids = re.findall(r' [0-9]+ ', text)
    ids = [i_d.strip() for i_d in ids]
    return ids

def get_posting(text):
    posting_list = re.findall(r'-([^;]*)', text)
    posting_list = [post.strip() for post in posting_list]
    return posting_list

def tf(term_freq, max_freq):
    return 0.5 + 0.5*(term_freq/int(max_freq))#1+math.log(term_freq)

def idf(n_app):
    vanilla = N_doc/n_app
    return math.log(vanilla)

def tf_idf(term_freq, max_freq, n_app):
    return tf(term_freq, max_freq) * idf(n_app)


def retrieve_line(word):
    #f = open('test_index.txt', 'r')
    f = open('index/'+word[0]+'_index.txt','r')
    lines = f.readlines()
    f.close()
    for line in lines:
        if line.startswith(word+" :"):
            list1 = line.strip().split(" :")[1:]
            lis1 = ' '.join([str(elem) for elem in list1])
            return lis1

def process_queries(fields, queries, K):
    docids_list = []
    titles_list = []
    tfidf_list = []
    sorted_ids = []
    sorted_titles = []
    for ind,query in enumerate(queries):
        query = strip_accents(query)
        query_tok = tokenize(query)
        for each_query in query_tok:
            line = retrieve_line(each_query)
            if not line:
                continue
            doc_id_list = get_id(line)
            df_t = len(doc_id_list)
            posting_list = get_posting(line)
            if fields:
                field = fields[ind].split(":")[0]
                for index, posting in enumerate(posting_list):
                    if field in posting:
                        substr = field+ r'[0-9]* ' 
                        tf = re.findall(substr, posting)
                        if not tf:
                            continue
                        tf_td = int(tf[0].strip()[1:])
                        tf_idf_field_w = tf_idf(tf_td, doc_info[doc_id_list[index]][1], df_t)*field_weight[field]
                        tfidf_list.append(tf_idf_field_w)
                        docids_list.append(doc_id_list[index])
                        titles_list.append(doc_info[doc_id_list[index]][0])
            else:
                for index, posting in enumerate(posting_list):
                    weight = 0
                    for field in ['t','b','c','i','r','e']:
                        substr = field+ r'[0-9]* ' 
                        tf = re.findall(substr, posting)
                        if not tf:
                            continue
                        tf_td = int(tf[0].strip()[1:])
                        weight += tf_idf(tf_td, doc_info[doc_id_list[index]][1], df_t)*field_weight[field]
                    tfidf_list.append(weight)
                    docids_list.append(doc_id_list[index])
                    titles_list.append(doc_info[doc_id_list[index]][0])
    sort_index = sorted(range(len(tfidf_list)), reverse=True, key=lambda k: tfidf_list[k])
    for i in sort_index:
        sorted_ids.append(docids_list[i])
        sorted_titles.append(titles_list[i])
    
    return sorted_ids, sorted_titles
            


if __name__ == '__main__':
    fp = open(sys.argv[1],'r')
    queries = fp.readlines()
    fp.close()
    n = len(queries)
    with open('queries_op.txt',"w+") as f:
        for query in queries:
            query = query.strip()
            query_parse = query.split(', ')
            K = int(query_parse[0])
            qp = query_parse[1]
            regex = r'[ticber]:'
            fields_per_line = re.findall(regex, qp)
            queries_per_line = re.sub(regex, ' ', qp)
            queries_per_line = queries_per_line.split('  ')
            start_time = time.time()
            page_ids, page_titles = process_queries(fields_per_line, queries_per_line, K)
            if K > len(page_ids):
                length = len(page_ids)
            else:
                length = K
            end_time = time.time() - start_time
            for i in range(length):
                f.write(page_ids[i]+', '+page_titles[i]+'\n')
            f.write(str(end_time)+', '+str(end_time/n)+'\n\n')
        f.close()
