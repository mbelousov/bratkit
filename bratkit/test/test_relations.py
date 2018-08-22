import unittest
from collections import Counter

from bratkit.reader import BratCorpusReader

def get_label_mentions(rows, label):
    all_labels = [item
                  for sl in [r[2] if r[2] else [False] for r in rows]
                  for item in sl]

    return Counter(all_labels).get(label, 0)


class TestRelations(unittest.TestCase):

    def __test_neg_sampling(self, neg, negval=None):
        if negval is None:
            negval = neg
        no_rel_label = "NO_RELATION"
        corpus = BratCorpusReader('./corpus/')
        rows = corpus.documents[0].get_relations_rows(
            [('Protein', 'Entity')], neg=neg, no_rel_label=no_rel_label)
        self.assertEqual(negval, get_label_mentions(rows, no_rel_label))
        return rows

    def test_get_relations_rows(self):
        corpus = BratCorpusReader('./corpus/')
        self.assertRaises(ValueError,
                          corpus.documents[0].get_relations_rows, [])
        rows = corpus.documents[0].get_relations_rows([('Protein', 'Entity')],
                                                      neg=None)
        self.assertEqual(544, len(rows))

    def test_get_relations_rows_neg_sampling_disabled(self):
        rows = self.__test_neg_sampling(neg=0)
        self.assertEqual(12, len(rows))

    def test_get_relations_rows_neg_sampling(self):
        rows = self.__test_neg_sampling(neg=5)
        self.assertEqual(12 + 5, len(rows))

    def test_get_relations_rows_neg_sampling_auto(self):
        rows = self.__test_neg_sampling(neg='auto', negval=12)
        self.assertEqual(12 + 12, len(rows))
