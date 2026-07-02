import unittest

from scripts.orchestrator.schema import validate_inputs


class TestInputSchema(unittest.TestCase):
    def test_required_and_type_validation(self):
        manifest = {
            "name": "review-pr",
            "input_schema": {
                "type": "object",
                "properties": {"pr_number": {"type": "string"}},
                "required": ["pr_number"],
            },
        }
        self.assertEqual(validate_inputs({}, manifest), ["Missing required argument 'pr_number'."])
        self.assertEqual(
            validate_inputs({"pr_number": 42}, manifest),
            ["Argument 'pr_number' should be string, got int."],
        )
        self.assertEqual(validate_inputs({"pr_number": "693"}, manifest), [])


if __name__ == "__main__":
    unittest.main()
