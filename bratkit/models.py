import codecs
import itertools
import json
import os
import random
from collections import OrderedDict

from bratkit.exceptions import UnsupportedAnnotationException


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

    @property
    def length(self):
        return self.end - self.start

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "%d-%d" % (self.start, self.end)

    def to_json(self):
        return self.start, self.end

    def get_span_text(self, text):
        return text[self.start:self.end]


class DiscontinuousSpan(Span):
    """Discontinuous span defined by multiple spans (e.g. 1-4, 6-8)
    """
    __spans = set()

    def __init__(self, *span_pairs):
        self.__spans = set()
        super(DiscontinuousSpan, self).__init__()
        for span_pair in span_pairs:
            self.add(Span(span_pair[0], span_pair[1]))

    def __eq__(self, other):
        eq = isinstance(other, self.__class__) and len(self.__spans) == len(
            other.__spans)
        i = 0
        while eq and i < len(self.__spans):
            eq = self.get(i) == other.get(i)
            i += 1
        return eq

    def add(self, span):
        self.__spans.add(span)
        self.start = min(self.__spans).start
        self.end = max(self.__spans).end

    def get(self, index):
        return list(self.__spans)[index]

    @property
    def subspans(self):
        return sorted(self.__spans)

    def __unicode__(self):
        return ";".join([str(s) for s in self.__spans])

    def to_json(self):
        return list(self.__spans)

    @property
    def length(self):
        return sum([s.length for s in self.__spans])

    def get_span_text(self, text):
        return " ".join([text[s.start:s.end] for s in sorted(self.__spans)])


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
        cls = ANNOTATION_MAP.get(entry_id[0], Annotation)
        if cls == Annotation:
            raise UnsupportedAnnotationException(line)

        return cls(line)

    def __init__(self, line):
        self.eid = line.split("\t")[0]

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

    def __init__(self, line):
        super(Entity, self).__init__(line)
        _, info, content = line.strip().split("\t")
        info_parts = info.split(None, 1)
        self.type = info_parts[0]
        txt_spans = info_parts[1].split(";")
        if len(txt_spans) > 1:
            self.span = DiscontinuousSpan()
            for txt_span in txt_spans:
                sp_start, sp_end = txt_span.split()
                self.span.add(Span(sp_start, sp_end))
        else:
            sp_start, sp_end = txt_spans[0].split()
            self.span = Span(sp_start, sp_end)
        self.content = content.strip()

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
            self.eid, self.type, span_value, self.content
        )


class Attribute(Annotation):
    """Attribute annotation
    """
    attr_name = ""
    value = ""
    ann_id = None

    def __init__(self, line):
        super(Attribute, self).__init__(line)
        _, info = line.strip().split("\t")
        info_parts = info.split()
        self.attr_name = info_parts[0]
        self.ann_id = info_parts[1]
        if len(info_parts) > 2:
            self.value = info_parts[2]
        else:
            self.value = True

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

    def __init__(self, line):
        super(Normalization, self).__init__(line)
        _, info, entry_value = line.strip().split("\t")
        self.type, self.ref, external = info.split()
        self.resource_id, self.entry_id = external.split(':')
        self.entry_value = entry_value.strip()

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
    entity_arguments = {}

    def __init__(self, line):
        super(Relation, self).__init__(line)
        info = line.split("\t")[1].split()
        self.type = info[0]
        self.arguments = OrderedDict()
        for arg in info[1:]:
            k, v = arg.split(':')
            self.arguments[k] = v

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
    def __init__(self, line):
        super(Equiv, self).__init__(line)
        self.references = []
        self.type = None
        self.eid, info = line.split("\t")
        parts = info.split(' ')
        self.type, refs = parts[0], parts[1:]
        for ref in refs:
            self.references.append(ref.strip())

    def to_brat_row(self):
        return "%s\t%s %s" % (self.eid, self.type, " ".join(self.references))


class Note(Annotation):
    """Note annotation
    """
    type = ""
    ref = None
    content = ""

    def __init__(self, line):
        super(Note, self).__init__(line)
        _, ann, content = line.split("\t")
        self.type, self.ref = ann.split(' ')
        self.content = content

    def __unicode__(self):
        return '<%s: %s "%s">' % (self.eid, self.ref, self.content)

    def to_brat_row(self):
        return "%s\t%s %s\t%s" % (self.eid, self.type, self.ref, self.content)


class AnnotatedDocument(object):
    def __init__(self):
        self.annotations = {}
        self.text = ""
        self.uid = 0

    def __parse_line(self, line):
        annotation = Annotation.factory(line)
        if annotation is None:
            return False
        k = annotation.__plural__.lower()
        self.annotations.setdefault(k, {})[annotation.eid] = annotation

    def readfile(self, filepath):
        self.annotations = {}
        for _, cls in ANNOTATION_MAP.items():
            self.annotations[cls.get_plural().lower()] = {}
        self.uid = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r') as f:
            for line in f:
                self.__parse_line(line)

    @property
    def __entity_order(self):
        return ['T', 'N', 'R', '#']

    def get_entities(self):
        return self.annotations.get('entities', {})

    def get_relations(self):
        return self.annotations.get('relations', {})

    def get_entities_relations(self):
        ent_rels = {}
        for rid, rel in self.annotations.get('relations', {}).items():
            args = {argname: self.annotations['entities'][argval]
                    for argname, argval in rel.arguments.items()}
            # rows[rid] = (rel.type, args)
            e1, e2 = list(rel.arguments.values())
            ent_rels.setdefault(e1, {}).setdefault(e2, {})[rel.type] = args
        return ent_rels

    def get_relations_rows(self, rel_ent_pairs, neg=None,
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
        for ent in self.get_entities().values():
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
        neg_lim = 0

        if neg == 'auto':
            neg_lim = len(pos_rows)
        elif neg and neg > 0:
            neg_lim = neg

        if neg_lim:
            random.seed(random_seed)
            random.shuffle(neg_rows)
            neg_rows = neg_rows[:neg_lim]
        if neg == 0:
            return pos_rows
        return pos_rows + neg_rows

    def __unicode__(self):
        return "<AnnotatedDoc>"

    def to_json(self):
        return {
            'eid': self.uid,
            'text': self.text,
            'annotations': self.annotations
        }

    def to_brat_rows(self):
        return [ann.to_brat_row()
                for anns in self.annotations.values()
                for ann in anns.values()]

    def save_brat(self, output_path):
        with codecs.open("%s.txt" % output_path, "w", "utf-8") as fp:
            fp.write(self.text)
        with codecs.open("%s.ann" % output_path, "w", "utf-8") as fp:
            fp.write("\n".join(self.to_brat_rows()))


ANNOTATION_MAP = {
    'N': Normalization,
    'T': Entity,
    'R': Relation,
    '#': Note,
    'A': Attribute,
    '*': Equiv,
}
