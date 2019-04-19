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
        self.currentCombinedTF = titleCount + contentCount + dateCount + courtCount\
        
        
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
#       Imports the dataStructure using pickle interface
#           input: outputFile(String)
#           output: DS(Object)
# =========================================================================
def importDS(outputFile):
    data = open(outputFile, 'r')
    DS = pickle.load(data)
    return DS    
    
# =========================================================================
#
#                           TEST
#
# =========================================================================    
def test(postingHandler):
    print(postingHandler.getDocFreq("SINGAPORE Vlogger"))
    print(postingHandler.extractPostingList("SINGAPORE Vlogger"))
    print(postingHandler.getNextPosting().getContentCount())
    
    
# =========================================================================
#
#                           RUN
#
# =========================================================================
#queries = processQueries(file_of_queries)
postingHandler = PostingHandler(dictionary_file, postings_file)
test(postingHandler)
#  python search_HW4.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt