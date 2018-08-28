import os
import tempfile
import unittest

from bratkit.reader import BratCorpusReader


class TestBratCorpusReader(unittest.TestCase):
    def test_corpus_reader(self):
        corpus = BratCorpusReader('./corpus/')
        self.assertEqual(len(corpus.documents), 2)
        self.assertEqual(corpus.documents[0].uid, 'PMID-10438731')
        self.assertEqual(len(corpus.documents[0].annotations['entities']), 50)
        self.assertEqual(len(corpus.documents[0].annotations['relations']), 12)
        self.assertEqual(len(corpus.documents[0].annotations['equivs']), 1)
        self.assertEqual(len(corpus.documents[0].annotations['attributes']), 0)
        self.assertEqual(len(corpus.documents[0].annotations['notes']), 0)
        self.assertEqual(
            len(corpus.documents[0].annotations['normalizations']), 0)
        corpus.validate()

    def test_invalid_path(self):
        corpus = BratCorpusReader('./corpus_invalid/')
        self.assertRaises(IOError, corpus.read_corpus)

    def test_reliability(self):
        corpus = BratCorpusReader('./corpus/')
        self.assertEqual(len(corpus.documents), 2)

        with tempfile.TemporaryDirectory() as tmpdir:
            for doc in corpus.documents:
                doc.save_brat(os.path.join(tmpdir, doc.uid))

            tmp_corpus = BratCorpusReader(tmpdir)
            self.assertEqual(len(corpus.documents), len(tmp_corpus.documents))
            for d1, d2 in zip(corpus.documents, tmp_corpus.documents):
                self.assertEqual(d1.uid, d2.uid)
                # self.assertEqual(d1.annotations, d2.annotations)
                self.assertEqual(d1.annotations['equivs'],
                                 d2.annotations['equivs'])
