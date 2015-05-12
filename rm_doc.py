#The purpose of this file is to remove a document from the existing data structures.

#imports
import pickle
import os
import sys

#--------------------------------------------------------------------------------#
#Start by getting all the necessary input arguments and checking if they're valid.

#retrieve the input document as a command line argument:
if not (len(sys.argv) == 2):
    print "correct usage: python add_doc.py filename"

rmfname = sys.argv[1]

#first, we want to check if the file is in the official database record
#the below should be constant for the whole app
dbdir = "data/"
fdoclist = open(dbdir + "doc_list.pkl", "rb")
doclist = pickle.load(fdoclist)
if rmfname in doclist:
    #remove from list
    doclist.remove(rmfname)
    fdoclist.close()
    fdoclist = open(dbdir + "doc_list.pkl", "wb")
    pickle.dump(doclist, fdoclist)
    fdoclist.close()
else:
    print "file not in the doclist. Files in the doclist include:"
    for doc in doclist:
	print doc


#--------------------------------------------------------------------------------#
#now, remove the snippet file
splitname = "./" + dbdir + "splitdocs/" + rmfname + "_split.pkl"
if os.path.exists(splitname):
    os.remove(splitname)
else:
    print "file snippets not found."


#--------------------------------------------------------------------------------#
#finally, clear the inverted index postings lists.

print "clearing postings list..."

#finally, remove the file from the inverted index.
fiind = open(dbdir + "iindex.pkl", "rb")
iindex = pickle.load(fiind)
fiind.close()
for wd in iindex:
    #check if the filename is in the wd list.
    postings = iindex[wd]
    filenames = [p[0] for p in postings]
    setfnames = list(set(filenames))
    if not (rmfname in setfnames):
        continue
    
    #otherwise, find the right indices to remove
    i = filenames.index(rmfname)
    while i < len(postings):
        if (rmfname == postings[i][0]):
            del(postings[i])
        else:
            i += 1

    #old method; not working...
    """
    #if the current file is the last in the index...
    if(setfnames.index(rmfname) < (len(setfnames)-1)):
        nextsind = setfnames.index(rmfname) + 1
        nextfname = setfnames[nextsind]
        iend = filenames.index(nextfname)
    else:
        iend = len(filenames)-1
    
    #now, remove the right indices
    rminds = range(iend, istart-1, -1)
    for ind in rminds:
        del postings[ind]
    """

    iindex[wd] = postings
    #[debugging] print iindex[wd]
    
#[debugging] print iindex
fiind = open(dbdir + "iindex.pkl", "wb")
pickle.dump(iindex, fiind)
fiind.close()
print "postings list cleared."
