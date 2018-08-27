import unittest

from bratkit.models import Entity, Attribute, Relation, Normalization
from bratkit.models import Note, Equiv


class TestAnnotations(unittest.TestCase):
    def test_entity(self):
        ann0 = Entity("T1	EntityType 11 25	entity content")
        ann1 = Entity("T1	EntityType 11 25	entity content")
        ann2 = Entity("T2	EntityType 11 27	entity content 2")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_discont_entity(self):
        ann0 = Entity(
            "T1	EntityType 2 9;16 35	content and another content")
        ann1 = Entity(
            "T1	EntityType 2 9;16 35	content and another content")
        ann2 = Entity(
            "T2	EntityType 2 9;16 35	content and another content")

        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_multivalued_attribute(self):
        ann0 = Attribute("A1	AttrName T1 AttrValue")
        ann1 = Attribute("A1	AttrName T1 AttrValue")
        ann2 = Attribute("A2	AttrName2 T1 AttrValue2")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_normalization(self):
        ann0 = Normalization(
            "N1	Reference T1 ExtResID:2	 entry value")
        ann1 = Normalization(
            "N1	Reference T1 ExtResID:2	 entry value")
        ann2 = Normalization(
            "N1	Reference T1 ExtResID:3	 entry val")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_relation(self):
        ann0 = Relation("R1	RelationType Arg1:T1 Arg2:T2")
        ann1 = Relation("R1	RelationType Arg1:T1 Arg2:T2")
        ann2 = Relation("R1	RelationT Arg1:T2 Arg2:T3")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_note(self):
        ann0 = Note("#1	AnnotatorNotes T1	note content")
        ann1 = Note("#1	AnnotatorNotes T1	note content")
        ann2 = Note("#1	AnnotatorNotes T2	note value")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)

    def test_equiv(self):
        ann0 = Equiv("*	Equiv T1 T2 T3")
        ann1 = Equiv("*	Equiv T1 T2 T3")
        ann2 = Equiv("*	Equiv T2 T3")
        self.assertEqual(ann0, ann1)
        self.assertNotEqual(ann1, ann2)
        self.assertNotEqual(ann0, ann2)
