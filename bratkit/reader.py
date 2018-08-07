import json
import os
import codecs
import glob

from bratkit.models import AnnotatedDocument
def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default

def read_file_contents(filepath, encoding='utf-8'):
    """
    Reads file context
    """
    with codecs.open(filepath, 'r', encoding) as f:
        return f.read()

class BratCorpusReader(object):
    def __init__(self, corpus_path):
        self.corpus_path = corpus_path
        self._documents = []

    @property
    def documents(self):
        if not self._documents:
            self.read_corpus()
        return self._documents

    def read_corpus(self):
        self._documents = []
        for doc in self.iterate_corpus():
            self._documents.append(doc)

    def iterate_corpus(self):
        filepaths = self.get_files()
        for i, filepath in enumerate(filepaths):
            d = self.process_document(filepath)
            if d is None:
                continue
            yield d

    def get_files(self):
        if not os.path.exists(self.corpus_path):
            raise FileNotFoundError("%s doesn't exist" % self.corpus_path)
        return sorted(glob.glob(os.path.join(self.corpus_path, '*.ann')))

    def process_document(self, filepath):
        doc = AnnotatedDocument()
        doc.readfile(filepath)
        doc.text = read_file_contents(filepath[:-4] + '.txt')
        return doc