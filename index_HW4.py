#!/usr/bin/python
import re
import nltk
import sys
import getopt

import os
import cPickle as pickle
import math
import tf_idf

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
    elif o == '-p':  # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_dictionary == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

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
dummyDocs["3"]["title"] = title[0].split()
dummyDocs["3"]["content"] = list(("This", "is", "the", "case", "where", "the", "fish", "was", "eaten"))
dummyDocs["3"]["date_posted"] = list(("19", "April", "2019"))
dummyDocs["3"]["court"] = list(("Supreme", "court"))

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
        self.tempPostingA = "tempA.txt"
        self.tempPostingB = "tempB.txt"
        self.local_dictionary = dict()
        self.local_posting_asList = list()
        self.dictionary = dict()
        self.numberOfFiles = len(self.input_dictionary)
        self.dictionary["DOC_ID"] = dict()
        self.whichFile = 1
        data = open(self.tempPostingA, "w")
        data.write("")
        data.close()
        data = open(self.tempPostingB, "w")
        data.write("")
        data.close()
        
        
    def indexDictionary(self, numberOfFilesToProcess = 0): 
        if numberOfFilesToProcess is 0:
            numberOfFilesToProcess = self.numberOfFiles
        self.processFiles(numberOfFilesToProcess)
        print("Pickle")
        exportDS(self.dictionary, self.dictionaryFile)
        
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
            print("Making grams")
            titleDict = makeGrams(self.input_dictionary[caseID]["title"])
            contentDict = makeGrams(self.input_dictionary[caseID]["content"])
            dateDict = makeGrams(self.input_dictionary[caseID]["date_posted"])
            courtDict = makeGrams(self.input_dictionary[caseID]["court"])
            dictToProcess = dict(title = titleDict, content = contentDict, date = dateDict, court = courtDict)
            length  = tf_idf.getLncLen(makeUniGrams(self.input_dictionary[caseID]["content"]))
            self.dictionary["DOC_ID"][str(count)] = tuple((caseID, length))
            print("Adding Words")
            self.addWords(dictToProcess, str(count))
            
            if ((count + 1) % 10) is 0:
                print(str(count+1) + " out of " + str(numberOfFilesToProcess) + " files processed.")
            
            if ((count + 1) % 10000) is 0:
                print("Writing File")
                if self.whichFile is 1:
                    oldFile = self.tempPostingA
                    newFile = self.tempPostingB
                    self.whichFile *= -1
                else:
                    oldFile = self.tempPostingB
                    newFile = self.tempPostingA
                    self.whichFile *= -1
                self.mergePosting(self.local_dictionary, self.local_posting_asList, oldFile, newFile)
                self.local_dictionary = dict()
                self.local_posting_asList = list()
                
            count += 1
            # lengthOfFile = self.calcLen(words)
            # self.dictionary["DOC_ID"][str(fileNumber)] = tuple((fileName, lengthOfFile)) 
        
        print("Writing File")
        if self.whichFile is 1:
            oldFile = self.tempPostingA
            newFile = self.tempPostingB
            self.whichFile *= -1
        else:
            oldFile = self.tempPostingB
            newFile = self.tempPostingA
            self.whichFile *= -1
        self.mergePosting(self.local_dictionary, self.local_posting_asList, oldFile, self.postingsFile)
        self.local_dictionary = dict()
        self.local_posting_asList = list()
        
        
# =========================================================================
#       Adds each word in the file to self.dictionary and self.local_posting_asList
#           input: words(Dictionary), fileName(String)
#           output: None
# =========================================================================
    def addWords(self, dictionary, fileIndex):
        for word in dictionary["title"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.local_dictionary[word]["index"]
            if fileIndex not in self.local_posting_asList[index]:
                self.local_posting_asList[index][fileIndex] = dict(title = 0, content = 0, date_posted = 0, court = 0)
                self.local_dictionary[word]["docFreq"] += 1
            self.local_posting_asList[index][fileIndex]["title"] += dictionary["title"][word]
        
        for word in dictionary["content"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.local_dictionary[word]["index"]
            if fileIndex not in self.local_posting_asList[index]:
                self.local_posting_asList[index][fileIndex] = dict(title = 0, content = 0, date_posted = 0, court = 0)
                self.local_dictionary[word]["docFreq"] += 1
            self.local_posting_asList[index][fileIndex]["content"] += dictionary["content"][word]
            
        for word in dictionary["date_posted"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.local_dictionary[word]["index"]
            if fileIndex not in self.local_posting_asList[index]:
                self.local_posting_asList[index][fileIndex] = dict(title = 0, content = 0, date_posted = 0, court = 0)
                self.local_dictionary[word]["docFreq"] += 1
            self.local_posting_asList[index][fileIndex]["date_posted"] += dictionary["date_posted"][word]
        
        for word in dictionary["court"]:
            #print(word)
            self.addWord(word, fileIndex)
            index = self.local_dictionary[word]["index"]
            if fileIndex not in self.local_posting_asList[index]:
                self.local_posting_asList[index][fileIndex] = dict(title = 0, content = 0, date_posted = 0, court = 0)
                self.local_dictionary[word]["docFreq"] += 1
            self.local_posting_asList[index][fileIndex]["court"] += dictionary["court"][word]
        # for word in words:
            # if word not in self.local_dictionary:
                # #print("found new word " + word + " in document " + fileName)
                # self.local_dictionary[word] = dict(docFreq = 1, index = len(self.local_posting_asList))
                # tempList = list()
                # tempList.append(tuple((fileName, words[word])))
                # self.local_posting_asList.append(tempList)
            # else:
                # self.local_dictionary[word]["docFreq"] += 1
                # index = self.local_dictionary[word]["index"]
                # self.local_posting_asList[index].append(tuple((fileName, words[word])))
                
# =========================================================================
#       Adds each word in the file to self.local_dictionary and self.local_posting_asList
#           input: words(Dictionary), fileName(String)
#           output: None
# =========================================================================   
    def addWord(self, word, count):
        if word not in self.local_dictionary:
            #print("found new word " + word + " in document " + str(count))  
            self.local_dictionary[word] = dict(docFreq = 1, index = len(self.local_posting_asList))
            tempList = dict()
            tempList[count] = dict(title = 0, content = 0, date_posted = 0, court = 0)
            self.local_posting_asList.append(tempList)
                
        
# =========================================================================
#       Merges local posting with global posting
#           input: 
#           output: 
# =========================================================================
    def mergePosting(self, local_dictionary, local_posting_asList, oldPostingFilePath, newPostingFile):
        oldPostingFile = open(oldPostingFilePath, 'r')
        data = open(newPostingFile, "w")
        data.write("")
        data.close()
        
        for word in local_dictionary:
            if word in self.dictionary:
                posting = extractPostingList(word, self.dictionary, oldPostingFile).rstrip()
                index = local_dictionary[word]["index"]
                posting = createPosting(local_posting_asList[index], posting)
                startPointer = addPosting(posting, newPostingFile)
                self.dictionary[word]["index"] = startPointer
                self.dictionary[word]["docFreq"] += local_dictionary[word]["docFreq"]
            else:
                posting = ""
                index = local_dictionary[word]["index"]
                posting = createPosting(local_posting_asList[index], posting)
                startPointer = addPosting(posting, newPostingFile)
                self.dictionary[word] = dict()
                self.dictionary[word]["index"] = startPointer
                self.dictionary[word]["docFreq"] = local_dictionary[word]["docFreq"]
        
        for word in self.dictionary:
            if not word in local_dictionary:
                if word == "DOC_ID":
                    continue
                posting = extractPostingList(word, self.dictionary, oldPostingFile)
                startPointer = addPosting(posting, newPostingFile)
                self.dictionary[word]["index"] = startPointer
        
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
#       Creates posting for one word first two digits represent the length
#           of fileIndex, followed by fileIndex, followed by two digits 
#           representing the length of termFreq, followed by termFreq \n
#           input: postings(list of dictionary)
#           output: posting(String)
# =========================================================================
def createPosting(postings, posting):
    list_of_str = list()
    for fileIndex in postings:
        list_of_str.append(str(len(fileIndex)).zfill(2) + fileIndex)
        list_of_str.append(str(postings[fileIndex]["title"]))
        list_of_str.append(str(len(str(postings[fileIndex]["content"]))).zfill(1) + str(postings[fileIndex]["content"]))
        list_of_str.append(str(postings[fileIndex]["date_posted"]))
        list_of_str.append(str(postings[fileIndex]["court"]))
    posting = "".join(list_of_str) + "\n"
    
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
    
#=========================================================================
#       Extracts a posting list for a word
#           input: Word, dictionary, posting list(type: file object)
#           returns: postingList(type: String)
#========================================================================= 
def extractPostingList(word, dictionary, postingsFile):
    startPointer = dictionary[word]["index"]
    postingsFile.seek(startPointer)
    postingList = postingsFile.readline()
    return postingList
               
        
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
#       Exports the dataStructure using pickle interface
#           input:inputFile(String)
#           output: DS(object)
# =========================================================================  
def importDSByte(inputFile):
    data = open(inputFile, 'rb')
    DS = pickle.load(data)
    return DS

# =========================================================================
#
#                           RUN
#
# =========================================================================
input_dictionary = importDSByte(input_dictionary)
indexer = Indexer(input_dictionary, output_file_dictionary, output_file_postings)
indexer.indexDictionary(0)
# python index_HW4.py -i preprocessing.txt -d dictionary.txt -p postings.txt