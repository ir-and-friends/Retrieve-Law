#!/usr/bin/python
import re
import nltk
import sys
import getopt
import os
from nltk.stem.porter import *
import time
import math
import pickle


def process_word(input_word):
    return PorterStemmer().stem(input_word.strip())


def process_text(text):
    words = []
    # Remove numbers and special symbols to salvage strings like may/july from the next filter
    split_word = nltk.word_tokenize(text)
    for w in split_word:
        for w2 in re.split(r"[0123456789\\$+\-()*&./ \n']", w):
            # Filters out non-alphabetical terms and stop word removal
            if str.isalpha(w2):
                words.append(process_word(w2).lower())
    return words


def process_text_sw(text, sw):
    words = []
    # Remove numbers and special symbols to salvage strings like may/july from the next filter
    split_word = nltk.word_tokenize(text)
    for w in split_word:
        for w2 in re.split(r"[0123456789\\$+\-()*&./ \n']", w):
            # Filters out non-alphabetical terms and stop word removal
            if str.isalpha(w2) and w2 not in sw:
                words.append(process_word(w2).lower())
    return words


def normalize(words):
    temp_dict = {}
    norm_len = 0.0
    for w in words:
        if w in temp_dict:
            temp_dict[w] += 1
        else:
            temp_dict[w] = 1

    # Get all squared weights
    for w in temp_dict:
        wt = 1.0 + math.log(temp_dict[w], 10)
        norm_len += wt * wt

    # Apply sqrt
    norm_len = math.sqrt(norm_len)

    return [temp_dict, norm_len]


def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")


if __name__ == "__main__":
    input_directory = output_file_dictionary = output_file_postings = None
    all_doc_name_handle = "$all_docs"

    try:
        opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
        # r_data = "C:\\Users\\Juxarius\\AppData\\Roaming\\nltk_data\\corpora\\reuters\\training\\"
        # opts = [("-i", r_data), ("-d", "dictionary.txt"), ("-p", "postings.txt")]
    except (getopt.GetoptError, Exception):
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

    if input_directory is None or output_file_postings is None or output_file_dictionary is None:
        usage()
        sys.exit(2)

    try:
        file_list = os.listdir(input_directory)
        dictionary = dict()

        t1 = time.time()
        last_time = t1
        file_counter = 0
        doc_lengths = {}
        doc_lengths_sw_removed = {}  # new length after stop word removal
        print('Starting full scan...')

        for file_name in file_list:
            file_counter += 1

            if time.time() - last_time > 3:
                print("Currently processing file [{}/{}]".format(file_counter, len(file_list)))
                last_time = time.time()

            with open(input_directory + file_name, "r", encoding="utf-8") as doc:
                stem_word_list = process_text(doc.read())

            temp_dict, doc_lengths[file_name] = normalize(stem_word_list)
            for word in temp_dict:
                if word not in dictionary:
                    dictionary[word] = []
                dictionary[word].append((file_name, temp_dict[word]))

        # Stop word removal
        print('Retrieving stop words...')
        num_docs = len(file_list)
        sort_by_df = sorted(dictionary.items(), key=lambda kv: len(kv[1]), reverse=True)
        stop_words = []
        stop_word_limit = 0.5 * num_docs  # Stop words are defined as those appearing in more than half of the documents
        for kv in sort_by_df:
            if len(kv[1]) > stop_word_limit:
                stop_words.append(kv[0])
            else:
                break

        file_counter = 0
        last_time = time.time()
        print('Recalculating lengths with stop word removal...')
        for file_name in file_list:
            file_counter += 1
            if time.time() - last_time > 3:
                print("Currently processing file [{}/{}]".format(file_counter, len(file_list)))
                last_time = time.time()
            with open(input_directory + file_name, "r", encoding="utf-8") as doc:
                stem_word_list = process_text_sw(doc.read(), stop_words)
            temp_dict, doc_lengths_sw_removed[file_name] = normalize(stem_word_list)

        dict_file = open(output_file_dictionary, "w+")
        posting_file = open(output_file_postings, "w+", encoding="utf-8")

        dict_mapping = {}
        for word in sorted(dictionary):
            posting_line = []
            for df_pair in dictionary[word]:
                posting_line.append(df_pair[0] + "$" + str(df_pair[1]))
            start_pos = str(posting_file.tell())
            posting_file.write(" ".join(posting_line) + "\n")

            # each line in dictionary.txt follows the following format
            # <word> <start_pos>
            dict_file.write(word + " " + start_pos + " " + str(len(dictionary[word])) + '\n')

        with open('document_lengths', 'wb+') as len_file:
            pickle.dump(doc_lengths, len_file)

        with open('stop_words', 'wb') as sw_file:
            pickle.dump(stop_words, sw_file)

        with open('document_length_sw_removed', 'wb+') as len_swr_file:
            pickle.dump(doc_lengths_sw_removed, len_swr_file)

        t2 = time.time()
        print("Time taken to index: " + str(t2-t1) + "s")

        dict_file.close()
        posting_file.close()

    except IOError:
        sys.exit("Invalid directory")
