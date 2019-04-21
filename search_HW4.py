#!/usr/bin/python
import re
import heapq
import nltk
import sys
import getopt

import math
import collections
import cPickle as pickle
import tf_idf
from retrieve_dict import preprocess
from index_HW4 import *
import json


def usage():
    print "usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results"

# =========================================================================
#
#                           Posting Class
#
# ========================================================================= 
class Posting:
    def __init__(self, docID, titleCount, contentCount, dateCount, courtCount):
        self.currentDocID = docID
        self.currentTitleCount = titleCount
        self.currentContentCount = contentCount
        self.currentDateCount = dateCount
        self.currentCourtCount = courtCount
        self.currentCombinedTF = titleCount + contentCount + dateCount + courtCount
        
        
    def getDocID(self):
        return self.currentDocID
        
    def getTitleCount(self):
        return self.currentTitleCount
        
    def getContentCount(self):
        return self.currentContentCount
       
    def getDateCount(self):
        return self.currentDateCount
        
    def getCourtCount(self):
        return self.currentCourtCount
        
    def getTF(self):
        return self.currentCombinedTF
    
# =========================================================================
#
#                           PostingHandler Class
#
# =========================================================================
class PostingHandler:
    def __init__(self, dictionary_file, postings_file):
        self.dictionaryFile = dictionary_file
        self.postingsFile = open(postings_file, 'r')
        self.dictionary = importDS(self.dictionaryFile)
        self.currentPostingsList = ""
        self.currentWord = ""
        self.currentPointer = None 
        self.currentDocFreq = 0
        self.postingIndex = 0
        self.currentPosting = None
        
        
    def getDocLength(self, docID):
        return self.dictionary["DOC_ID"][docID][1]
        
    def getDocName(self, docID):
        return self.dictionary["DOC_ID"][docID][0]
        
    def getDocFreq(self, word):
        if word in self.dictionary:
            return self.dictionary[word]["docFreq"]
        else:
            return 0

    def getNumDoc(self):
        return len(self.dictionary["DOC_ID"])

    def getStartPointer(self, word):
        if word in self.dictionary:
            return self.dictionary[word]["index"]
        else:
            print("No such word: " + word + "in dictionary!")
            
    def extractPostingList(self, word):
        self.currentWord = word
        if word not in self.dictionary:
            return False
        startPointer = self.getStartPointer(word)
        self.postingsFile.seek(startPointer)
        postingList = self.postingsFile.readline()
        
        self.currentPostingsList = postingList
        self.currentPointer = 0
        self.currentDocFreq = self.getDocFreq(word)
        self.postingIndex = 0
        
        return True 
        
    def getNextPosting(self):
        self.postingIndex += 1
        if self.postingIndex > self.currentDocFreq:
            return None
            
        nextStartPointer = self.currentPointer
    
        docIDLen = int(self.currentPostingsList[nextStartPointer : nextStartPointer + 2])
        nextStartPointer += 2
        docID = self.currentPostingsList[nextStartPointer : nextStartPointer + docIDLen]
        nextStartPointer += docIDLen
        titleCount = int(self.currentPostingsList[nextStartPointer : nextStartPointer + 1])
        nextStartPointer += 1
        contentCountLen = int(self.currentPostingsList[nextStartPointer : nextStartPointer + 1])
        nextStartPointer += 1
        contentCount = int(self.currentPostingsList[nextStartPointer : nextStartPointer + contentCountLen])
        nextStartPointer += contentCountLen
        dateCount = int(self.currentPostingsList[nextStartPointer : nextStartPointer + 1])
        nextStartPointer += 1
        courtCount = int(self.currentPostingsList[nextStartPointer : nextStartPointer + 1])
        nextStartPointer += 1
        
        self.currentPointer = nextStartPointer
        self.currentPosting = Posting(docID, titleCount, contentCount, dateCount, courtCount)
        
        return self.currentPosting
        
    
# =========================================================================
#       Return the docName given DOC_ID
#           input: dictionary, DOC_ID(int)
#           output: docName(String)
# =========================================================================
def getDocName(dictionary, docID):
    return dictionary["DOC_ID"][docID][0]

# =========================================================================
#       Return the query as a dict with normalized scores
#           input: dictionary, query(dict)
#           output: query_scores(dict)
# =========================================================================
def queryToScore(query):
    global postingHandler
    uniDict = makeUniGrams(preprocess(query))
    q_len = tf_idf.getLtcLen(postingHandler, uniDict)
    N = postingHandler.getNumDoc()
    for word in uniDict:
        df = postingHandler.getDocFreq(word)
        uniDict[word] = tf_idf.get_ltc(uniDict[word], N, df, q_len)
    return uniDict


# =========================================================================
#       Processes a free text query
#           input: dictionary, query(String)
#           output: sorted_results(list)
# =========================================================================
def processFreeText(query):
    global postingHandler
    q_score = queryToScore(query)
    score_list = {}
    for q_word in q_score:
        postingHandler.extractPostingList(q_word)
        posting = postingHandler.getNextPosting()
        while posting is not None:
            docID = posting.getDocID()
            docName = postingHandler.getDocName(docID)
            temp_score = [0.0, 0.0, 0.0, 0.0, 0.0]
            # Scores are contained as
            # [docID, court, title, date, content] as per descending importance
            temp_score[0] = 1 if docID == q_word else 0
            temp_score[1] = 1 if posting.getCourtCount() > 0 else 0
            temp_score[2] = 1 if posting.getTitleCount() > 0 else 0
            temp_score[3] += tf_idf.get_lnc(posting.getDateCount(), postingHandler.getDocLength(docID)) * q_score[q_word]
            temp_score[4] += tf_idf.get_lnc(posting.getContentCount(), postingHandler.getDocLength(docID)) * q_score[q_word]
            if sum(temp_score) > 0:
                if docName not in score_list:
                    score_list[docName] = temp_score
                else:
                    for i in range(5):
                        if temp_score[i] > 0:
                            score_list[docName][i] += temp_score[i] + 1

            posting = postingHandler.getNextPosting()

    sorted_results = sorted(score_list.items(), key=lambda k:k[1], reverse=True)
    return sorted_results


# =========================================================================
#       Imports the dataStructure using pickle interface
#           input: outputFile(String)
#           output: DS(Object)
# =========================================================================
def importDS(outputFile):
    data = open(outputFile, 'r')
    DS = json.load(data)
    return DS
    
# =========================================================================
#
#                           TEST
#
# =========================================================================    
def test(dictionary, postingsFile):   
    for word in dictionary:
        if word == "DOC_ID":
            continue
        print(word)
        posting = extractPostingList(word, dictionary, postingsFile)
        df = dictionary[word]["docFreq"]
        nextStartPointer = 0
        for index in range(df):
            docID, titleCount, contentCount, dateCount, courtCount, nextStartPointer = extractPosting(posting, nextStartPointer)
            print("Case number = " + getDocName(dictionary, docID))
            print(contentCount)
        print(getDocLength(dictionary, docID))
    
# =========================================================================
#
#                           RUN
#
# =========================================================================
if __name__ == "__main__":
    #queries = processQueries(file_of_queries)
    dictionary_file = "Fulldictionary.txt"
    postings_file = "Fullpostings.txt"
    postingHandler = PostingHandler(dictionary_file, postings_file)
    res = processFreeText("knife attempted murder wife husband police supreme court")
    #  python search_HW4.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt

    dictionary_file = postings_file = file_of_queries = output_file_of_results = None

    # try:
    #     opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
    # except getopt.GetoptError, err:
    #     usage()
    #     sys.exit(2)
    #
    # for o, a in opts:
    #     if o == '-d':
    #         dictionary_file = a
    #     elif o == '-p':
    #         postings_file = a
    #     elif o == '-q':
    #         file_of_queries = a
    #     elif o == '-o':
    #         file_of_output = a
    #     else:
    #         assert False, "unhandled option"
    #
    # if dictionary_file == None or postings_file == None or file_of_queries == None or file_of_output == None:
    #     usage()
    #     sys.exit(2)
