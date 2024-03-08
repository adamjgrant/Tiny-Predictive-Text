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

    def test_pruning_input(self):
      tree = {"anchor": {"-": 2, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}, 
              "anchor2": {"-": 1, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}} 
      expected_pruned_tree = {"anchor": {"-": 2, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}} 
      pruned_tree = create_dictionary(tree, 1)

      self.assertEqual(pruned_tree, expected_pruned_tree)

    def test_doesnt_prune_special_keys(self):
      tree = {"anchor": 
                {
                  "second1": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "-": 2, 
                  "second2": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second3": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second4": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second5": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second6": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                }
             }
      expected_pruned_tree = {"anchor": 
                {
                  "second1": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "-": 2, 
                  "second2": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second3": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                  "second4": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}},
                }
             }
      pruned_tree = create_dictionary(tree, 1)

      self.assertEqual(pruned_tree, expected_pruned_tree)

    def test_token_dict(self):
      tree = {"anchor": {"-": 1, "second": {"-": 1, "first": {"-": 1, "_": {"a": 1, "b": 1, "c": 1}}}}} 
      expected_tokenized_tree = {0: {"-": 1, 1: {"-": 1, 2: {"-": 1, "_": {3: 1, 4: 1, 5: 1}}}}} 
      expected_dict = {}
      actual_tokenized_tree, actual_dict = create_token_dict(tree)

      self.assertEqual(actual_tokenized_tree, expected_tokenized_tree)
      

if __name__ == '__main__':
    unittest.main()