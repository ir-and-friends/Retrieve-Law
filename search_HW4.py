#!/usr/bin/python
import re
import heapq
import nltk
import sys
import getopt

import math
import collections
import json
import tf_idf
# from index_HW4 import *

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
#
#                           MAIN
#
# =========================================================================
def main():
    f = open(file_of_queries)
    queries = f.readlines()
    f.close()

    output = []
    for line in queries:
        line = line.replace('\n', '')
        if line.find(" AND ") != -1:
            output.append(processBoolQuery(line) + '\n')
        else:
            output.append(processFreeText(line) + '\n')

    f = open(file_of_output, 'w+')
    f.writelines(output)
    f.close()

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
def queryToScore(dictionary, query):
    uniDict = makeUniGrams(processText(query))
    q_len = tf_idf.getLtcLen(dictionary, uniDict)
    N = len(dictionary["DOC_ID"])
    for word in uniDict:
        df = dictionary[word]['docFreq']
        uniDict[word] = tf_idf.get_ltc(uniDict[word], N, df, q_len)
    return uniDict


# =========================================================================
#       Return the docName given DOC_ID
#           input: dictionary, DOC_ID(int)
#           output: docName(String)
# =========================================================================
def processQuery(dictionary, query):
    global postingsFile
    q_score = queryToScore(dictionary, query)
    score_list = {}
    for q_word in q_score:
        p_list = extractPostingList(q_word, dictionary, postingsFile)
        posting = getNextPosting(p_list)
        while posting is not None:
            docID, titleCount, contentCount, dateCount, courtCount, nextStartPointer = posting
            if docID not in score_list:
                score_list[docID] = [0.0, 0.0, 0.0, 0.0, 0.0]
            # Scores are contained as
            # [docID, court, title, date, content] as per descending importance
            if score_list[docID][0] != 1 and docID == q_word:
                score_list[docID][0] = 1
            partial_score = lambda doc_tf, p, q_score: tf_idf.get_lnc(doc_tf, p.getDocLen()) * q_score
            score_list[docID][1] += partial_score(courtCount, posting, q_score[q_word])
            score_list[docID][2] += partial_score(titleCount, posting, q_score[q_word])
            score_list[docID][3] += partial_score(dateCount, posting, q_score[q_word])
            score_list[docID][4] += partial_score(contentCount, posting, q_score[q_word])
            posting = getNextPosting(p_list)

    return sorted(score_list.items(), key=lambda k:k[1])

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
#           Boolean Search
#
# =========================================================================
def processBoolQuery(query):
    # Since only boolean operator is AND, each element in this list will be AND-merged
    query = query.split(" AND ")
    stemmer(query)
    convertToScores(query)

    # Since skip lists aren't implemented, no need to prioritise shortest query
    while len(query) > 1:
        query[0] = doAnd(query[0], query[1])
        del query[1]

    query = query[0]
    if len(query) == 0:
        return ""
    else:
        query.sort(key=lambda x: x[1], reverse=True)
        # print query
        result = [str(i) for i in zip(*query)[0]]
        return ' '.join(result)

def stemmer(list):
    # Uses the same stemmer as index phase
    ps = nltk.stem.PorterStemmer()
    for i in range(len(list)):
        if list[i][0] == "'" or list[i][0] == '"':
            list[i] = list[i][1:-1]
        list[i] = ps.stem(list[i])

def convertToScores(list):
    # Retrieve postings and calculate lnc.ltc
    # Returns array of postings of format [str(docID), float(lnc)]
    ph = PostingHandler(dictionary_file, postings_file)

    ltc = {}
    sum = 0
    for i in range(len(list)):
        word = list[i]
        ph.extractPostingList(word)
        df = int(ph.getDocFreq(word))
        if df != 0:
            ltc[word] = math.log10(1.0/df)
        else:
            ltc[word] = 0
        sum += pow(ltc[word], 2)
    if sum == 0:
        sum = 1
    for word in ltc:
        ltc[word] /= pow(sum, 0.5)

    lnc = []
    for i in range(len(list)):
        word = list[i]
        list[i] = []
        ph.extractPostingList(word)
        sum = 0
        for count in range(int(ph.getDocFreq(word))):
            post = ph.getNextPosting()

            docID = ph.getDocName(post.getDocID())
            tf = post.getTF()
            lnc.append([docID, 1 + math.log10(tf)])
            sum += pow(1 + math.log10(tf), 2)
        if sum == 0:
            sum = 1
        for j in range(len(lnc)):
            docID = lnc[j][0]
            lncScore = lnc[j][1] / pow(sum, 0.5)

            list[i].append([docID, lncScore * ltc[word]])

def doAnd(t1, t2):
    # AND-merge of two nested arrays of format [[docID, score], ...]
    # Returns nested array of similar format
    i = j = 0
    result = []
    while i < len(t1) and j < len(t2):
        # print("i: %d of %d\nj: %d of %d" % (i, len(t1), j, len(t2)))
        d1, s1 = t1[i]
        d2, s2 = t2[j]
        if d1 == d2:
            result.append([d1, s1 * s2])
            i += 1
            j += 1
        elif d1 < d2:
            i += 1
        else:
            j += 1

    return result


# =========================================================================
#
#                           RUN
#
# =========================================================================
main()
#queries = processQueries(file_of_queries)
# postingHandler = PostingHandler(dictionary_file, postings_file)
# test(postingHandler)
#  python search_HW4.py -d dictionary.txt -p postings.txt -q queries.txt -o output.txt