import os
from bratkit.reader import BratCorpusReader

if __name__ == '__main__':
    corpus_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                               'sample_corpus')
    corpus = BratCorpusReader(corpus_path)
    print("Documents in corpus: %d" % corpus.num_documents)
    for doc in corpus.documents:
        print('{:-^80}'.format(doc.uid))
        print("\"%s...\"" % doc.text[:75])
        for anntype, anns in doc.annotations.items():
            print("\t%d %s" % (len(anns), anntype))
