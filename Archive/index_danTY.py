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

# =========================================================================
#
#                           Methods
#
# =========================================================================
class Indexer:
    def __init__(self, input_directory, output_file_dictionary, output_file_postings):
        self.directory = input_directory
        self.dictionaryFile = output_file_dictionary
        self.postingsFile = output_file_postings
        self.dictionary = dict()
        self.tempPostingList = list()
        self.listOfFiles = os.listdir(self.directory)
        self.listOfFiles.sort(key = int)
        self.numberOfFiles = len(self.listOfFiles)
        self.dictionary["DOC_ID"] = dict()
        
    def indexDirectory(self, numberOfFilesToProcess = 0): 
        if numberOfFilesToProcess is 0:
            numberOfFilesToProcess = self.numberOfFiles
        self.processFiles(numberOfFilesToProcess)
        self.createPostingList()
        exportDS(self.dictionary, self.dictionaryFile)
        
# =========================================================================
#       Processes Files in directory and calls self.addWords()
#           input: numberOfFilesToProcess(int)
#           output: None
# =========================================================================   
    def processFiles(self, numberOfFilesToProcess):    
        for fileNumber in range(numberOfFilesToProcess):
            fileName = self.listOfFiles[fileNumber]
            tokens = tokenise(self.directory + fileName)
            words = preprocess(tokens)
            self.addWords(words, str(fileNumber))
            lengthOfFile = self.calcLen(words)
            self.dictionary["DOC_ID"][str(fileNumber)] = tuple((fileName, lengthOfFile)) 

# =========================================================================
#       Calculates the length based on log(tf)
#           input: words(Dictionary)
#           output: None
# ========================================================================= 
    def calcLen(self, words):
        squareSum = 0
        for word in words:
            index = self.dictionary[word]["index"]
            lastIndex = len(self.tempPostingList[index]) - 1
            tf = self.tempPostingList[index][lastIndex][1]
            tf = 1 + math.log(tf, 10)
            squareSum += tf ** 2
        LENGTH = math.sqrt(squareSum)
        return LENGTH
 
# =========================================================================
#       Adds each word in the file to self.dictionary and self.tempPostingList
#           input: words(Dictionary), fileName(String)
#           output: None
# =========================================================================
    def addWords(self, words, fileName):
        for word in words:
            if word not in self.dictionary:
                #print("found new word " + word + " in document " + fileName)
                self.dictionary[word] = dict(docFreq = 1, index = len(self.tempPostingList))
                tempList = list()
                tempList.append(tuple((fileName, words[word])))
                self.tempPostingList.append(tempList)
            else:
                self.dictionary[word]["docFreq"] += 1
                index = self.dictionary[word]["index"]
                self.tempPostingList[index].append(tuple((fileName, words[word])))
                
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
            if word is "DOC_ID":
                continue
            docfreq = self.dictionary[word]["docFreq"]
            index = self.dictionary[word]["index"]
            # print(word)
            posting = createPosting(self.tempPostingList, index)
            #print(posting)
            skipPosting = createSkipPosting(posting, docfreq)
            # print(skipPosting)
            startPointer = addSkipPosting(skipPosting, self.postingsFile)
            # print(startPointer)
            self.dictionary[word]["index"] = startPointer
        return
        
# =========================================================================
#       Creates posting for one word first two digits represent the length
#           of docName, followed by docName, followed by two digits 
#           representing the length of termFreq, followed by termFreq \n
#           input: postings(list of list of tuple), index(int)
#           output: posting(String)
# =========================================================================
def createPosting(postings, index):
    posting = ""
    for tuple in postings[index]:
        docName = tuple[0]
        posting += str(len(docName)).zfill(2) + docName  # len of posting is padded to make it 2 digit
        termFreq = str(tuple[1])
        posting += str(len(termFreq)).zfill(2) + termFreq 
    posting += "\n"
    return posting
    
# =========================================================================
#       Creates skip pointers in the posting
#           End result is a posting of digits_in_skip_pointer(1), 
#           length_of_docName(2), docName, length_of_docFreq(2), docFreq,
#           skip_Pointer(relative to head of posting) 
#           input: posting(String), freq(int)
#           output: skipPosting(String)
# =========================================================================
def createSkipPosting(posting, freq):
    nSkips = int(math.sqrt(freq))
    skipDistance = int(freq / nSkips)
    if freq % nSkips is 0:
        nSkips -= 1
    pointerA = pointerB = 0
    skipPosting = ""
    for i in range(nSkips):
        skipPointer = 0
        for j in range(skipDistance):
            postingNameLen = int(posting[pointerA: pointerA + 2])
            pointerA += postingNameLen + 2
            skipPointer += postingNameLen + 2
            lenTermFreq = int(posting[pointerA: pointerA + 2])
            pointerA += lenTermFreq + 2
            skipPointer += lenTermFreq + 2
        
        finalSkipPointer = skipPointer + skipDistance + 1  # skipDistance to account for the appended checking number and 2 for the skip pointer
        lenFSP = len(str(finalSkipPointer))
        if len(str(finalSkipPointer + lenFSP)) > lenFSP:
            lenFSP + 1
        finalSkipPointer += lenFSP
        postinglen = int(posting[pointerB: pointerB + 2])
        skipPosting += str(lenFSP) + posting[pointerB: pointerB + postinglen + 2]
        pointerB += postinglen + 2
        lenTermFreq = int(posting[pointerB: pointerB + 2])
        skipPosting += posting[pointerB: pointerB + lenTermFreq + 2] + str(finalSkipPointer)
        pointerB += lenTermFreq + 2
        

        for j in range(skipDistance - 1):
            postinglen = int(posting[pointerB: pointerB + 2])
            skipPosting += "0" + posting[pointerB: pointerB + postinglen + 2]
            pointerB += postinglen + 2
            lenTermFreq = int(posting[pointerB: pointerB + 2])
            skipPosting += posting[pointerB: pointerB + lenTermFreq + 2]
            pointerB += lenTermFreq + 2
            

    while pointerB < len(posting) - 1:
        postinglen = int(posting[pointerB: pointerB + 2])
        skipPosting += "0" + posting[pointerB: pointerB + postinglen + 2]
        pointerB += postinglen + 2
        lenTermFreq = int(posting[pointerB: pointerB + 2])
        skipPosting += posting[pointerB: pointerB + lenTermFreq + 2]
        pointerB += lenTermFreq + 2

    skipPosting += "\n"
    # print(skipPosting)
    # sys.exit(2)
    return skipPosting

# =========================================================================
#       Add the posting to the outputFile 
#           input: skipposting(String), outputFile(String)
#           output: startPointer
# =========================================================================
def addSkipPosting(skipPosting, outputFile):
    outputData = open(outputFile, "a+")
    outputData.seek(0,2)
    startPointer = outputData.tell()
    outputData.write(skipPosting)
    outputData.close()
    return startPointer
   
# =========================================================================
#       Opens the file and tokenises the words using NLTK library
#           input: file(String)
#           output: tokens(List)
# =========================================================================
def tokenise(file):
    data = open(file).read()
    tokens = nltk.word_tokenize(data)
    return tokens
   
# =========================================================================
#       Preprocesses the tokens by using porter stemmer
#           input: tokens(List)
#           output: words(Dictionary)
# =========================================================================
def preprocess(tokens):
    words = dict()
    Stemmer = nltk.stem.porter.PorterStemmer()
    for token in tokens:
        word = Stemmer.stem(token) # apparently already does case folding
        if word not in words:
            words[word] = 1
        else:
            words[word] += 1
    return words

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
indexer = Indexer(input_directory, output_file_dictionary, output_file_postings)
indexer.indexDirectory()
# python27 index.py -i E://nltk_data/corpora/reuters/training/ -d dictionary.txt -p postings.txt