
#This file is designed to take the output stored in the "search_results" file, and package it more nicely, using document
#percentages and the actual text of the scenes to populate a new file called "interpreted_search_results".

import pickle


#in this function, get the path of a .pkl file (starting from the /data folder) and load the object in that file
#into a data structure for use in the program.
def load_obj(path):
    f = open('./data/' + path, 'rb')
    obj = pickle.load(f)
    f.close()
    return obj

#start by opening the "search_results" file.
frawres = open('search_results', 'r')
doc_snipind = []
docs = []
for line in frawres:
    linearr = line.split(' ')
    docs += [linearr[0]]
    snips = linearr[1]
    if '-' in snips: #means there are multiple snippets.
        snips = snips.split('-')
        doc_snipind += [ (linearr[0], int(snips[0]), int(snips[1])) ]
    else:
        doc_snipind += [(linearr[0], int(snips), int(snips))]
#[for debugging] print doc_snipind

#now, open the snippet files for each document and print out percentages
docs = list(set(docs))
docfiles = []
for doc in docs:
    docfiles += [load_obj('splitdocs/'+doc+'_split.pkl')]

#now, write the percentage starting points and the first few words of the results.
fintres = open('interpreted_search_results', 'w')
fintres.write('Search Results with Percentages:\n')
resno = 0
for s in doc_snipind:
    resno += 1
    docname = s[0]
    i = docs.index(docname)
    docfile = docfiles[i]
    #write the percent length of starting / ending point in the doc.
    pct_start = int( 100* float(s[1])/len(docfile) )
    if s[1] == s[2]:
        fintres.write(str(resno) + '. ' + docname + ': ' + 'beginning = ' + str(pct_start)+'%\n')
    else:
        clumplen = (s[2]-s[1])*300
        fintres.write(str(resno) + '. ' + docname + ': ' + 'beginning = ' + str(pct_start) + '%, length = ' + str(clumplen) + ' wds' + '\n')
    #write the first few characters
    fintres.write('\nBeginning:\n'+docfile[s[1]][:100]+'...\n\n')
    fintres.write('Ending:\n...'+docfile[s[2]][-100:]+'\n\n')
    
fintres.close()

