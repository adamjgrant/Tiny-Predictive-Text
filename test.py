import unittest

from lib.finish_filing import main as finish_filing
from lib.create_dictionary import create_dictionary, create_token_dict, remove_scores_and_flatten_predictions
from lib.merge_epochs import merge

class TestFiling(unittest.TestCase):
    def test_basic_input(self):
        tree_store = {}
        context_words = { "context_window": ["first", "second"], "anchor": "anchor" }
        predictive_words = ["a", "b", "c"]
        actual = finish_filing(tree_store, context_words, predictive_words)
        expected = { "anchor": { "score": 1, "second": { "score": 1, "first": { "score": 1, "predictions": [ {"prediction": ["a", "b", "c"], "score": 1} ] } } } }

        self.assertEqual(actual, expected)

class TestCreateDictionary(unittest.TestCase):
    def test_basic_input(self):
      tree = { "anchor": { "score": 1, "second": { "score": 1, "first": { "score": 1, "predictions": [ {"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1} ] } } } }
      pruned_tree = create_dictionary(tree, 1000)

      self.assertEqual(pruned_tree, tree)

    def test_pruning_input(self):
      tree = { "anchor": { "score": 2, "second": { "score": 1, "first": { "score": 1, "predictions": [ {"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1} ] } } }, 
        "anchor2": { "score": 1, "second": { "score": 1, "first": { "score": 1, "predictions": [ {"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1} ] } } } }
      expected_pruned_tree = { "anchor": { "score": 2, "second": { "score": 1, "first": { "score": 1, "predictions": [ {"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1} ] } } } }      
      pruned_tree = create_dictionary(tree, 1)

      self.assertEqual(pruned_tree, expected_pruned_tree)

    def test_doesnt_prune_special_keys(self):
      tree = {
          "anchor": {
              "second1": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "score": 2,
              "second2": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second3": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second4": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second5": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second6": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}}
          }
      }
      expected_pruned_tree = {
          "anchor": {
              "second1": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "score": 2,
              "second2": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second3": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}},
              "second4": {"score": 1, "first": {"score": 1, "predictions": [{"prediction": ["a", "a2", "a3"], "score": 1}, {"prediction": ["b", "b2", "b3"], "score": 1}, {"prediction": ["c", "c2", "c3"], "score": 1}]}}
          }
      }
      pruned_tree = create_dictionary(tree, 1)

      self.assertEqual(pruned_tree, expected_pruned_tree)

    def test_token_dict(self):
      tree = {"anchor": {"score": 1, "second": {"score": 1, "first": {"score": 1, "predictions": [{ "prediction": ["a", "a2", "a3"], "score": 1}, { "prediction": ["b", "b2", "b3"], "score": 1 }, { "prediction": ["c", "c2", "c3"], "score": 1 } ]}}}} 
      expected_tokenized_tree = {1: {2: {12: [[3,4,5], [6,7,8], [9,10,11]]}}} 
      simplified = remove_scores_and_flatten_predictions(tree)
      actual_tokenized_tree = create_token_dict(simplified)

      self.assertEqual(actual_tokenized_tree, expected_tokenized_tree)

class TestMergingAndPruningEpochs(unittest.TestCase):      
    def test_merging_epochs(self):
        tree_1 = {
                   "a": {"score": 0, "a1": {"score": 0, "a2": { "score": 0, "predictions": [["ax", "ay", "az"], ["aalpha", "abeta", "atheta"]]}}},
                   "b": {"score": 0, "b1": {"score": 0, "b2": { "score": 0, "predictions": [["bx", "by", "bz"], ["balpha", "bbeta", "btheta"]]}}},
                 }
        tree_2 = {
                   "a": {"score": 0, "a1": {"score": 0, "a2": { "score": 0, "predictions": [["ax", "ay", "az"], ["aalpha", "abeta", "atheta"]]}}},
                   "c": {"score": 0, "c1": {"score": 0, "c2": { "score": 0, "predictions": [["cx", "cy", "cz"], ["calpha", "cbeta", "ctheta"]]}}},
                 }
        expected_merged_tree = {
                      "a": {"score": 1, "a1": {"score": 1, "a2": { "score": 1, "predictions": [["ax", "ay", "az"], ["aalpha", "abeta", "atheta"]]}}},
                      "b": {"score": 0, "b1": {"score": 0, "b2": { "score": 0, "predictions": [["bx", "by", "bz"], ["balpha", "bbeta", "btheta"]]}}},
                      "c": {"score": 0, "c1": {"score": 0, "c2": { "score": 0, "predictions": [["cx", "cy", "cz"], ["calpha", "cbeta", "ctheta"]]}}},
        }
        actual_merged_tree = merge(tree_1, tree_2)

        self.assertEqual(actual_merged_tree, expected_merged_tree)

if __name__ == '__main__':
    unittest.main()