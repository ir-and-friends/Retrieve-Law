#!/usr/bin/python
import sys
import getopt
import nltk
import json
import math

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

        docIDLen = int(self.currentPostingsList[nextStartPointer: nextStartPointer + 2])
        nextStartPointer += 2
        docID = self.currentPostingsList[nextStartPointer: nextStartPointer + docIDLen]
        nextStartPointer += docIDLen
        titleCount = int(self.currentPostingsList[nextStartPointer: nextStartPointer + 1])
        nextStartPointer += 1
        contentCountLen = int(self.currentPostingsList[nextStartPointer: nextStartPointer + 1])
        nextStartPointer += 1
        contentCount = int(self.currentPostingsList[nextStartPointer: nextStartPointer + contentCountLen])
        nextStartPointer += contentCountLen
        dateCount = int(self.currentPostingsList[nextStartPointer: nextStartPointer + 1])
        nextStartPointer += 1
        courtCount = int(self.currentPostingsList[nextStartPointer: nextStartPointer + 1])
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
    DS = json.load(data)
    return DS

def main():
    f = open(file_of_queries)
    queries = f.readlines()
    f.close()

    results = []
    for line in queries:
        results.append(' '.join(processquery(line[:-1])) + "\n")

    f = open(file_of_output, 'w+')
    f.writelines(results)
    f.close()

def processquery(query):
    # Since only boolean operator is AND, each element in this list will be AND-merged
    query = query.split(" AND ")
    stemmer(query)
    convertToScores(query)

    # Since skip lists aren't implemented, no need to prioritise shortest query
    while len(query) > 1:
        query[0] = doAnd(query[0], query[1])
        del query[1]

    query.sort(key=lambda x:x[1], reverse=True)
    query = query[0]
    if len(query) == 0:
        return ""
    else:
        return [str(i) for i in zip(*query)[0]]

def stemmer(list):
    # Uses the same stemmer as index phase
    ps = nltk.stem.PorterStemmer()
    for i in range(len(list)):
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
        ltc[word] = math.log10(1.0/df)
        sum += pow(ltc[word], 2)
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

            docID = post.getDocID()
            tf = post.getTF()
            lnc.append([docID, 1 + math.log10(tf)])
            sum += pow(1 + math.log10(tf), 2)
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
        print("i: %d of %d\nj: %d of %d" % (i, len(t1), j, len(t2)))
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

main()

