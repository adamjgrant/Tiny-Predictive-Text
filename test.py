import unittest

from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_dictionary, create_dictionary_and_tokenize, create_token_dict

class TestFiling(unittest.TestCase):
    def test_basic_input(self):
        tree_store = {}
        context_words = { "context_window": ["first", "second"], "anchor": "anchor" }
        predictive_words = ["a", "b", "c"]
        actual = finish_filing(tree_store, context_words, predictive_words)
        expected = {"anchor": {"-": 1, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}}
        
        self.assertEqual(actual, expected)

class TestCreateDictionary(unittest.TestCase):
    def test_basic_input(self):
      tree = {"anchor": {"-": 1, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}} 
      pruned_tree = create_dictionary(tree, 1000)

      self.assertEqual(pruned_tree, tree)

if __name__ == '__main__':
    unittest.main()