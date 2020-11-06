#!/usr/bin/python
import xml.sax 
import sys
import Stemmer
import nltk
from nltk.corpus import stopwords
from tqdm import tqdm
import re
import os
import time

inv_index = {}
#total_pages = 0
#Preprocessing of text
stemmer = Stemmer.Stemmer('english')
nltk.download('stopwords')
stop_words = stopwords.words('english')
def tokenize(text):
    preprocessed = []
    tokens = re.split(r'[^A-Za-z0-9]+', text)
    for token in tokens:
        word = stemmer.stemWord(token.lower())
        if len(word) <= 1 or word in stop_words:
            continue
        preprocessed.append(word)
    return preprocessed


#Parse out title, body, categories,infobox(and within infobox), references, links
def parse_categories(text):
    categories = re.findall(r"\[\[Category:(.*)\]\]", text, flags=re.IGNORECASE)
    if len(categories) <= 1:
        return []
    categories_list = []
    for category in categories:
        categories_list += tokenize(category)
    
    return categories_list
    
      
def parse_infoboxes(text):
    infoboxes = re.split(r'\{\{\s?Infobox', text, flags=re.IGNORECASE)
    if len(infoboxes) <= 1:
        return []

    infoboxes_list = []
    for index in range(1,len(infoboxes)):
        each_infobox = infoboxes[index].split("\n")
        for lines in each_infobox:
            if lines == "}}":
                break
            infoboxes_list += tokenize(lines)
    return infoboxes_list



def parse_references(text):
    references = re.split(r'\=\=\s?References\s?\=\=', text)
    reduced_text = references[0]
    if len(references) <= 1:
        return [] , reduced_text
    
    references_list = []
    references = references[1].split('\n')
    for lines in references:
        if ("[[Category" in lines) or ("==" in lines) or ("DEFAULTSORT" in lines):
            break
        line = tokenize(lines)
        if "Reflist" in line:
            line.remove("Reflist")
        if "reflist" in line:
            line.remove("reflist")
        references_list += line
 
    return references_list, reduced_text

def parse_links(text):
    links = re.split(r'\=\=\s?External links\s?\=\=', text)
    if len(links) <= 1:
        return []
    
    links_list = []
    links = links[1].split("\n")
    for lines in links:
        if lines and ('*' in lines ):
            links_list += tokenize(lines)
    
    return links_list

#Form a field ( F : index )
def create_field(key_tokens, key_index, page_id):
    for token in key_tokens:
        
        #['t', 'b', 'c', 'i', 'r', 'e']
        keys = [0, 0, 0, 0, 0, 0]
        if token not in inv_index:
            keys[key_index] += 1
            inv_index[token] = {}
            inv_index[token][page_id] = keys
        else:
            old = inv_index[token]
            if page_id not in old:
                keys[key_index] += 1
                inv_index[token][page_id] = keys
            else:
                old = old[page_id]
                old[key_index] += 1
                inv_index[token][page_id] = old

        
#Inverted Index construction
def mk_inv_index(title, text, page_id):
    title_tok = tokenize(title)
    create_field(title_tok, 0, page_id)
    reference_tok, reduced_text = parse_references(text)
    body = re.sub(r'\{\{\s?Infobox[\s\S]*\}\}\n', ' ', reduced_text, flags=re.IGNORECASE)
    body_tok = tokenize(body)
    create_field(body_tok, 1, page_id)
    category_tok = parse_categories(text)
    create_field(category_tok, 2, page_id)
    infobox_tok = parse_infoboxes(text)
    create_field(infobox_tok, 3, page_id)
    create_field(reference_tok, 4, page_id)
    link_tok = parse_links(text)
    create_field(link_tok, 5, page_id)
    doc_words = len(title_tok) + len(reference_tok) + len(category_tok) + len(body_tok) + len(infobox_tok) + len(link_tok)
    return doc_words 

#write inverted index to disk
def write_to_disk(titles, total_words):
    #     t=title b=body c=category i=infobox r=reference e=external links
    key_names = ['t', 'b', 'c', 'i', 'r', 'e']
    sorted_index = sorted(inv_index.keys())
    with open(sys.argv[2]+'_index.txt','w+') as f:
        for ind, word in enumerate(sorted_index):
            string = str(word) + " : "
            for each_page in inv_index[word]:
                pointer = inv_index[word][each_page]
                string += str(each_page) + " - "
                for index, frequency in enumerate(pointer):
                    if frequency > 0:
                        string += str(key_names[index])+str(frequency) + " "
                string += "; " 
            f.write(string+'\n')
        f.close()

    with open(sys.argv[2]+'_titles.txt','w+') as f:
        for title_id, title_name in titles.items():
            string = str(title_id) + " ~~ " + str(title_name) + " ~~ " + str(total_words[title_id])
            f.write(string+"\n")
        f.close()

class PageHandler(xml.sax.ContentHandler):
    
    def __init__(self):
        self.current_data = ""
        self.current_title = ""
        self.current_text = ""
        self.total_pages = 0
        self.block_titles = {}
        self.block_total = {}
        self.id_flag = True
    def startElement(self, tag, attributes):
        self.current_data = ""
        if tag == "page":
            self.total_pages += 1
        if tag == "id" and self.id_flag:
            self.page_id = ""
        if tag == "revision":
            self.id_flag = False
        if tag == "title":
            self.current_title = ""
        if tag == "text":
            self.current_text =  ""

    def endElement(self, tag):
        if tag == "page":
            total_word = mk_inv_index(self.current_title, self.current_text, self.page_id)
            self.block_total[self.page_id] = total_word
        elif tag == "revision":
            self.id_flag = True
        elif tag == "title":
            self.current_title = self.current_data
        elif tag == "id" and self.id_flag:
            self.page_id = self.current_data
            self.block_titles[self.page_id] = self.current_title
        elif tag == "text":
            self.current_text = self.current_data
        elif tag == "mediawiki":
            write_to_disk(self.block_titles, self.block_total)
            self.block_titles = {}

    def characters(self, ch):
        self.current_data += ch


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("usage: python wiki_indexer.py [path-to-wiki-dump-folder] [path-to-output-folder]")
        sys.exit()

    parser = xml.sax.make_parser()
    parser.setFeature(xml.sax.handler.feature_namespaces, 0)
    handler = PageHandler()
    parser.setContentHandler(handler)
    parser.parse(sys.argv[1])
    