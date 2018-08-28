class UnsupportedAnnotationException(Exception):
    def __init__(self, line):
        super(UnsupportedAnnotationException, self).__init__(
            "Unsupported  annotation: \"%s\"" % line)
