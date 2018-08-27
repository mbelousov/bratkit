import codecs
import os
import shutil


def makedirs(dirpath, remove=False):
    if remove and os.path.exists(dirpath):
        shutil.rmtree(dirpath)

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def save_documents(documents, output_path):
    makedirs(output_path, remove=True)
    for doc in documents:
        doc.save_brat(os.path.join(output_path, doc.uid))


def read_file_contents(filepath, encoding='utf-8'):
    """
    Reads file context
    """
    with codecs.open(filepath, 'r', encoding) as f:
        return f.read()
