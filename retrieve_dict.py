#!/usr/bin/python
import nltk
import pickle
import pandas


def preprocess(string):
    tokens = nltk.word_tokenize(string)
    words = list()
    Stemmer = nltk.stem.porter.PorterStemmer()
    for token in tokens:
        word = Stemmer.stem(token)
        words.append(word)
    return list(words)

def exportDS(DS, outputFile):
    DS_string = pickle.dumps(DS, protocol=2)
    outputFile = open(outputFile, 'wb')
    outputFile.write(DS_string)
    return

def openCSV():
    path = "E:/Git/Retrieve-Law/data/dataset.csv"
    df = pandas.read_csv(path)
    dummyDocs= dict()
    columns = ["title","content","date_posted","court"]
    length = len(df)
    count = 0
    for index, row in df.iterrows():
        count+=1
        dummyDoc = dict()
        for column in columns:
            dummyDoc[column] = preprocess(row[column])
        dummyDocs[row["document_id"]] = dummyDoc
        print(dummyDoc)
        print(str(count/length*100)[:5]+'% has done!')
    exportDS(dummyDocs,'preprocessing.txt')

openCSV()