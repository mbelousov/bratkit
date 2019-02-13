import codecs
import itertools
import json
import os
import random
from collections import OrderedDict
from copy import copy
from enum import Enum

from bratkit.exceptions import UnsupportedAnnotationException
from bratkit.utils import makedirs_file


class MergeMode(Enum):
    """
    The mode defines how two entities with the same TYPE should be merged
    """
    OVERLAP = 1  # only if two entities overlaps
    EXACT = 2  # only if two entities has exactly the same spans
    ALL = 3  # take all entities from both sets
    RIGHT_ONLY = 4
    LEFT_ONLY = 5


def merge_entities(entities1, entities2, merge=None):
    if merge is None:
        merge = {'*': MergeMode.ALL}

    entities = {}
    for e1 in entities1:
        em = merge.get(e1.type, merge['*'])
        valid = False
        if em == MergeMode.EXACT:
            valid = any(e1.span == e2.span and e1.type == e2.type
                        for e2 in entities2)
        elif em == MergeMode.OVERLAP:
            valid = any(e1.span.within(e2.span) and e1.type == e2.type
                        for e2 in entities2)
        elif em in (MergeMode.RIGHT_ONLY, MergeMode.ALL):
            valid = True
        if valid:
            entities[e1.eid] = e1

    shift = max([int(a.eid[1:]) for a in entities1])
    for e2 in entities2:
        em = merge.get(e2.type, merge['*'])
        if em in (MergeMode.ALL, MergeMode.LEFT_ONLY):
            if e2.eid in entities:
                e2.eid = "%s%d" % (e2.eid[0],
                                   int(e2.eid[1:]) + shift)
            entities[e2.eid] = e2
    return entities.values()


# def merge_annotation(self, annotation, shift, merge):
#
#     if merge == MergeMode.ALL:
#         annotation.eid = "%s%d" % (annotation.eid[0],
#                                    int(annotation.eid[1:]) + shift)
#     elif merge == MergeMode.EXACT:
#         anns = {aid: ann for aid, ann in self._annotations.items()
#                 if ann.type == annotation.type}
#         m = self.filter_annotations(
#             anns.items(),
#             cmp=lambda x, kw: x.span == kw['span'],
#             span=annotation.span)
#         if m:
#             self.add(annotation)
# def merge_many(self, annotations, shift, merge):
#     for ann in annotations:
#         self.merge_annotation(ann, shift, merge)
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default


class Span(object):
    """Span defined by start and end positions
    """
    start = 0
    end = 0

    def __init__(self, start=0, end=0):
        self.start = int(start)
        self.end = int(end)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and self.start ==
                other.start and self.end == other.end)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return (self.start < other.start
                or (self.start == other.start and self.end < other.end))

    def __le__(self, other):
        return self.__lt__(other) or self.__eq__(other)

    def __gt__(self, other):
        return (self.start > other.start
                or (self.start == other.start and self.end > other.end))

    def __ge__(self, other):
        return self.__gt__(other) or self.__eq__(other)

    def __hash__(self):
        return hash((self.start, self.end))

    def within(self, other):
        return self.start >= other.start and self.end <= other.end

    def shift(self, s):
        return Span(self.start + s, self.end + s)

    def overlaps(self, other):
        return min(self.end, other.end) - max(self.start, other.start) > 0

    @property
    def length(self):
        return self.end - self.start

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%d-%d" % (self.start, self.end)

    def __repr__(self):
        return str(self.to_json())

    def to_json(self):
        return self.start, self.end

    def get_span_text(self, text):
        return text[self.start:self.end]


class DiscontinuousSpan(Span):
    """Discontinuous span defined by multiple spans (e.g. 1-4, 6-8)
    """
    __spans = set()
    __ordered = []

    def __init__(self, *span_pairs):
        self.__spans = set()
        self.__ordered = None

        super(DiscontinuousSpan, self).__init__()
        for span_pair in span_pairs:
            self.add(Span(span_pair[0], span_pair[1]))

    def __eq__(self, other):
        eq = (isinstance(other, self.__class__) and self.length == other.length
              and self.num_subspans == other.num_subspans)
        i = 0
        while eq and i < self.num_subspans:
            eq = self.get(i) == other.get(i)
            i += 1
        return eq

    def add(self, span):
        self.__spans.add(span)
        self.__ordered = sorted(self.__spans)
        self.start = self.subspans[0].start
        self.end = self.subspans[-1].end

    def get(self, index):
        return self.subspans[index]

    @property
    def subspans(self):
        return self.__ordered

    @property
    def num_subspans(self):
        return len(self.__spans)

    def __unicode__(self):
        return ";".join([str(s) for s in self.subspans])

    def to_json(self):
        return list(self.subspans)

    @property
    def length(self):
        return sum([s.length for s in self.__spans])

    def get_span_text(self, text):
        return " ".join([text[s.start:s.end] for s in self.subspans])


class Annotation(object):
    """BRAT Annotation object (base)
    For more information see http://brat.nlplab.org/standoff.html
    """
    eid = None

    @staticmethod
    def factory(line=""):
        """
        Create an appropriate annotation representation based on line from
        .ann standoff format (http://brat.nlplab.org/standoff.html)
        :param line: Annotation line
        :return: Annotation representation
        """
        line = line.strip()
        if line == '':
            return None
        entry_id = line.split("\t")[0]
        if entry_id[0] == 'E':
            # print("SKIP EVENT: %s" % line)
            return None

        cls = ANNOTATION_MAP.get(entry_id[0], Annotation)
        if cls == Annotation:
            raise UnsupportedAnnotationException(line)

        return cls.from_line(line)

    def __init__(self, eid=None):
        self.eid = eid

    @classmethod
    def from_line(cls, line):
        raise NotImplementedError("not implemented")

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Ann: %s>" % self.eid

    def to_json(self):
        return self.__dict__

    @classmethod
    def get_plural(cls):
        endings = {'y': 'ies'}
        singular = cls.__name__
        plural = None
        for end, pl_end in endings.items():
            if singular.endswith(end):
                plural = singular[:-len(end)] + pl_end
        if not plural:
            plural = singular + 's'
        return plural

    @classmethod
    def get_kind_name(cls):
        return cls.get_plural().lower()

    @property
    def __plural__(self):
        return self.get_plural()

    def to_brat_row(self):
        raise NotImplementedError("not implemented.")

    def __hash__(self):
        return hash(self.to_brat_row())

    def __eq__(self, other):
        return (self.__class__ == other.__class__ and
                self.to_brat_row() == other.to_brat_row())


class Entity(Annotation):
    """Entity (text-bound) annotation
    """
    type = ""
    span = None
    content = ""

    def __init__(self, eid=None, type=None, span=None, content=None):
        super(Entity, self).__init__(eid)
        self.type = type
        self.span = span
        self.content = content
        self._validaite_data()

    @classmethod
    def from_line(cls, line):
        obj = Entity()
        obj.eid, info, content = line.strip().split("\t", 2)
        info_parts = info.split(None, 1)
        obj.type = info_parts[0]
        txt_spans = info_parts[1].split(";")
        if len(txt_spans) > 1:
            obj.span = DiscontinuousSpan()
            for txt_span in txt_spans:
                sp_start, sp_end = txt_span.split()
                obj.span.add(Span(sp_start, sp_end))
        else:
            sp_start, sp_end = txt_spans[0].split()
            obj.span = Span(sp_start, sp_end)
        obj.content = content.strip()
        obj._validaite_data()
        return obj

    def _validaite_data(self):
        if self.content is None:
            return False

        newline = "\n"
        if newline not in self.content:
            return True
        curr = 0
        lines = self.content.split(newline)
        dsp = DiscontinuousSpan()
        for line in lines:
            line = line.strip()
            dsp.add(Span(self.span.start + curr,
                         self.span.start + curr + len(line)))
            curr += len(line) + len(newline)
        self.span = dsp
        return True

    def __unicode__(self):
        return "<%s: %s[%s] %s>" % (
            self.eid, self.type, self.span, self.content)

    def to_brat_row(self):
        if isinstance(self.span, DiscontinuousSpan):
            span_value = ";".join([
                "%d %d" % (sp.start, sp.end)
                for sp in self.span.subspans])
        else:
            span_value = "%d %d" % (self.span.start, self.span.end)

        return "%s\t%s %s\t%s" % (
            self.eid, self.type, span_value, self.content.replace("\n", " ")
        )


class Attribute(Annotation):
    """Attribute annotation
    """
    attr_name = ""
    value = ""
    ann_id = None

    def __init__(self, eid=None, attr_name=None, ann_id=None, value=None):
        super(Attribute, self).__init__(eid)
        self.attr_name = attr_name
        self.ann_id = ann_id
        self.value = value

    @classmethod
    def from_line(cls, line):
        obj = Attribute()
        obj.eid, info = line.strip().split("\t")
        info_parts = info.split()
        obj.attr_name = info_parts[0]
        obj.ann_id = info_parts[1]
        if len(info_parts) > 2:
            obj.value = info_parts[2]
        else:
            obj.value = True
        return obj

    def __unicode__(self):
        return "<%s: %s %s>" % (
            self.eid, self.attr_name, self.ann_id)

    def to_brat_row(self):
        if self.value is None:
            return "%s\t%s %s" % (
                self.eid, self.attr_name, self.ann_id
            )

        return "%s\t%s %s %s" % (
            self.eid, self.attr_name, self.ann_id, self.value
        )


class Normalization(Annotation):
    """Normalization annotation
    See http://brat.nlplab.org/normalization.html
    """

    type = ""
    ref = None
    resource_id = None
    entry_id = None
    entry_value = None

    def __init__(self, eid=None, type=None, ref=None, external=None,
                 resource_id=None, entry_value=None):
        super(Normalization, self).__init__(eid)
        self.type = type
        self.ref = ref
        self.external = external
        self.resource_id = resource_id
        self.entry_value = entry_value

    @classmethod
    def from_line(cls, line):
        obj = Normalization()
        obj.eid, info, entry_value = line.strip().split("\t")
        obj.type, obj.ref, external = info.split()
        obj.resource_id, obj.entry_id = external.split(':')
        obj.entry_value = entry_value.strip()
        return obj

    def __unicode__(self):
        return "<%s: %s[%s] %s>" % (self.eid, self.resource_id, self.entry_id,
                                    self.entry_value)

    def to_brat_row(self):
        return "%s\t%s %s %s:%s\t%s" % (
            self.eid, self.type, self.ref, self.resource_id, self.entry_id,
            self.entry_value
        )


class Relation(Annotation):
    """Relation annotation
    """
    type = ""
    arguments = OrderedDict()

    def __init__(self, eid=None, type=None, arguments=None):
        super(Relation, self).__init__(eid)
        self.type = type
        if self.arguments and not isinstance(arguments, OrderedDict):
            self.arguments = OrderedDict(arguments)
        else:
            self.arguments = arguments

    @classmethod
    def from_line(cls, line):
        obj = Relation()
        obj.eid, info_data = line.split("\t")
        info = info_data.split()
        obj.type = info[0]
        obj.arguments = OrderedDict()
        for arg in info[1:]:
            k, v = arg.split(':')
            obj.arguments[k] = v
        return obj

    def __unicode__(self):
        return '<%s: %s %s>' % (
            self.eid, self.type, self.arguments
        )

    def to_json(self):
        obj = self.__dict__
        obj['arguments'] = self.arguments
        return obj

    def to_brat_row(self):
        argvalues = ["%s:%s" % (k, v) for k, v in self.arguments.items()]
        return "%s\t%s %s" % (self.eid, self.type, " ".join(argvalues))


class Equiv(Annotation):
    def __init__(self, eid=None, type=None, references=None):
        super(Equiv, self).__init__(eid)
        self.type = type
        self.references = references

    @classmethod
    def from_line(cls, line):
        obj = Equiv()
        obj.references = []
        obj.type = None
        obj.eid, info = line.split("\t")
        if obj.eid == '*':
            obj.eid = '%s%s' % ('*', str(random.random())[2:])
        parts = info.split(' ')
        obj.type, refs = parts[0], parts[1:]
        for ref in refs:
            obj.references.append(ref.strip())
        return obj

    def to_brat_row(self):
        return "%s\t%s %s" % (self.eid, self.type, " ".join(self.references))


class Note(Annotation):
    """Note annotation
    """

    def __init__(self, eid=None, type=None, ref=None, content=None):
        super(Note, self).__init__(eid)
        self.type = type
        self.ref = ref
        self.content = content

    @classmethod
    def from_line(cls, line):
        obj = Note()
        obj.eid, ann, content = line.split("\t")
        obj.type, obj.ref = ann.split(' ')
        obj.content = content
        return obj

    def __unicode__(self):
        return '<%s: %s "%s">' % (self.eid, self.ref, self.content)

    def to_brat_row(self):
        return "%s\t%s %s\t%s" % (self.eid, self.type, self.ref, self.content)


class AnnotatedDocument(object):
    def __init__(self):
        self.text = ""
        self.uid = 0
        self._annotations = {}

    def __parse_line(self, line):
        annotation = Annotation.factory(line)
        if annotation is None:
            return False
        self.add(annotation)
        return annotation

    def read_ann_file(self, filepath):
        self._annotations = {}
        # for _, cls in ANNOTATION_MAP.items():
        #     self._annotations[cls.get_kind_name()] = {}
        self.uid = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r') as f:
            for line in f:
                self.__parse_line(line)

    def get_highest_annotation_id(self, kind=None):
        if kind is None:
            anns = [ann for anns in self._annotations.values()
                    for ann in anns.values()]
        else:
            anns = self._get_annotations(kind).values()

        if anns:
            return max([int(a.eid[1:]) for a in anns])
        return 0

    @classmethod
    def from_pair(cls, doc1, doc2):
        d1 = copy(doc1)
        d2 = copy(doc2)

        d = AnnotatedDocument()
        assert d1.text == d2.text
        d.uid = d1.uid
        d.text = d1.text
        shift = d1.get_highest_annotation_id()

        d.add_many(d1.entities.values())
        d.add_many(d1.relations.values())
        d.add_many(d1.attributes.values())
        d.add_many(d1.normalizations.values())
        d.add_many(d1.notes.values())
        d.add_many(d1.equivs.values())

        d.add_many_shifted(d2.entities.values(), shift=shift)
        d.add_many_shifted(d2.relations.values(), shift=shift)
        d.add_many_shifted(d2.attributes.values(), shift=shift)
        d.add_many_shifted(d2.normalizations.values(), shift=shift)
        d.add_many_shifted(d2.notes.values(), shift=shift)
        d.add_many_shifted(d2.equivs.values(), shift=shift)

        return d

    @property
    def __entity_order(self):
        return ['T', 'N', 'R', '#']

    def _get_annotations(self, kind):
        k = kind.get_kind_name()
        self._annotations.setdefault(k, {})
        return self._annotations[k]

    def _remove_annotations(self, kind):
        k = kind.get_kind_name()
        if k in self._annotations:
            self._annotations[k] = {}

    def add_many(self, annotations):
        for ann in annotations:
            self.add(ann)

    def add(self, annotation):
        annset = self._get_annotations(annotation.__class__)
        if annotation.eid in annset:
            raise ValueError("Annotation %s is already exists." % (
                annotation.eid))
        annset[annotation.eid] = annotation

    def add_shifted(self, annotation, shift):
        annotation.eid = "%s%d" % (annotation.eid[0],
                                   int(annotation.eid[1:]) + shift)
        self.add(annotation)

    def add_many_shifted(self, annotations, shift):
        for ann in annotations:
            self.add_shifted(ann, shift)

    def clean_entities(self):
        return self._remove_annotations(Entity)

    def clean_relations(self):
        return self._remove_annotations(Relation)

    def clean_attributes(self):
        return self._remove_annotations(Attribute)

    def clean_normalizations(self):
        return self._remove_annotations(Normalization)

    def clean_notes(self):
        return self._remove_annotations(Note)

    def clean_equivs(self):
        return self._remove_annotations(Equiv)

    def clean_annotations(self):
        self._annotations = {}

    @property
    def entities(self):
        return self._get_annotations(Entity)

    @property
    def relations(self):
        return self._get_annotations(Relation)

    @property
    def attributes(self):
        return self._get_annotations(Attribute)

    @property
    def normalizations(self):
        return self._get_annotations(Normalization)

    @property
    def notes(self):
        return self._get_annotations(Note)

    @property
    def equivs(self):
        return self._get_annotations(Equiv)

    def get_entities_relations(self):
        ent_rels = {}
        for rid, rel in self.relations.items():
            args = {argname: self.entities[argval]
                    for argname, argval in rel.arguments.items()}
            # rows[rid] = (rel.type, args)
            e1, e2 = list(rel.arguments.values())
            ent_rels.setdefault(e1, {}).setdefault(e2, {})[rel.type] = args
        return ent_rels

    def get_relations_rows(self, rel_ent_pairs, neg='all',
                           dist_thresh=0, random_seed=None,
                           no_rel_label='NO_RELATION',
                           entfunc=None, labelfunc=None):
        if len(rel_ent_pairs) <= 0:
            raise ValueError("Provide entity pairs for relations!")
        if entfunc is None:
            entfunc = lambda doc, ent: "%s-%s" % (doc.uid, ent.span)
        if labelfunc is None:
            labelfunc = lambda x: x

        pos_rows = []
        neg_rows = []
        ent_rels = self.get_entities_relations()
        ent_types = {}
        for ent in self.entities.values():
            ent_types.setdefault(ent.type, []).append(ent)

        for et1, et2 in rel_ent_pairs:
            e1_list = ent_types.get(et1, [])
            e2_list = ent_types.get(et2, [])
            if isinstance(dist_thresh, dict):
                try:
                    dt = dist_thresh[et1][et2]
                except KeyError:
                    dt = dist_thresh[et2][et1]
            else:
                dt = int(dist_thresh)

            for e1, e2 in itertools.product(e1_list, e2_list):

                dist = (max(e1.span.end, e2.span.end) -
                        min(e1.span.start, e2.span.start) + 1)
                e1e2_rels = ent_rels.get(e1.eid, {}).get(e2.eid, {})
                if len(e1e2_rels) == 0:
                    labels = [no_rel_label]

                    if 0 < dt < dist:
                        # print("SKIP d=%d" % dist)
                        continue
                else:
                    labels = list(e1e2_rels.keys())
                row = (entfunc(self, e1), entfunc(self, e2), labelfunc(labels))
                if labels == [no_rel_label]:
                    neg_rows.append(row)
                else:
                    pos_rows.append(row)

        if neg == 'all':
            neg_lim = len(neg_rows)
        elif neg == 'auto':
            neg_lim = len(pos_rows)
        else:
            try:
                neg_lim = int(neg)
            except ValueError:
                raise ValueError("Invalid value for neg!")

        if neg_lim == 0:
            return pos_rows

        random.seed(random_seed)
        random.shuffle(neg_rows)
        neg_rows = neg_rows[:neg_lim]
        return pos_rows + neg_rows

    def __unicode__(self):
        return "<AnnotatedDoc>"

    def to_json(self):
        return {
            'eid': self.uid,
            'text': self.text,
            'annotations': self._annotations
        }

    def to_brat_rows(self):
        return [ann.to_brat_row()
                for anns in self._annotations.values()
                for ann in anns.values()]

    def save_brat(self, output_path):
        makedirs_file("%s.txt" % output_path)
        with codecs.open("%s.txt" % output_path, "w", "utf-8") as fp:
            fp.write(self.text)
        with codecs.open("%s.ann" % output_path, "w", "utf-8") as fp:
            fp.write("\n".join(self.to_brat_rows()))

    def filter_annotations(self, annotations, cmp=None, **kwargs):
        if cmp is None:
            cmp = lambda x, kw: True
        return [
            ann for k, anns in annotations
            for aid, ann in anns.items() if cmp(ann, **kwargs)
        ]

    def crop(self, span):
        cropped = AnnotatedDocument()
        cropped.uid = '%s_crop%s' % (self.uid, span)
        cropped.text = self.text[span.start:span.end]
        cr_annotations = self.filter_annotations(
            self._annotations.items(),
            cmp=lambda x, kw: x.span.within(kw['span']),
            span=span)
        for ann in cr_annotations:
            ann.span = ann.span.shift(-span.start)
            cropped.add(ann)
        return cropped


ANNOTATION_MAP = {
    'N': Normalization,
    'T': Entity,
    'R': Relation,
    '#': Note,
    'A': Attribute,
    '*': Equiv,
}
