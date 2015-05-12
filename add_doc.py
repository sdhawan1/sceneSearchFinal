
import sys
import os
import nltk
import pickle
import operator
from nltk.corpus import stopwords
from nltk.probability import FreqDist
from operator import itemgetter

#----------------------------------------------------------------#
#preliminary checks
#confirm that a '.txt' file is entered as a command line argument.
if not (len(sys.argv) == 2):
    print "correct usage: python add_doc.py [path/to/filename.txt]"
    exit(0)
if not (sys.argv[1][-4:] == '.txt'):
    print "file %s not a '.txt' file" % sys.argv[1]
    exit(0)
if not os.path.exists(sys.argv[1]):
    print "could not find file: %s" % sys.argv[1]
    exit(0)

#otherwise read the file in. If there are some reading errors, don't want to
#update the database backup file before.
f = open(sys.argv[1])
ftxt = f.read()
f.close()


#ensure that a directory exists to store split documents and other data.
if not os.path.exists('./data'):
    os.makedirs('./data')
dbdir = "./data/splitdocs"
if not os.path.exists(dbdir):
    os.makedirs(dbdir)

#create a file to write output to
finpath = sys.argv[1].split('/')
fname = finpath[-1][:-4]
foutname = dbdir + "/" + fname + "_split.pkl"
if os.path.exists(foutname):
    print "error: file already setup. Use 'rm_file' to remove file."
    exit(0)

#create a file that backs up the documents in the inverted index
if not os.path.exists('./data/doc_list.pkl'):
    f = open('data/doc_list.pkl', 'wb')
    filedata = [fname]
    pickle.dump(filedata, f)
    f.close()
else:
    f = open('data/doc_list.pkl', 'rb')
    #should be a list that you can add file names to.
    filedata = pickle.load(f)
    f.close()
    if fname in filedata:
        print "error: file already in database. Use 'rm_file' to remove file."
        exit(0)

    filedata += [fname]
    f = open('data/doc_list.pkl', 'wb')
    pickle.dump(filedata, f)
    f.close()
    

#----------------------------------------------------------------#
#start the inverted index data structure - eventually will be stored in text file.
from collections import defaultdict
if not os.path.exists('./data/iindex.pkl'):
    iindex = defaultdict(list)
### TO-DO!!!
#else: read in the invertex index from a big master file called iindex.
else:
    findex = open('data/iindex.pkl', 'rb')
    iindex = pickle.load(findex)
    findex.close()

#----------------------------------------------------------------#
#start by dividing a document into 300-word pieces
#store this divided document into a new "pickle".
snippet_len = 300
snipid = 0
wds_tosort = []
doc_split = []

fwds = ftxt.split(' ')
fsnippetpts = range(0, len(fwds), snippet_len)[1:]

for pt in fsnippetpts:
    sniparr = fwds[(pt-300):pt]
    snip = (' ').join(sniparr)
    doc_split += [snip]
    sniparr = nltk.word_tokenize(snip)
    sniparr = [wd.lower() for wd in sniparr]
    snipfd = FreqDist(sniparr)
    
    #remove stopwords, nonalphabetical
    for wd in snipfd.keys():
        if not wd.isalpha():
            del snipfd[wd]

    for wd in stopwords.words('english'):
        if snipfd[wd] > 0:
            del snipfd[wd]
    
    #add these terms to the inverted index.
    for wd in snipfd.keys():
        #name of the file, id of snippet, and frequency in snippet.
        if snipfd[wd] > 0:
            iindex[wd] += [(fname, snipid, snipfd[wd])]
            wds_tosort += [wd]

    #increment id of snippet
    snipid += 1

#write to, and close the file that stores the snippets.
fout = open(foutname, "wb")
pickle.dump(doc_split, fout)
fout.close()

#---------------------------------------------------------------#
#now, sort all the modded words in the inverted index and add
#them back into the 'iindex' file

"""
wds_tosort = set(wds_tosort)
for wd in wds_tosort:
    ####Don't think the below is necessary; don't think there will be enough data.
    
    #sort postings to create champion lists.
    plist = iindex[wd]
    #sort all the postings by the frequency of word in snippet. [MAY BE BAD STATISTICS.]
    plist = sorted(plist, key=itemgetter(2), reverse=True)
    iindex[wd] = plist
    
    ####end unnecessariness

    plist = iindex[wd]
    print plist
""" 

#now, print this stuff into a master "pickle" file, called "iindex.pkl"
findex = open('data/iindex.pkl', 'wb')
pickle.dump(iindex, findex)
findex.close()





