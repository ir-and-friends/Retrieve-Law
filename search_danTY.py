#!/usr/bin/python
import re
import heapq
import nltk
import sys
import getopt

import math
import collections
import cPickle as pickle

# =========================================================================
#
#                           ARGS PASS
#
# =========================================================================

def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

dictionary_file = postings_file = file_of_queries = output_file_of_results = None
    
try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        file_of_queries = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    usage()
    sys.exit(2)
    
# =========================================================================
#
#                           Methods
#
# =========================================================================

#=========================================================================
#       Stemming and Case folding
#           input: word(String)
#           output: word(String)
#=========================================================================
def Stemmer(word):
    Stemmer = nltk.stem.porter.PorterStemmer()
    word = Stemmer.stem(word) #apparently already does case folding
    return word
# =========================================================================
#       Creates an ArrayList containing the 
#           input: word(string), dictionary(dict), postingsFile(type: file object)
#           output: TfList(list(tuple(docID, TfIdf)))
# =========================================================================   
def getTf(word, dictionary, postingsFile):
    TfList = list()
    df = dictionary[word]["docFreq"]
    
    postingList = extractPostingList(word, dictionary, postingsFile)
    startPointer = 0
    for index in range(df):
        _, _, docID, _, startPointer, tf, _ = extractPosting(postingList, startPointer)
        tf = 1 + math.log(tf, 10)
        TfList.append(tuple((docID, tf)))
        
    return TfList
    
#=========================================================================
#       Extracts a posting list for a word
#           input: Word, dictionary, posting list(type: file object)
#           returns: postingList(type: String)
#========================================================================= 
def extractPostingList(word, dictionary, postingsFile):
    if word not in dictionary:
        return ""
    startPointer = dictionary[word]["index"]
    postingsFile.seek(startPointer)
    postingList = postingsFile.readline()
    return postingList
    
# =========================================================================
#       Imports the dataStructure using pickle interface
#           input: outputFile(String)
#           output: DS(Object)
# =========================================================================
def importDS(outputFile):
    data = open(outputFile, 'r')
    DS = pickle.load(data)
    return DS

# =========================================================================
#       Extracts the data from posting list given a startPointer and postingList
#           input: postingList(String), nextStartPointer(int)
#           output: checker(String), postinglength(int), docName(String),
#                skipPointer(int), nextStartPointer(int), termFreq(int), 
#                TFlength(String)
# =========================================================================
def extractPosting(postingList, nextStartPointer):
    skipPointer = 0
    checker = postingList[nextStartPointer]
    nextStartPointer += 1
    postinglength = postingList[nextStartPointer : nextStartPointer + 2]
    nextStartPointer += 2
    docName = postingList[nextStartPointer : nextStartPointer + int(postinglength)]
    nextStartPointer += int(postinglength)
    TFlength = postingList[nextStartPointer : nextStartPointer + 2]
    nextStartPointer += 2
    termFreq = int(postingList[nextStartPointer : nextStartPointer + int(TFlength)])
    nextStartPointer += int(TFlength)
    if checker > "0":
        skipPointer = int(postingList[nextStartPointer : nextStartPointer + int(checker)])
        nextStartPointer += int(checker)
    return checker, postinglength, docName, skipPointer, nextStartPointer, termFreq, TFlength

# =========================================================================
#       Process Queries
# =========================================================================
def processQueries(inputFile):
    data = open(inputFile, 'r').readlines()
    queries = list()
    for line in data:
        tokens = nltk.word_tokenize(line)
        stemtokens = set()
        for token in tokens:
            stemtokens.add(Stemmer(token))
        queries.append(stemtokens)
    return queries

# =========================================================================
#       Search base on the query set
#           input: query(set), dictionary(dict), postingsFile(type: file object)
#           output: sortedDocScore(list(tuple(docID, score)))
# =========================================================================
def search(query, dictionary, postingsFile):
    wordList = set(dictionary.keys())
    wordIntersection = wordList.intersection(query)
    
    blankVector = createBlankVector(wordIntersection)
    queryVector = initQueryVector(wordIntersection, dictionary, postingsFile, blankVector)
    
    dictOfVectors = dict()
    for word in wordIntersection:
        TfList = getTf(word, dictionary, postingsFile)
        for doc in TfList:
            if doc[0] not in dictOfVectors:
                dictOfVectors[doc[0]] = createBlankVector(wordIntersection)
                dictOfVectors[doc[0]]["LENGTH"] = getDocLength(dictionary, doc[0])
            dictOfVectors[doc[0]][word] = doc[1]
    
    docScore = dict()
    for docID in dictOfVectors:
        docName = getDocName(dictionary, docID)
        docScore[docName] = getCosScore(dictOfVectors[docID], queryVector)
    # for docid in dictionary["DOC_ID"]:
        # score = 0
        # for word in wordIntersection:
            # TfList = wordTFidfdict[word]
            # for tfidf in TfList:
                # if tfidf[0] == docid:
                    # score+=tfidf[1]
        # docScore[docid] = score
    sortedDocScore10 = heapq.nlargest(10, docScore.items(), key=lambda score: score[1])
    return sortedDocScore10
    
# =========================================================================
#       Initialise query vector
#           input: query, dictionary, postingsFile, blankVector
#           output: queryVector
# =========================================================================
def initQueryVector(query, dictionary, postingsFile, blankVector):
    N = len(dictionary["DOC_ID"])

    queryVector = blankVector
    squareSum = 0
    score = 0
    for word in query:
        squareSum += 1**2
        df = dictionary[word]["docFreq"]
        idf = math.log(N/df, 10)
        blankVector[word] = idf
    queryVector["LENGTH"] = math.sqrt(squareSum)
    
    return queryVector
    
# =========================================================================
#       get cos score of a given vector with TfIdf
#           input: vector, queryVector
#           output: normScore
# =========================================================================    
def getCosScore(vector, queryVector):
    score = 0
    vectorLen = vector["LENGTH"]
    queryLen = queryVector["LENGTH"]
    for word in vector:
        if word is "LENGTH":
            continue
        score += ((vector[word] / vectorLen) + (queryVector[word] / queryLen))
    
    return score

# =========================================================================
#       Creates a blank dictionary with words of query at tfidf = 0
#           input: query(list)
#           output: vector(dictionary)
# =========================================================================
def createBlankVector(query):
    vector = dict()
    vector["LENGTH"] = 0
    for word in query:
        vector[word] = 0
        
    return vector

# =========================================================================
#       Return the sqrtLen given DOC_ID
#           input: dictionary, DOC_ID(int)
#           output: docName(String)
# =========================================================================
def getDocLength(dictionary, docID):
    return dictionary["DOC_ID"][docID][1]
    
# =========================================================================
#       Return the docName given DOC_ID
#           input: dictionary, DOC_ID(int)
#           output: docName(String)
# =========================================================================
def getDocName(dictionary, docID):
    return dictionary["DOC_ID"][docID][0]

# =========================================================================
#       Calls the evaluation function and exports the result
#           input is a list of queries
#           input is a list of queries
# =========================================================================
def emportRe(queries, dictionary, postingsFile):
    with open(file_of_output, 'w') as output_file:
        for query in queries:
            sortedDocScore = search(query, dictionary, postingsFile)
            length = len(sortedDocScore)
            if length == 0:
                output_file.write("\n")
            else:
                for DocScoreIndex in range(length-1):
                    output_file.write (str(sortedDocScore[DocScoreIndex][0])+" ")
                output_file.write(str(sortedDocScore[length-1][0])+"\n")

# =========================================================================
#
#                           TEST
#
# =========================================================================    
def test():
    dictionary = importDS(dictionary_file)
    postingsFile = open(postings_file, 'r')
    word = "apple"
    TfIdf = getTf(word, dictionary, postingsFile)
    print(TfIdf)


# =========================================================================
#
#                           RUN
#
# =========================================================================
queries = processQueries(file_of_queries)
dictionary = importDS(dictionary_file)
postingsFile = open(postings_file, 'r')
#search(queries[0], dictionary, postingsFile)
#searchDaniel(queries[0], dictionary, postingsFile)
#test()
emportRe(queries, dictionary, postingsFile)
#  python2.7 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt




