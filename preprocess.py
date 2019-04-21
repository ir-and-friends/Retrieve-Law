#!/usr/bin/python
import re
import nltk
import sys
import getopt

import os
import json
import cPickle as pickle
import math
import tf_idf

dummyDocs = dict()
dummyDocs["1"] = dict()
dummyDocs["1"]["title"] = list(("The", "case", "thickens"))
dummyDocs["1"]["content"] = list(("This", "is", "the", "case", "where", "the", "fish", "was", "eaten"))
dummyDocs["1"]["date_posted"] = list(("19", "April", "2019"))
dummyDocs["1"]["court"] = list(("Supreme", "court"))
dummyDocs["2"] = dict()
dummyDocs["2"]["title"] = list(("The", "case", "thickens"))
dummyDocs["2"]["content"] = list(("This", "is", "the", "case", "where", "the", "fish", "was", "eaten"))
dummyDocs["2"]["date_posted"] = list(("19", "April", "2019"))
dummyDocs["2"]["court"] = list(("Supreme", "court"))
dummyDocs["3"] = dict()
title = "This is the title"
dummyDocs["3"]["title"] = title.split()
dummyDocs["3"]["content"] = list(("This", "is", "the", "case", "where", "the", "fish", "was", "eaten"))
dummyDocs["3"]["date_posted"] = list(("19", "April", "2019"))
dummyDocs["3"]["court"] = list(("Supreme", "court"))

# =========================================================================
#
#                           ARGS PASS
#
# =========================================================================

def usage():
    print "usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file"


input_directory = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError, err:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i':  # input dictionary
        input_dictionary = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    else:
        assert False, "unhandled option"

if input_dictionary == None or output_file_dictionary == None:
    usage()
    sys.exit(2)
    

def processFiles(input_dictionary):
    
    numberOfFilesToProcess = len(input_dictionary)
    print(numberOfFilesToProcess)
    count = 0
    dictToProcess = dict()
    
    for caseID in input_dictionary:
        if count > numberOfFilesToProcess:
            break
        titleDict = makeGrams(input_dictionary[caseID]["title"])
        contentDict = makeGrams(input_dictionary[caseID]["content"])
        dateDict = makeGrams(input_dictionary[caseID]["date_posted"])
        courtDict = makeGrams(input_dictionary[caseID]["court"])
        caseID = str(caseID)
        dictToProcess[caseID] = dict(title = titleDict, content = contentDict, date_posted = dateDict, court = courtDict)
        count += 1
        if ((count + 1) % 10) is 0:
            print(str(count+1) + " out of " + str(numberOfFilesToProcess) + " files processed.")
        
    return dictToProcess
# =========================================================================
#       Processes input of dictionary of lists into dictionary of dictionary
#           input: list of words)
#           output: dictionary of grams
# ========================================================================= 
def makeGrams(list):
    dictOfGrams = dict()
    
    dictOfGrams.update(makeAllGrams(list))
    
    return dictOfGrams

# =========================================================================
#       Processes list into dictionary of uniGrams
#           input: list of words
#           output: dictionary of uniGrams
# =========================================================================
def makeUniGrams(list):
    words = dict()
    for word in list:
        if word not in words:
            #print(word)
            words[word] = 1
        else:
            words[word] += 1
    return words
    
# =========================================================================
#       Processes list into dictionary of uniGrams
#           input: list of words
#           output: dictionary of uniGrams
# =========================================================================
def makeBiGrams(list):
    words = dict()
    count = 0
    for word in list:
        if count > 0:
            biWord = prevWord + " " + word
            if biWord not in words:
                #print(biWord)
                words[biWord] = 1
            else:
                words[biWord] += 1
        prevWord = word
        count += 1
    return words
    
# =========================================================================
#       Processes list into dictionary of uniGrams
#           input: list of words
#           output: dictionary of uniGrams
# =========================================================================
def makeTriGrams(list):
    words = dict()
    count = 0
    for word in list:
        if count > 1:
            triWord = prevPrevWord + " " + prevWord + " " + word
            if triWord not in words:
                #print(triWord)
                words[triWord] = 1
            else:
                words[triWord] += 1
        if count > 0:
            prevPrevWord = prevWord
        prevWord = word
        count += 1
    return words
    
# =========================================================================
#       Processes list into dictionary of uniGrams
#           input: list of words
#           output: dictionary of uniGrams
# =========================================================================
def makeAllGrams(list):
    words = dict()
    count = 0
    for word in list:
        
        if word not in words:
            #print(word)
            words[word] = 1
        else:
            words[word] += 1
        
        if count > 0:
            biWord = prevWord + " " + word
            if biWord not in words:
                #print(biWord)
                words[biWord] = 1
            else:
                words[biWord] += 1
    
        if count > 1:
            triWord = prevPrevWord + " " + prevWord + " " + word
            if triWord not in words:
                #print(triWord)
                words[triWord] = 1
            else:
                words[triWord] += 1
        
        if count > 0:
            prevPrevWord = prevWord
        prevWord = word
        count += 1
    return words
 
# =========================================================================
#       Exports the dataStructure using pickle interface
#           input:DS(object), outputFile(String)
#           output: None
# =========================================================================
def exportDSJSON(DS, outputFile):
    DS_string = json.dumps(DS)
    outputFile = open(outputFile, 'w')
    outputFile.write(DS_string)
    outputFile.close()
    return 
 
# =========================================================================
#       Exports the dataStructure using pickle interface
#           input:DS(object), outputFile(String)
#           output: None
# =========================================================================
def exportDS(DS, outputFile):
    DS_string = pickle.dumps(DS)
    outputFile = open(outputFile, 'w')
    outputFile.write(DS_string)
    outputFile.close()
    return 
    
# =========================================================================
#       Exports the dataStructure using pickle interface
#           input:inputFile(String)
#           output: DS(object)
# =========================================================================  
def importDSByte(inputFile):
    data = open(inputFile, 'rb')
    DS = pickle.load(data)
    return DS
    
print("starting import")
input_dictionary = importDSByte(input_dictionary)
dictionary = processFiles(input_dictionary)
print("Processesing completed. Pickling")
exportDSJSON(dictionary, output_file_dictionary)
# python preprocess.py -i preprocess.txt -d Predictionary.txt