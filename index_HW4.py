#!/usr/bin/python
import re
import nltk
import sys
import getopt

import os
import cPickle as pickle
import math

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
    if o == '-i':  # input directory
        input_directory = a
    elif o == '-d':  # dictionary file
        output_file_dictionary = a
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_directory == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

dummyDocs = dict()
dummyDocs["caseID"] = dict()
dummyDocs["caseID"]["title"] = list(("The", "case", "thickens"))
dummyDocs["caseID"]["content"] = list(("This", "is", "the", "case", "where", "the", "fish", "was", "eaten"))
dummyDocs["caseID"]["date"] = list(("19", "April", "2019"))
dummyDocs["caseID"]["court"] = list(("Supreme", "court"))

# =========================================================================
#
#                           Methods
#
# =========================================================================
class Indexer:
    def __init__(self, input_dictionary, output_file_dictionary, output_file_postings):
        self.input_dictionary = input_dictionary
        self.dictionaryFile = output_file_dictionary
        self.postingsFile = output_file_postings
        self.dictionary = dict()
        self.tempPostingList = list()
        self.numberOfFiles = len(self.input_dictionary)
        self.dictionary["DOC_ID"] = dict()
        
    def indexDictionary(self, numberOfFilesToProcess = 0): 
        if numberOfFilesToProcess is 0:
            numberOfFilesToProcess = self.numberOfFiles
        self.processFiles(numberOfFilesToProcess)
        self.createPostingList()
        exportDS(self.dictionary, self.dictionaryFile)
        #print(self.dictionary)
        
# =========================================================================
#       Processes Files in directory and calls self.addWords()
#           input: numberOfFilesToProcess(int)
#           output: None
# =========================================================================   
    def processFiles(self, numberOfFilesToProcess):
        count = 0        
        for caseID in self.input_dictionary:
            if count > numberOfFilesToProcess:
                break
            titleDict = makeGrams(self.input_dictionary[caseID]["title"])
            contentDict = makeGrams(self.input_dictionary[caseID]["content"])
            dateDict = makeGrams(self.input_dictionary[caseID]["date"])
            courtDict = makeGrams(self.input_dictionary[caseID]["court"])
            dictToProcess = dict(title = titleDict, content = contentDict, date = dateDict, court = courtDict)
            length  = self.calcLen(makeUniGrams(self.input_dictionary[caseID]["content"]))
            self.dictionary["DOC_ID"][str(count)] = tuple((caseID, length))
            self.addWords(dictToProcess, str(count))
            count += 1
            # lengthOfFile = self.calcLen(words)
            # self.dictionary["DOC_ID"][str(fileNumber)] = tuple((fileName, lengthOfFile)) 

# =========================================================================
#       Calculates the length based on log(tf)
#           input: words(Dictionary)
#           output: None
# ========================================================================= 
    def calcLen(self, words):
        squareSum = 0
        for word in words:
            tf = words[word]
            tf = 1 + math.log(tf, 10)
            squareSum += tf ** 2
        LENGTH = math.sqrt(squareSum)
        return LENGTH        
        
        
# =========================================================================
#       Adds each word in the file to self.dictionary and self.tempPostingList
#           input: words(Dictionary), fileName(String)
#           output: None
# =========================================================================
    def addWords(self, dictionary, fileIndex):
        for word in dictionary["title"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.dictionary[word]["index"]
            self.tempPostingList[index][fileIndex]["title"] += dictionary["title"][word]
        
        for word in dictionary["content"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.dictionary[word]["index"]
            self.tempPostingList[index][fileIndex]["content"] += dictionary["content"][word]
            
        for word in dictionary["date"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.dictionary[word]["index"]
            self.tempPostingList[index][fileIndex]["date"] += dictionary["date"][word]
        
        for word in dictionary["court"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.dictionary[word]["index"]
            self.tempPostingList[index][fileIndex]["court"] += dictionary["court"][word]
        
        # for word in words:
            # if word not in self.dictionary:
                # #print("found new word " + word + " in document " + fileName)
                # self.dictionary[word] = dict(docFreq = 1, index = len(self.tempPostingList))
                # tempList = list()
                # tempList.append(tuple((fileName, words[word])))
                # self.tempPostingList.append(tempList)
            # else:
                # self.dictionary[word]["docFreq"] += 1
                # index = self.dictionary[word]["index"]
                # self.tempPostingList[index].append(tuple((fileName, words[word])))
                
# =========================================================================
#       Adds each word in the file to self.dictionary and self.tempPostingList
#           input: words(Dictionary), fileName(String)
#           output: None
# =========================================================================   
    def addWord(self, word, count):
        if word not in self.dictionary:
            #print("found new word " + word + " in document " + str(count))  
            self.dictionary[word] = dict(docFreq = 1, index = len(self.tempPostingList))
            tempList = dict()
            tempList[count] = dict(title = 0, content = 0, date = 0, court = 0)
            self.tempPostingList.append(tempList)
                
# =========================================================================
#       Exports the posting list as a readable txt doc. 
#           also updates dictionary
#           inputs: None
#           outputs: None 
# =========================================================================
    def createPostingList(self):
        data = open(self.postingsFile, "w")
        data.write("")
        data.close()
        for word in self.dictionary:
            if word == "DOC_ID":
                continue
            docfreq = self.dictionary[word]["docFreq"]
            index = self.dictionary[word]["index"]
            #print(word)
            posting = createPosting(self.tempPostingList[index])
            startPointer = addPosting(posting, self.postingsFile)
            self.dictionary[word]["index"] = startPointer
            #print(posting)
            # skipPosting = createSkipPosting(posting, docfreq)
            # # print(skipPosting)
            # startPointer = addSkipPosting(skipPosting, self.postingsFile)
            # # print(startPointer)
            # self.dictionary[word]["index"] = startPointer
        return
        
# =========================================================================
#       Processes input of dictionary of lists into dictionary of dictionary
#           input: list of words)
#           output: dictionary of grams
# ========================================================================= 
def makeGrams(list):
    dictOfGrams = dict()
    
    dictOfGrams.update(makeUniGrams(list))
    dictOfGrams.update(makeBiGrams(list))
    dictOfGrams.update(makeTriGrams(list))
    
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
#       Creates posting for one word first two digits represent the length
#           of fileIndex, followed by fileIndex, followed by two digits 
#           representing the length of termFreq, followed by termFreq \n
#           input: postings(list of dictionary)
#           output: posting(String)
# =========================================================================
def createPosting(postings):
    posting = ""
    for fileIndex in postings:
        posting += str(len(fileIndex)).zfill(2) + fileIndex  # len of posting is padded to make it 2 digit
        posting += str(postings[fileIndex]["title"])
        posting += str(len(str(postings[fileIndex]["content"]))) + str(postings[fileIndex]["content"])
        posting += str(postings[fileIndex]["date"])
        posting += str(postings[fileIndex]["court"])
    posting += "\n"
    return posting
    
# =========================================================================
#       Add the posting to the outputFile 
#           input: posting(String), outputFile(String)
#           output: startPointer
# =========================================================================
def addPosting(Posting, outputFile):
    outputData = open(outputFile, "a+")
    outputData.seek(0,2)
    startPointer = outputData.tell()
    outputData.write(Posting)
    outputData.close()
    return startPointer
               
        
# =========================================================================
#       Exports the dataStructure using pickle interface
#           input:DS(object), outputFile(String)
#           output: None
# =========================================================================
def exportDS(DS, outputFile):
    DS_string = pickle.dumps(DS)
    outputFile = open(outputFile, 'w')
    outputFile.write(DS_string)
    return 

# =========================================================================
#
#                           RUN
#
# =========================================================================
indexer = Indexer(dummyDocs, output_file_dictionary, output_file_postings)
indexer.indexDictionary(1)
# python index_HW4.py -i E://nltk_data/corpora/reuters/training/ -d dictionary.txt -p postings.txt