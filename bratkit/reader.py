from __future__ import print_function

import glob
import json
import os
import sys

from bratkit.models import AnnotatedDocument
from bratkit.utils import read_file_contents


def _default(self, obj):
    return getattr(obj.__class__, "to_json", _default.default)(obj)


_default.default = json.JSONEncoder().default
json.JSONEncoder.default = _default


class BratCorpusReader(object):
    def __init__(self, corpus_path, skip_errors=False):
        self.corpus_path = corpus_path
        self._documents = []
        self.skip_errors = skip_errors

    @property
    def documents(self):
        if not self._documents:
            self.read_corpus()
        return self._documents

    @property
    def num_documents(self):
        return len(self.documents)

    def read_corpus(self):
        self._documents = []
        for doc in self.iterate_corpus():
            self._documents.append(doc)

    def iterate_corpus(self):
        filepaths = self.get_files()
        for i, filepath in enumerate(filepaths):
            try:
                d = self.process_document(filepath)
                if d is None:
                    continue
                yield d
            except Exception as e:
                print("File: %s" % filepath, file=sys.stderr)
                print("Error: %s" % e, file=sys.stderr)
                if self.skip_errors:
                    continue
                raise e

    def get_files(self):
        if not os.path.exists(self.corpus_path):
            raise IOError("%s doesn't exist" % self.corpus_path)
        return sorted(glob.glob(os.path.join(self.corpus_path, '*.ann')))

    def process_document(self, filepath):
        doc = AnnotatedDocument()
        doc.readfile(filepath)
        doc.text = read_file_contents(filepath[:-4] + '.txt')
        return doc

    def validate(self):
        for doc in self.documents:
            self.validate_entities(doc)

    def validate_entities(self, doc, strip_content=False):
        for eid, ent in doc.annotations['entities'].items():
            doc_content = ent.span.get_span_text(doc.text)
            ent_content = ent.content
            if strip_content:
                doc_content = doc_content.strip()
                ent_content = ent_content.strip()

            if doc_content != ent_content:
                raise ValueError(
                    "Invalid entity annotation!"
                    "\n\tDoc: %s"
                    "\n\tEntity ID: %s"
                    "\n\tSpan: %s"
                    "\n\tContent: \"%s\""
                    "\n\tIn-document content: \"%s\"" % (
                        doc.uid, eid, ent.span, ent.content, doc_content
                    ))
