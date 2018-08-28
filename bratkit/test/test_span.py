import unittest

from bratkit.models import Span, DiscontinuousSpan


class TestSpan(unittest.TestCase):
    def test_gt(self):
        self.assertGreater(Span(2, 5), Span(1, 8))
        self.assertGreater(Span(1, 9), Span(1, 4))

    def test_lt(self):
        self.assertLess(Span(2, 5), Span(3, 9))
        self.assertLess(Span(2, 5), Span(2, 9))


class TestDiscontinuousSpan(unittest.TestCase):
    def test_start_end(self):
        ds = DiscontinuousSpan((2, 5), (8, 19))
        self.assertEqual(ds.start, 2)
        self.assertEqual(ds.end, 19)
