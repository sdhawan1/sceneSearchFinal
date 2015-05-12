#use this file while debugging
#want to add features like allowing all database data to be printed

import pickle
import os

#first, print the files that should be present in the db.
fdblist = open('./data/doc_list.pkl', 'rb')
dblist = pickle.load(fdblist)
fdblist.close()
print "files in the database list:"
print dblist

#now, print the things present in the inverted index.
fiindex = open('./data/iindex.pkl', 'rb')
iindex = pickle.load(fiindex)
fiindex.close()

iind_docs = []
for wd in iindex:
    pdocs = [p[0] for p in iindex[wd]]
    iind_docs += pdocs

iind_docs = list(set(iind_docs))
print "files in the inverted index:"
print iind_docs

#check that the same files are in the inverted index and the db list.
for f in iind_docs:
    if not f in dblist:
        print "error: %s in inverted index, but not dblist" % f

for f in dblist:
    if not f in iind_docs:
        print "error: %s in dblist, but not in inverted index." % f

    
#check that there are no extra split files.
for fname in iind_docs:
    fsplitname = "./data/splitdocs/" + fname + "_split.pkl"
    if not os.path.exists(fsplitname):
        print "error: %s does not have a snippet file." % fname
    
