import os
import tempfile
import unittest

from bratkit.reader import BratCorpusReader
from bratkit.models import AnnotatedDocument, Entity, Span

class TestAnnDocumentMerge(unittest.TestCase):
    def test_merge(self):
        d1 = AnnotatedDocument()
        d1.uid = "test"
        d1.text = "this is a sample document"
        d1.add(Entity(eid='T102', type='Person', span=Span(10, 16)))

        d2 = AnnotatedDocument()
        d2.uid = "test"
        d2.text = "this is a sample document"
        d2.add(Entity(eid='T1', type='Company', span=Span(17, 25)))

        d = AnnotatedDocument.from_pair(d1, d2)
        self.assertEqual(d1.text, d.text)
        self.assertEqual(d2.text, d.text)
        self.assertEqual(2, len(d.entities))
        self.assertTrue('T102' in d.entities)
        self.assertTrue('T103' in d.entities)
        self.assertEqual(d.entities['T102'].span, d1.entities['T102'].span)
        self.assertEqual(d.entities['T102'].content, d1.entities['T102'].content)
        self.assertEqual(d.entities['T103'].span, d2.entities['T1'].span)
        self.assertEqual(d.entities['T103'].content, d2.entities['T1'].content)
