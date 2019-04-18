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
#       Extracts the data from posting list given a startPointer and postingList
#           input: postingList(String), nextStartPointer(int)
#           output: checker(String), postinglength(int), docName(String),
#                skipPointer(int), nextStartPointer(int), termFreq(int), 
#                TFlength(String)
# =========================================================================
def extractPosting(postingList, nextStartPointer):
    docIDLen = int(postingList[nextStartPointer : nextStartPointer + 2])
    nextStartPointer += 2
    docID = postingList[nextStartPointer : nextStartPointer + docIDLen]
    nextStartPointer += docIDLen
    titleCount = int(postingList[nextStartPointer : nextStartPointer + 1])
    nextStartPointer += 1
    contentCountLen = int(postingList[nextStartPointer : nextStartPointer + 1])
    nextStartPointer += 1
    contentCount = int(postingList[nextStartPointer : nextStartPointer + contentCountLen])
    nextStartPointer += contentCountLen
    dateCount = int(postingList[nextStartPointer : nextStartPointer + 1])
    nextStartPointer += 1
    courtCount = int(postingList[nextStartPointer : nextStartPointer + 1])
    nextStartPointer += 1
    
    return docID, titleCount, contentCount, dateCount, courtCount, nextStartPointer
    
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
#queries = processQueries(file_of_queries)
dictionary = importDS(dictionary_file)
postingsFile = open(postings_file, 'r')
test(dictionary, postingsFile)
#  python2.7 search.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt