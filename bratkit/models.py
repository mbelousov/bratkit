import json
import os

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

    def get(self, index):
        return list(self.__spans)[index]

    def __unicode__(self):
        return ";".join([str(s) for s in self.__spans])

    def to_json(self):
        return list(self.__spans)

    @property
    def length(self):
        return sum([s.length for s in self.__spans])


class Annotation(object):
    """BRAT Annotation object (base)
    For more information see http://brat.nlplab.org/standoff.html
    """
    id = None

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
        self.id = line.split("\t")[0]

    def __str__(self):
        return self.__unicode__()

    def __unicode__(self):
        return "<Ann: %s>" % self.id

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
            self.id, self.type, self.span, self.content)


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
            self.id, self.attr_name, self.ann_id)


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
        return "<%s: %s[%s] %s>" % (self.id, self.resource_id, self.entry_id,
                                    self.entry_value)


class Relation(Annotation):
    """Relation annotation
    """
    type = ""
    arguments = {}

    def __init__(self, line):
        super(Relation, self).__init__(line)
        info = line.split("\t")[1].split()
        self.type = info[0]
        self.arguments = {}
        for arg in info[1:]:
            k, v = arg.split(':')
            self.arguments[k] = v

    def __unicode__(self):
        return '<%s: %s %s>' % (
            self.id, self.type, self.arguments
        )

    def to_json(self):
        obj = self.__dict__
        obj['arguments'] = self.arguments
        return obj


class Equiv(Annotation):
    def __init__(self, line):
        super().__init__(line)
        self.references = []
        self.type = None
        self.id, info = line.split("\t")
        parts = info.split(' ')
        self.type, refs = parts[0], parts[1:]
        for ref in refs:
            self.references.append(ref.strip())


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
        return '<%s: %s "%s">' % (self.id, self.ref, self.content)


class AnnotatedDocument(object):
    def __init__(self):
        self.annotations = {}
        self.text = ""
        self.id = 0

    def __parse_line(self, line):
        annotation = Annotation.factory(line)
        if annotation is None:
            return False
        k = annotation.__plural__.lower()
        self.annotations.setdefault(k, {})[annotation.id] = annotation

    def readfile(self, filepath):
        self.annotations = {}
        for _, cls in ANNOTATION_MAP.items():
            self.annotations[cls.get_plural().lower()] = {}
        self.id = os.path.splitext(os.path.basename(filepath))[0]
        with open(filepath, 'r') as f:
            for line in f:
                self.__parse_line(line)

    @property
    def __entity_order(self):
        return ['T', 'N', 'R', '#']

    def __unicode__(self):
        return "<AnnotatedDoc>"

    def to_json(self):
        return {
            'id': self.id,
            'text': self.text,
            'annotations': self.annotations
        }


ANNOTATION_MAP = {
    'N': Normalization,
    'T': Entity,
    'R': Relation,
    '#': Note,
    'A': Attribute,
    '*': Equiv,
}
