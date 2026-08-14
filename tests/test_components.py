import unittest
import sys
import os

# Add parent directory to path to import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from app.classifier import classify_query
from app.validator import count_sentences, has_advisory_language, validate_response

class TestClassifier(unittest.TestCase):
    def test_factual_query(self):
        self.assertEqual(classify_query("What is the exit load on HDFC Mid Cap Fund?"), "factual")
        self.assertEqual(classify_query("Who manages HDFC Defence Fund Direct Growth?"), "factual")
        self.assertEqual(classify_query("What is the minimum SIP amount for HDFC Small Cap Fund?"), "factual")

    def test_advisory_query(self):
        self.assertEqual(classify_query("Should I invest in HDFC Small Cap Fund?"), "advisory")
        self.assertEqual(classify_query("Which fund is better: HDFC Mid Cap or HDFC Small Cap?"), "advisory")
        self.assertEqual(classify_query("Recommend a fund for short term opportunities"), "advisory")

    def test_performance_query(self):
        self.assertEqual(classify_query("What are the historical returns of HDFC Defence Fund?"), "performance")
        self.assertEqual(classify_query("How has HDFC Balanced Advantage Fund performed over the last year?"), "performance")
        self.assertEqual(classify_query("Compare the return rate of these mutual funds"), "performance")


class TestValidator(unittest.TestCase):
    def test_count_sentences(self):
        self.assertEqual(count_sentences("This is a single sentence."), 1)
        self.assertEqual(count_sentences("This is one. This is two."), 2)
        # Check abbreviation handling
        self.assertEqual(count_sentences("Minimum SIP is Rs. 100. It is managed by Dr. Gopal."), 2)
        self.assertEqual(count_sentences("Min. SIP is Rs. 500. This is the second sentence. And this is three."), 3)

    def test_has_advisory_language(self):
        self.assertFalse(has_advisory_language("The expense ratio of HDFC Mid Cap Fund is 0.75%."))
        self.assertTrue(has_advisory_language("I suggest you should invest in this fund."))
        self.assertTrue(has_advisory_language("This is a highly recommended fund for you."))

    def test_validate_response(self):
        # Valid response: under 3 sentences, no advisory language
        is_valid, msg = validate_response("The exit load is 1% if redeemed within 1 year. Minimum SIP is Rs. 100.")
        self.assertTrue(is_valid)
        self.assertEqual(msg, "")

        # Invalid response: too long (> 3 sentences)
        is_valid, msg = validate_response("Sentence one. Sentence two. Sentence three. Sentence four.")
        self.assertFalse(is_valid)
        self.assertIn("exceeds 3 sentences", msg)

        # Invalid response: contains advisory language
        is_valid, msg = validate_response("The exit load is 1%. You should invest in this fund.")
        self.assertFalse(is_valid)
        self.assertIn("advisory language", msg)

if __name__ == "__main__":
    unittest.main()
