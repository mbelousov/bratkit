import unittest

from bratkit.reader import BratCorpusReader


class TestBratCorpusReader(unittest.TestCase):
    def test_corpus_reader(self):
        corpus = BratCorpusReader('./corpus/')
        self.assertEqual(len(corpus.documents), 2)
        self.assertEqual(corpus.documents[0].id, 'PMID-10438731')
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
        self.assertRaises(FileNotFoundError, corpus.read_corpus)
