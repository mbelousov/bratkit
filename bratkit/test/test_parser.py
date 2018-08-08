import unittest
from bratkit.models import Annotation, Span, DiscontinuousSpan
from bratkit.models import Entity, Attribute, Normalization, Relation, Note
from bratkit.models import Equiv
from bratkit.exceptions import UnsupportedAnnotationException


class TestBratParsing(unittest.TestCase):
    def test_unsupported_annotation_parser(self):
        self.assertRaises(UnsupportedAnnotationException,
                          Annotation.factory,
                          "X1	This is unsupported annotation")

    def test_entity_parser(self):
        ann = Annotation.factory("T1	EntityType 11 25	entity content")
        self.assertIsInstance(ann, Entity)
        self.assertEqual(ann.id, "T1")
        self.assertEqual(ann.type, "EntityType")
        self.assertEqual(ann.span, Span(11, 25))
        self.assertEqual(ann.content, "entity content")

    def test_discontinuous_entity_parser(self):
        line = "T1	EntityType 2 9;16 35	content and another content"
        ann = Annotation.factory(line)
        self.assertIsInstance(ann, Entity)
        self.assertEqual(ann.id, "T1")
        self.assertEqual(ann.type, "EntityType")
        self.assertEqual(ann.span, DiscontinuousSpan((2, 9), (16, 35)))
        self.assertEqual(ann.content, "content and another content")

    def test_multivalued_attribute_parser(self):
        ann = Annotation.factory("A1	AttrName T1 AttrValue")
        self.assertIsInstance(ann, Attribute)
        self.assertEqual(ann.id, "A1")
        self.assertEqual(ann.attr_name, "AttrName")
        self.assertEqual(ann.ann_id, "T1")
        self.assertEqual(ann.value, "AttrValue")

    def test_binary_attribute_parser(self):
        ann = Annotation.factory("A1	BinaryAttrName T1")
        self.assertIsInstance(ann, Attribute)
        self.assertEqual(ann.id, "A1")
        self.assertEqual(ann.attr_name, "BinaryAttrName")
        self.assertEqual(ann.ann_id, "T1")
        self.assertEqual(ann.value, True)

    def test_normalization_parser(self):
        ann = Annotation.factory(
            "N1	Reference T1 ExtResID:2	 entry value")
        self.assertIsInstance(ann, Normalization)
        self.assertEqual(ann.id, "N1")
        self.assertEqual(ann.type, "Reference")
        self.assertEqual(ann.resource_id, "ExtResID")
        self.assertEqual(ann.entry_id, "2")
        self.assertEqual(ann.entry_value, "entry value")

    def test_relation_parser(self):
        ann = Annotation.factory("R1	RelationType Arg1:T1 Arg2:T2")
        self.assertIsInstance(ann, Relation)
        self.assertEqual(ann.id, "R1")
        self.assertEqual(ann.type, "RelationType")
        self.assertEqual(len(ann.arguments), 2)
        self.assertEqual(ann.arguments.get('Arg1', None), "T1")
        self.assertEqual(ann.arguments.get('Arg2', None), "T2")

    def test_note_parser(self):
        ann = Annotation.factory("#1	AnnotatorNotes T1	note content")
        self.assertIsInstance(ann, Note)
        self.assertEqual(ann.id, "#1")
        self.assertEqual(ann.type, "AnnotatorNotes")
        self.assertEqual(ann.content, "note content")

    def test_equiv_parser(self):
        ann = Annotation.factory("*	Equiv T1 T2 T3")
        self.assertIsInstance(ann, Equiv)
        self.assertEqual(ann.id, '*')
        self.assertEqual(ann.type, "Equiv")
        self.assertEqual(len(ann.references), 3)
        self.assertEqual(ann.references[1], "T2")
