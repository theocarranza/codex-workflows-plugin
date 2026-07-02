import unittest
from scripts.orchestrator.evaluator import evaluate_output

class TestEvaluator(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "name": "start-ticket",
            "output_signature": {
                "type": "object",
                "required": ["success"],
                "properties": {
                    "active_ledger_path": {
                        "type": "string"
                    },
                    "success": {
                        "type": "boolean"
                    }
                }
            }
        }

    def test_evaluate_valid_output(self):
        valid_output = {
            "active_ledger_path": "/vault/Tickets/Active/TICKET-1.md",
            "success": True
        }
        critiques = evaluate_output(valid_output, self.manifest)
        self.assertEqual(len(critiques), 0, "Valid output should return 0 critiques")

    def test_evaluate_missing_property(self):
        invalid_output = {
            "active_ledger_path": "/vault/Tickets/Active/TICKET-1.md"
        }
        critiques = evaluate_output(invalid_output, self.manifest)
        self.assertEqual(len(critiques), 1)
        self.assertIn("Missing required output property 'success'", critiques[0])

    def test_evaluate_wrong_type(self):
        invalid_output = {
            "active_ledger_path": 12345,  # Should be string
            "success": "yes"              # Should be boolean
        }
        critiques = evaluate_output(invalid_output, self.manifest)
        self.assertEqual(len(critiques), 2)
        
        critique_texts = " ".join(critiques)
        self.assertIn("should be a string", critique_texts)
        self.assertIn("should be a boolean", critique_texts)

    def test_evaluate_wrong_base_type(self):
        # The schema expects a dictionary/object, not a raw string
        invalid_output = "/vault/Tickets/Active/TICKET-1.md"
        critiques = evaluate_output(invalid_output, self.manifest)
        self.assertEqual(len(critiques), 1)
        self.assertIn("Expected output to be a dictionary/object", critiques[0])

if __name__ == '__main__':
    unittest.main()
