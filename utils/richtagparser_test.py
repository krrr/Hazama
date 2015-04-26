import unittest
from hazama.ui.customobjects import NTextDocument


class NTextDocumentFormatsTest(unittest.TestCase):
    def test_overlap(self):
        test_str = 'This is something, string, string.\nparagraph, paragraph!\n    method?'
        test_fmt = [(0, 2, 1), (0, 2, 2), (0, 10, 3), (5, 15, 4), (34, 3, 5)]
        # output formats may be duplicated, because Qt store format this way
        true_result = [
            (0, 2, 1), (0, 2, 2),
            (0, 2, 3), (2, 3, 3), (5, 5, 3),  # from (0, 10, 3), broken into three parts
            (5, 5, 4), (10, 10, 4),  # from (5, 15, 4)
            (35, 2, 5)  # 34 is \n
        ]
        doc = NTextDocument()
        doc.setText(test_str, test_fmt)
        result = NTextDocument.getFormats(doc)
        self.assertEqual(true_result, result)


if __name__ == '__main__':
    unittest.main()