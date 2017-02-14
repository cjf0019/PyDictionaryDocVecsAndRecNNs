# -*- coding: utf-8 -*-
"""
Created on Mon Feb  6 14:45:50 2017
Sets up input and output arrays for a word vector deep neural network involving the PyDictionary 
definitions (originally found on WordNet). Word vectors are trained using a modified version of 
gensim's Doc2Vec (Doc2VecWordFixed). First, a vocabulary and vectors are generated using the Brown
Corpus and the Distributed Bag of Words Model. The docvecs are discarded and if the user
wishes replaced by the definitional words (by function 'build_docvecs'). 

The input of the neural network is the original vector for each word in the vocabulary
trained from the Brown Corpus. The output is equal to the average of all of the vectors
found in each word's definition and can include the docvec (labeled by the defitional word...
not included here yet but would need to concatenate these vectors to the others).
The conditional probabilities of the words and their contexts are reread, this time 
from the PyDictionary text. Unlike the original Doc2Vec, the weights are not reset, thus fixing the 
vectors from the previous Brown Corpus run.

@author: InfiniteJest
"""




import numpy as np
import re
import os
import nltk
tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
stops = set(nltk.corpus.stopwords.words("english"))
stops.update(['.',',','"',"'", '?', '!', ':', ';','(',')','[',']','{','}',"''",'``'])

import gensim

os.chdir('C:\\Users\\InfiniteJest\\Documents\\Python_Scripts')
new_file = open('GutenbergDictionary3.txt')
rawtext = new_file.read()
rawkeywords = re.findall('(?<=\n).*[A-Z]{3,}', rawtext)
rawwords = []
#Generate a list of sentences tokenized and uncapitalized
for i in re.split('[\n][\n].*?[A-Z]{3,}.*[\n]', rawtext):    
   x = i.lower()
   x = x.split()
   rawwords.append(x)

brownmodel = gensim.models.doc2vec.Doc2Vec.load('brownindocvecs')
vocabulary = brownmodel.vocab.keys()

def review_to_wordlist( list_of_sentences ):
    a = []    
    for sentences in list_of_sentences:
        b = []
        for words in sentences:
            x = re.sub("\'s", '', words.lower())           
            x2 = re.sub('^\$\d*$', 'money', x)
            x3 = re.sub('^1\d\d\d$', 'year', x2)
            x4 = re.sub('^\d+$', 'number', x3)
            x5 = re.sub('[^\w\s]', '', x4)
            words = x5
            b.append(words)
        b = [w for w in b if w in vocabulary]
        a.append(b)
    return a

definitions = review_to_wordlist(rawwords)

keywords = []
for word in rawkeywords:
    keywords.append(word.split('; '))

words = review_to_wordlist(keywords)

dictionary = list(zip(words, definitions))
dictionary = [l for l in dictionary if l[0] != []]
dictionary = [l for l in dictionary if l[1] != []]
dictionarywords = []
dictionarydefinitions = []
for i in range(len(dictionary)):
    dictionarywords.append(dictionary[i][0][0])
    dictionarydefinitions.append(dictionary[i][1])
    
dictionarydict = dict(zip(dictionarywords, dictionarydefinitions))
dictvalues = list(dictionarydict.values())
dictkeys = list(dictionarydict.keys())
dictkeys.sort()

from PyDictionary import PyDictionary

class PyDictionaryMod(PyDictionary):
    def write_to_file(self):              #original does not include a write_to_file option
        file = open('pydictionary.txt', 'a')
        try:
            dic = self.getMeanings()
            for key in dic.keys():
                file.write(key + ':')
                file.write("\n")
                try:
                    for k in dic[key].keys():
                        for m in dic[key][k]:   
                            file.write(m)
                            file.write("\n\n")
                except:
                    pass
        except:
            pass
        file.close()

#pydict = PyDictionaryMod(dictkeys)
#pydict.write_to_file()

#file = open('pydictionary.txt', 'r')
#x = file.read()
#x = re.sub('\(.*\n', '', x)
#x = re.sub('\n\n(?!.*\:\n)', '\n', x)
#x = re.sub('\;|\,', '', x)
#x = re.sub('(?=\n.*\:)', '\n', x)
#x = re.sub('\n.*\:\n\n', '', x)
#output = open('pydictionarymodified.txt', 'w')
#output.write(x)
#output.close()

new_file = open('pydictionarymodified.txt')
rawtext = new_file.read()
rawkeywords = re.findall('(?<=\n).*(?=:\n)', rawtext)
rawwords = []
for i in re.split('[\n][\n].*:[\n]', rawtext):    #Generates a list of sentences tokenized and uncapitalized
   x = i.lower()
   x = x.split('\n')
   rawwords.append(x)
   
definitions = []
for i in rawwords:
    definitionlist = []
    for j in i:
        if j != '':
            k = re.split(' ', j)
            k = [w for w in k if w != '']
            definitionlist.append(k)
    definitions.append(definitionlist)
    
dictionary = list(zip(definitions, rawkeywords))
dictionary.sort()
labeledsentences = []
for i, j in dictionary:
    labeledsentences.append(gensim.models.doc2vec.LabeledSentence(words=i, tags=j))

fullsentencelist= []
fulltaglist = []
for definition in labeledsentences:
    for sentence in definition.words:
        fullsentencelist.append(sentence)
    count = 0
    while count < len(definition.words):
        fulltaglist.append(definition.tags)
        count += 1


def train_document_dm(model, doc_words, doctag_indexes, alpha, work=None, neu1=None,
                      learn_doctags=True, learn_words=True, learn_hidden=True,
                      word_vectors=None, word_locks=None, doctag_vectors=None, doctag_locks=None, dnn=False):
    """
                          Expanded to include documents as lists of lists. Also added extra-layer
                          deep neural network training (Set dnn = True). The new word vectors are comprised
                          of the network output up to, but not including the last hidden layer (kept as syn1,
                          just as in Doc2Vec)
    """

    from numpy import dot    #Added so it could properly access word2vec
    if word_vectors is None:
        word_vectors = model.syn0
    if word_locks is None:
        word_locks = model.syn0_lockf
    if doctag_vectors is None:
        doctag_vectors = model.docvecs.doctag_syn0
    if doctag_locks is None:
        doctag_locks = model.docvecs.doctag_syn0_lockf

    if isinstance(doc_words[0], list):
        for sentence in doc_words:
            word_vocabs = [model.vocab[w] for w in sentence if w in model.vocab and
            model.vocab[w].sample_int > model.random.rand() * 2**32]
            for pos, word in enumerate(word_vocabs):
                reduced_window = model.random.randint(model.window)  # `b` in the original doc2vec code
                start = max(0, pos - model.window + reduced_window)
                window_pos = enumerate(word_vocabs[start:(pos + model.window + 1 - reduced_window)], start)
                word2_indexes = [word2.index for pos2, word2 in window_pos if pos2 != pos]
                l1 = np.sum(word_vectors[word2_indexes], axis=0) + np.sum(doctag_vectors[doctag_indexes], axis=0)
                count = len(word2_indexes) + len(doctag_indexes)
                if model.cbow_mean and count > 1 :
                    if dnn == True:                   
                        l1 /= count
                        neu1e = train_cbow_pair_dnn(model, word, word2_indexes, l1, alpha,
                                                                   learn_vectors=dnn, learn_hidden=learn_hidden)
                    else:
                        l1 /= count
                        neu1e = gensim.models.word2vec.train_cbow_pair(model, word, word2_indexes, l1, alpha,
                                                                   learn_vectors=False, learn_hidden=learn_hidden)                        

                if not model.cbow_mean and count > 1:
                    neu1e /= count
                if (dnn and not learn_words) or learn_words:  #dnn will learn the word vectors anyways
                    for i in word2_indexes:
                        word_vectors[i] += neu1e * word_locks[i]     
                if learn_doctags:
                    for i in doctag_indexes:
                        doctag_vectors[i] += neu1e * doctag_locks[i]
    else:
        word_vocabs = [model.vocab[w] for w in doc_words if w in model.vocab and
        model.vocab[w].sample_int > model.random.rand() * 2**32]
        for pos, word in enumerate(word_vocabs):
            reduced_window = model.random.randint(model.window)  # `b` in the original doc2vec code
            start = max(0, pos - model.window + reduced_window)
            window_pos = enumerate(word_vocabs[start:(pos + model.window + 1 - reduced_window)], start)
            word2_indexes = [word2.index for pos2, word2 in window_pos if pos2 != pos]
            l1 = np.sum(word_vectors[word2_indexes], axis=0) + np.sum(doctag_vectors[doctag_indexes], axis=0)
            count = len(word2_indexes) + len(doctag_indexes)
            if model.cbow_mean and count > 1 :
                    if dnn == True:                   
                        l1 /= count
                        neu1e = train_cbow_pair_dnn(model, word, word2_indexes, l1, alpha,
                                                                   learn_vectors=dnn, learn_hidden=learn_hidden)
                    else:
                        l1 /= count
                        neu1e = gensim.models.word2vec.train_cbow_pair(model, word, word2_indexes, l1, alpha,
                                                                   learn_vectors=False, learn_hidden=learn_hidden)                        

            if not model.cbow_mean and count > 1:
                neu1e /= count
            if (dnn and not learn_words) or learn_words:
                for i in word2_indexes:
                    word_vectors[i] += neu1e * word_locks[i]     
            if learn_doctags:
                for i in doctag_indexes:
                    doctag_vectors[i] += neu1e * doctag_locks[i]
    return len(word_vocabs)
    
    
def train_cbow_pair_dnn(model, word, input_word_indices, l1, alpha, learn_vectors=True, learn_hidden=True):
    neu1e = np.zeros(l1.shape)

    p1 = np.sum(model.syn2[input_word_indices], axis=0)           #the previous layer's saved input weights
    count = len(input_word_indices)
    p1 /= count
    if model.hs:
        p2a = model.syn3[word.point]                                #the previous layer's saved hidden weights
        fpa = 1. / (1. + np.exp(-np.dot(p1, p2a.T)))                #the previous layer's activation function
        l2a = model.syn1[word.point]  # 2d matrix, codelen x layer1_size
        fa = 1. / (1. + np.exp(-np.dot(fpa, l2a.T)))  # uses previous layer's output as input
        ga = (1. - word.code - fa) * alpha  # vector of error gradients multiplied by the learning rate
        if learn_hidden:
            model.syn1[word.point] += np.outer(ga, p1)  # learn hidden -> output
        neu1e += np.dot(ga, l2a)  # save error

    if model.negative:
        # use this word (label = 1) + `negative` other random words not from this sentence (label = 0)
        p2b = model.syn3neg[word.point]
        fpb = 1. / (1. + np.exp(-np.dot(p1, p2b.T)))                #the previous layer's activation function 
        word_indices = [word.index]
        while len(word_indices) < model.negative + 1:
            w = model.cum_table.searchsorted(model.random.randint(model.cum_table[-1]))
            if w != word.index:
                word_indices.append(w)
        l2b = model.syn1neg[word_indices]  # 2d matrix, k+1 x layer1_size
        fb = 1. / (1. + np.exp(-np.dot(fpb, l2b.T)))  # uses previous layer's output as input
        gb = (model.neg_labels - fb) * alpha  # vector of error gradients multiplied by the learning rate
        if learn_hidden:
            model.syn1neg[word_indices] += np.outer(gb, p1)  # learn hidden -> output
        neu1e += np.dot(gb, l2b)  # save error

    if learn_vectors:
        # learn input -> hidden, here for all words in the window separately
        if not model.cbow_mean and input_word_indices:
            neu1e /= len(input_word_indices)
        for i in input_word_indices:
            model.syn0[i] += neu1e * model.syn0_lockf[i]

    return neu1e

class Doc2VecWordFixed(gensim.models.doc2vec.Doc2Vec):
    """
    A modification of Doc2Vec that allows for extra-layer deep neural network training... in addition to
    the input, projection, hidden, and output layers, it allows for the addition of a second hidden layer.
    The first layer must be trained with dbow and the second with dm. The first layer, both projection and hidden,
    is saved as syn2 and syn3 respectively. The document probability distributions can then be updated and the
    vocabulary words fixed with 'update probabilities' for training on new documents. Note: the docvecs
    are only inferred, not trained by the DNN.
    """
    def __init__(self, documents=None, size=300, alpha=0.025, window=8, min_count=5,
                 max_vocab_size=None, sample=0, seed=1, workers=1, min_alpha=0.0001,
                 dm=1, hs=1, negative=0, dbow_words=0, dm_mean=0, dm_concat=0, dm_tag_count=1,
                 docvecs=None, docvecs_mapfile=None, comment=None, trim_rule=None, dnn=False, **kwargs):
        self.dnn = dnn
        super(Doc2VecWordFixed, self).__init__(documents=documents, size=size, alpha=alpha, window=window, min_count=min_count,
                max_vocab_size=max_vocab_size, sample=sample, seed=seed, workers=workers, min_alpha=min_alpha,
                dm=dm, hs=hs, negative=negative, dbow_words=dbow_words, dm_concat=dm_concat,
                dm_tag_count=dm_tag_count, docvecs=docvecs, docvecs_mapfile=docvecs_mapfile, comment=comment,
                trim_rule=trim_rule)
    
    def _do_train_job(self, job, alpha, inits):
        work, neu1 = inits
        dnn = self.dnn
        tally = 0
        for doc in job:
            indexed_doctags = self.docvecs.indexed_doctags(doc.tags)
            doctag_indexes, doctag_vectors, doctag_locks, ignored = indexed_doctags
            if dnn == True:
                ifdnn = True
            else:
                ifdnn = False
            if self.sg:
                tally += gensim.models.doc2vec.train_document_dbow(self, doc.words, doctag_indexes, alpha, work,
                                             train_words=self.dbow_words, doctag_vectors=doctag_vectors, doctag_locks=doctag_locks)
            elif self.dm_concat:
                tally += gensim.models.doc2vec.train_document_dm_concat(self, doc.words, doctag_indexes, alpha, work, neu1,
                                                  doctag_locks=doctag_locks, learn_words=ifdnn)
            else:
                tally += train_document_dm(self, doc.words, doctag_indexes, alpha, work, neu1, 
                                           doctag_locks=doctag_locks, learn_words=ifdnn, dnn=dnn)
            self.docvecs.trained_item(indexed_doctags)

        return tally, self._raw_word_count(job)

    def build_docvecs(self, documents):
        self.docvecs = gensim.models.doc2vec.DocvecsArray()
        document_no = -1
        for document_no, document in enumerate(documents):
            document_length = len(document.words)
#            for tag in document.tags:        NOTE: Previously EACH SENTENCE had its own tag in a document... modifying so only one tag per document.
            self.docvecs.note_doctag(document.tags, document_no, document_length)   #Changed tag to document.tags
            self.docvecs.reset_weights(self)

    def update_probabilities(self, documents, min_count=None, sample=None, dry_run=False, keep_raw_vocab=False, trim_rule=None):
        """
            Put together from pieces scale_vocab and finalize_vocab and then modified further,
            this will generate the output probability distributions for a new set of documents,
            without resetting the weights of the word or document vectors.
        """
        from six import iteritems
        from collections import defaultdict

        document_no = -1
        total_words = 0
        vocab = defaultdict(int)
        for document_no, document in enumerate(documents):
            if isinstance(document.words, list):          #added to include documents as lists of sentences
                for sentence in document.words:
                    for word in sentence:
                        vocab[word] += 1
                total_words += len(document.words)
            else:
                for word in document.words:
                    vocab[word] += 1
                total_words += len(document.words)               

        self.corpus_count = document_no + 1
        self.raw_vocab = vocab
        print(self.raw_vocab.keys())        

        min_count = min_count or self.min_count
        retain_total = 0
        sample = sample or self.sample
        if not dry_run:
            self.index2word = []
            # make stored settings match these applied settings
            self.min_count = min_count
            self.sample = sample
        #keep words found in BOTH previous layer's vocab and in current documents... necessary for accurate probabilities
        retain_words = list(filter(lambda x: x in list(self.vocab.keys()), self.raw_vocab.keys()))
        self.vocab = {}
        for word, v in iteritems(self.raw_vocab):
            if word in set(retain_words): 
                retain_total += v      #might want to reexamine v here
                if not dry_run:            
                    self.vocab[word] = gensim.models.word2vec.Vocab(count=v, index=len(self.index2word))
                    self.index2word.append(word)
            
        # Precalculate each vocabulary item's threshold for sampling
        if not sample:
            # no words downsampled
            threshold_count = retain_total
        elif sample < 1.0:
            # traditional meaning: set parameter as proportion of total
            threshold_count = sample * retain_total
        else:
            # new shorthand: sample >= 1 means downsample all words with higher count than sample
            threshold_count = int(sample * (3 + np.sqrt(5)) / 2)


        downsample_total, downsample_unique = 0, 0
        for w in retain_words:
            v = self.raw_vocab[w]
            word_probability = (np.sqrt(v / threshold_count) + 1) * (threshold_count / v)
            if word_probability < 1.0:
                downsample_unique += 1
                downsample_total += word_probability * v
            else:
                word_probability = 1.0
                downsample_total += v
            if not dry_run:
                self.vocab[w].sample_int = int(round(word_probability * 2**32))

        if not dry_run and not keep_raw_vocab:
            self.raw_vocab = defaultdict(int)        #delete raw vocab

        # return from each step: words-affected, resulting-corpus-size
        report_values = {'downsample_unique': downsample_unique, 'downsample_total': int(downsample_total)}
        # print extra memory estimates
        report_values['memory'] = self.estimate_memory(vocab_size=len(retain_words))
        if self.hs:
            # add info about each word's Huffman encoding
            self.create_binary_tree()
        if self.negative:
            # build the table for drawing random words (for negative sampling)
            self.make_cum_table()
        return report_values



    
import wordvectorgenerator

model = Doc2VecWordFixed(wordvectorgenerator.labeledsentences2, size=100, workers=4, min_count=10, window=8, dm=0, dbow_words=1)
model.update_probabilities(labeledsentences)

word_vectors = model.syn0
out = np.array([])
words = []
passedcount = 0
for definition in labeledsentences:
    if definition.tags not in set(model.vocab.keys()):
        pass
    else:
        for sentence in definition.words:
            word_vocabs = [model.vocab[w] for w in sentence if w in model.vocab and
            model.vocab[w].sample_int > model.random.rand() * 2**32]
            for pos, word in enumerate(word_vocabs):
                reduced_window = model.random.randint(model.window) 
                start = max(0, pos - model.window + reduced_window)
                window_pos = enumerate(word_vocabs[start:(pos + model.window + 1 - reduced_window)], start)
                word2_indexes = [word2.index for pos2, word2 in window_pos if pos2 != pos]
                l1 = np.sum(word_vectors[word2_indexes], axis=0)
                count = len(word2_indexes)
                if np.isnan(l1/count).any():
                    passedcount += 1
                elif len(out) == 0:
                    out = np.append(out, l1/count)
                    words.append(definition.tags)
                else:
                    out = np.vstack([out, l1/count])
                    words.append(definition.tags)

print('finished out')
print('Passed Arrays=', passedcount)

inp = np.array([])
for word in words:
    x = list(model.vocab).index(word)    
    if len(inp) == 0:
        inp = np.append(inp, model.syn0[x])
    else:    
        inp = np.vstack([inp, model.syn0[x]])

print('finished inp')

np.save('pydicdnninp.py', inp)
np.save('pydicdnnout.py', out)
