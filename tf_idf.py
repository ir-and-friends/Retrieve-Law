import math

# =========================================================================
#       Return the log-idf weight value
#           input: term frequency, num_doc, document frequency
#           output: docName(String)
# =========================================================================

def get_lt(tf, N, df):
    return (1.0 + math.log10(tf)) * math.log10(float(N) / float(df))

# =========================================================================
#       Return the log-none weight value
#           input: term frequency
#           output: ln value(String)
# =========================================================================

def get_ln(tf):
    return 1.0 + math.log10(tf)

# =========================================================================
#       Return the log-idf-cos norm value
#           input: term frequency, num_doc, document frequency, length
#           output: docName(String)
# =========================================================================

def get_ltc(tf, N, df, q_len):
    return (1.0 + math.log10(tf)) * math.log10(float(N) / float(df)) / q_len

# =========================================================================
#       Return the log-none-cos norm value
#           input: term frequency, document length
#           output: docName(String)
# =========================================================================

def get_lnc(tf, doc_len):
    return (1.0 + math.log10(tf)) / doc_len

# =========================================================================
#       Normalises based on LNC
#           input: words(dict)
#           output: docName(String)
# =========================================================================

def getLncLen(words):
    sum_w = 0.0
    for w in words:
        tf = words[w]
        sum_w += get_ln(tf) ** 2

    # Apply sqrt
    lnc_len = math.sqrt(sum_w)

    return lnc_len

# =========================================================================
#       Normalises based on LTC
#           input: dictionary(dict), words(dict)
#           output: docName(String)
# =========================================================================

def getLtcLen(postingHandler, words):
    N = postingHandler.getNumDoc()
    sum_w = 0.0
    for w in words:
        df = postingHandler.getDocFreq(w)
        tf = words[w]
        sum_w += get_lt(tf, N, df) ** 2

    # Apply sqrt
    ltc_len = math.sqrt(sum_w)

    return ltc_len
