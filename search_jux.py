#!/usr/bin/python
import sys
import getopt
import math
from index import process_text, process_text_sw
import pickle
import heapq


def get_ltc(tf, df, q_len):
    global num_doc
    return (1.0 + math.log(tf, 10)) * math.log(num_doc / df, 10) / q_len


def get_lnc(tf, doc_len):
    return (1.0 + math.log(tf, 10)) / doc_len


def get_postings(start_pos):
    with open(postings_file) as p:
        p.seek(start_pos)
        return p.readline().split()


def normalize_q(words):
    temp_dict = {}
    norm_len = 0.0
    for w in words:
        if w not in dictionary:
            continue
        if w in temp_dict:
            temp_dict[w] += 1
        else:
            temp_dict[w] = 1

    # Get all squared weights
    for w in temp_dict:
        wt = (1.0 + math.log(temp_dict[w], 10)) * math.log(num_doc / dictionary[w][1], 10)
        norm_len += wt * wt

    # Apply sqrt
    norm_len = math.sqrt(norm_len)

    return [temp_dict, norm_len]


def process_query(q):
    global stop_words, dictionary, doc_lengths, doc_lengths_swr
    shortlisted_doc = {}
    # Start by removing all stop words
    bag_of_words = process_text_sw(q, stop_words)
    len_to_use = doc_lengths_swr
    # If none of the terms are in the dictionary allow stop words
    if not any(w in bag_of_words for w in dictionary):
        bag_of_words = process_text(q)
        len_to_use = doc_lengths
    bag_of_words, q_len = normalize_q(bag_of_words)
    for word in bag_of_words:
        # query word is found in dictionary
        postings = get_postings(dictionary[word][0])
        for posting in postings:
            docId, tf = posting.split('$')
            if docId not in shortlisted_doc:
                shortlisted_doc[docId] = 0
            else:
                shortlisted_doc[docId] += 1  # Award a hard score to articles with higher number of term matches
            norm_doc = get_lnc(int(tf), len_to_use[docId])
            norm_q = get_ltc(bag_of_words[word], dictionary[word][1], q_len)
            shortlisted_doc[docId] += norm_doc * norm_q
    shortlisted = []
    for k in shortlisted_doc:
        shortlisted.append((shortlisted_doc[k], k))
    # heapq.heapify(shortlisted)
    return heapq.nlargest(10, shortlisted)


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


dictionary_file = postings_file = file_of_queries = file_of_output = None

try:
    # opts = [("-d", "dictionary.txt"), ("-p", "postings.txt"), ("-q", "query.txt"), ("-o", "output.txt")]
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except(getopt.GetoptError, Exception):
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

if dictionary_file is None or postings_file is None or file_of_queries is None or file_of_output is None:
    usage()
    sys.exit(2)

try:
    # Load dictionary
    with open(dictionary_file, "r", encoding="utf-8") as dict_file:
        dict_text = dict_file.readlines()
        dictionary = dict()
        for dict_line in dict_text:
            dict_entry = dict_line.split()
            dictionary[dict_entry[0]] = (int(dict_entry[1]), int(dict_entry[2]))

    # Load lengths
    with open('document_lengths', 'rb') as len_file:
        doc_lengths = pickle.load(len_file)
    num_doc = len(doc_lengths)

    with open('document_length_sw_removed', 'rb') as len_swr_file:
        doc_lengths_swr = pickle.load(len_swr_file)

    # Load stop words
    with open('stop_words', 'rb') as sw_file:
        stop_words = pickle.load(sw_file)

    # Get all queries
    with open(file_of_queries, "r", encoding="utf-8") as query_file:
        queries = query_file.readlines()

    # Process queries
    with open(file_of_output, "w", encoding="utf-8") as out_file:
        for query in queries:
            stripped_query = query.strip()
            if len(stripped_query) == 0:
                out_file.write('\n')
                continue
            try:
                top_ten_scores = process_query(stripped_query)
                top_ten_docId = []
                for t in top_ten_scores:
                    top_ten_docId.append(t[1])
                ans = " ".join(top_ten_docId) + '\n'
            except:
                # Query is not valid and thus an empty list is returned
                ans = '\n'

            out_file.write(ans)

except IOError:
    sys.exit("Invalid file path")
