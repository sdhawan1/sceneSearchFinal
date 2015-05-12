
import sys
import os
import pickle
import nltk
import numpy
from collections import defaultdict
from operator import itemgetter

#------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#
# Ancillary functions
#------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#

#in this function, get the path of a .pkl file (starting from the /data folder) and load the object in that file
#into a data structure for use in the program.
def load_obj(path):
    f = open('./data/' + path, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj

#in this function, input the path of a .pkl file, starting again from /data, and input an object to be stored.
#this function will store that object in that .pkl file.
def save_obj(obj, path):
    f = open('./data/' + path, 'wb')
    pickle.dump(obj, f)
    f.close()

#taking two lists of words (terms and keys), return the list of words that is the intersection of those two lists.
def intersect_terms(terms, keys):
    terms_ret = []
    #keys should be = iindex.keys()
    for t in terms:
        if t in keys:
            terms_ret += [t]
    return terms_ret

#find the number of snippets in the database. Unfortunately, this currently involves opening all the snippet
#files and finding the number of snippets within them.
def num_snippets():
    doclist = load_obj('doc_list.pkl')
    N = 0
    for d in doclist:
        f = open('data/splitdocs/' + d + '_split.pkl', 'rb')
        splitdoc = pickle.load(f)
        N += len(splitdoc)
    splitdoc = []
    return N

#find the cosine similarity between a snippet (snip) and a query (query). Although in actuality it could be
#used to find the cosine similarity between any two documents.
def dotprod(snip, query):
    terms = intersect_terms(query.keys(), snip.keys())
    res = float( sum( [snip[t]*query[t] for t in terms] ) )
    #all snippets already have the same length, so no need to normalize the dot product.
    return res

#in this function, narrow down a postings list (postings) to its champions. Takes the number of results needed
# (currently 30). Returns a "champion" shortlist of postings called "champ_postings"
def find_champ_postings(nres, postings):
    if len(postings) < nres*3:
        return postings
    threshold_pctl = int(100 * float(nres*2)/len(postings)) #(threshold percentile)
    tfs = [p[2] for p in postings] #get all the tfs in the snippets.
    threshold_val = numpy.percentile(tfs, threshold_pctl)
    champ_postings = [p for p in postings if p[2] > threshold_val]
    return champ_postings


#this function finds and returns clumps to evaluate alongside snippets. It should take in the number of results to 
#return, in order to better calculate percentiles. It should also take in a hashtable, which matches each snippet
#id to its dot product score.
#it should return a list of tuples, matching a uniquely identified clump with its score (which can be done with 
#an average).
def find_clumps(nres, ht_snip_score):
    #discover all unique file names 
    filenames = [k.split(' ')[:-1] for k in ht_snip_score.keys()]
    filenames = [(' ').join(f) for f in filenames]
    filenames = list(set(filenames))
    #sort all keys by filenames
    snip_by_filename = {}
    for f in filenames:
        snip_by_filename[f] = []
    for s in ht_snip_score:
        sarr = s.split(' ')
        fn = (' ').join(sarr[:-1])
        snip_by_filename[fn] += [(s, int(sarr[-1]))] #has the snippet(0) and its id(1).
    
       #sort all snippets within filenames
    for f in snip_by_filename:
        fsnips = snip_by_filename[f]
        fsnips = sorted(fsnips, key = itemgetter(1))
        snip_by_filename[f] = fsnips
    
    #search for clumps within the filenames.
    clumps_ret = [] #add all successful clumps to this list.
    maxclumpsize = 65 #i.e. ~20,000 words.
    for f in snip_by_filename:
        fsnips = snip_by_filename[f]
        minid = fsnips[0][1]
        maxid = fsnips[-1][1]
        rangeid = maxid-minid
        clumpsize = 2
        #search for all the various clump sizes within the file.
        while (clumpsize < rangeid) and (clumpsize < maxclumpsize):
            csind = 0 #clumpstartind
            clumpstart = fsnips[csind][1]
            while (clumpstart+clumpsize) < maxid:
                clump_snips = [fsnips[csind]]
                clumpstart = fsnips[csind][1]
                clumpend = fsnips[csind][1] + clumpsize
                #gather all snippets in the clump
                j = 1
                while csind+j < len(fsnips):
                    if(fsnips[csind+j][1] < clumpend):
                        clump_snips += [fsnips[csind+j]]
                    else:
                        break
                    j += 1
                
                #now, compute the score of the clump and, if it's good, add clump to list.
                if len(clump_snips) > clumpsize*0.7: #0.7 is minimum clump density.
                    clumpscores = [ht_snip_score[s[0]] for s in clump_snips]
                    last_snipid = clump_snips[-1][1]
                    #may also need to improve calculation of scores.
                    clumps_ret += [(clump_snips[0][0]+'-'+str(last_snipid), numpy.mean(clumpscores))]
                
                #now, update the starting point of the clump.
                csdiff = len(clump_snips)
                if csdiff < 1:
                    csdiff = 1
                csind += csdiff
            
            clumpsize = clumpsize * 2
    
    return clumps_ret


#------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#
# Search.py: searches for the best results within the established database.
#------------------------------------------------------------------------------------------------------------------#
#------------------------------------------------------------------------------------------------------------------#

#starting the actual algorithm

#make sure all the setup has been done properly.
if (not os.path.exists('./data/iindex.pkl')) or (not os.path.exists('./data/doc_list.pkl')):
    print "The database files do not seem to be setup correctly."
    print "Use add_doc.py to setup the files you want to search."
    print "Use debug.py to make sure there are no problems with the setup."

#make sure the semantics of the request are valid.
if (len(sys.argv) < 2) or (len(sys.argv) == 3) or (len(sys.argv) > 4):
    print "Correct usage: python search.py 'query terms'"
    print "Optional:"
    print "-nr [number of results]"
    exit(0)
elif (len(sys.argv) == 4): #assume user is trying to specify number of results.
    #inputs should be in a specific order - make sure that's the case.
    if (not sys.argv[2] == "-nr") or (not sys.argv[3].isdigit()):
        print "Correct usage: python search.py 'query terms' -nr [number of results]"
        exit(0)        

#set values of the main input parameters
query = sys.argv[1]
if len(sys.argv) == 4:
    nres = int(sys.argv[3])
else:
    nres = 30 #default request number.

#make sure the processing is within reason
if len(query.split()) > 10:
    print "Too many terms in query. Max = 10 terms. Note that stopwords (is, and, or,...) have no bearing on the query."
    exit(0)
if nres > 200:
    print "Too many results requested. Max results = 200"
    exit(0)
#debugging only...
print "query: " + str(query)
print "results: " + str(nres)

#------------------------------------------------------------------------------------------------------------------#

#prepare for the main search. Narrow down the proper terms and compute their idfs.
iindex = load_obj('iindex.pkl')

#convert query into searchable terms, and find those present in the inverted index.
terms = nltk.word_tokenize(query)
terms = [w.lower() for w in terms if w.isalpha()]
#find the terms present in the iindex. If none, quit.
terms = intersect_terms(terms, iindex.keys())
terms = [t for t in terms if iindex[t]]

if not terms:
    print "Your search did not match anything in the database. Be sure to check your spelling."
    exit(0)

#compute idfs of all valid terms.
N = float(num_snippets())
idfs = {}
for t in terms:
    df = len(iindex[t])
    idfs[t] = numpy.log(N / df)
query_tfidf = idfs
print "query idfs: " + str(query_tfidf)

#-------------------------------------------------------------------------------------------------------------------#

#now, time to combine postings lists.
#this H.T. will hash a snippet str(fileno+id) to (a dict of terms hashed to their tfs in the snippet).
snippets = defaultdict(dict)
for t in terms:
    #Narrow down the postings list to get a champion list using one of the functions above.
    champ_postings = find_champ_postings(nres, iindex[t])
    print t + ' ' + str(champ_postings)
    #put all the postings into a hash table.
    for p in champ_postings:
        #p[0] should be the file name, and p[1] should be the snippet number.
        key = p[0] + ' ' + str(p[1])
        snippets[key][t] = p[2]
        
#for everything in the hash table, compute scores
res_snippets = []
ht_snip_score = {}
for s in snippets:
    #compute the dot product.
    dp = dotprod(snippets[s], query_tfidf)
    res_snippets += [(s, dp)]
    ht_snip_score[s] = dp

###now, find clumps to include in the search as well.
res_clumps = find_clumps(ht_snip_scores)

#sort the results.
res_snippets = sorted(res_snippets, key = itemgetter(1), reverse=True)
if len(res_snippets) > nres:
    print res_snippets[0:nres-1]
else:
    print res_snippets

#final output (for real)
f = open("search_results", "w")
print "\n\n***Results of Search***"
sind = 1
for s in res_snippets:
    print str(sind)+". "+s[0]
    f.write(s[0]+'\n')
    sind += 1
    if sind > nres:
        break
print "*Note: numbers corresponds to ids of text 'snippets' of length 300 words.\n"
f.close()
