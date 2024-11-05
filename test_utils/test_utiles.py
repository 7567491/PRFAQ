import unittest
from pathlib import Path
import json
from modules.utils import (
    load_config, 
    load_templates, 
    load_prompts, 
    load_history, 
    save_history, 
    load_letters, 
    add_letters_record
)

class TestUtils(unittest.TestCase):

    def setUp(self):
        # Set up any necessary test data or state
        self.config_path = Path("config/prompts.json")
        self.templates_path = Path("config/templates.json")
        self.prompts_path = Path("config/prompt.json")
        self.history_path = Path("config/prfaqs.json")
        self.letters_path = Path("config/letters.json")

    def test_load_config(self):
        config = load_config()
        self.assertIsInstance(config, dict)
        self.assertTrue(self.config_path.exists())

    def test_load_templates(self):
        templates = load_templates()
        self.assertIsInstance(templates, dict)
        self.assertTrue(self.templates_path.exists())

    def test_load_prompts(self):
        prompts = load_prompts()
        self.assertIsInstance(prompts, dict)
        self.assertTrue(self.prompts_path.exists())

    def test_load_history(self):
        history = load_history()
        self.assertIsInstance(history, list)
        self.assertTrue(self.history_path.exists())

    def test_save_history(self):
        item = {'content': 'test', 'type': 'test'}
        save_history(item)
        history = load_history()
        self.assertIn(item, history)

    def test_load_letters(self):
        letters = load_letters()
        self.assertIsInstance(letters, dict)
        self.assertTrue(self.letters_path.exists())

    def test_add_letters_record(self):
        result = add_letters_record(1000, 2000, 'test_api', 'test_operation')
        self.assertTrue(result)
        letters = load_letters()
        self.assertGreater(letters['total']['input_letters'], 0)
        self.assertGreater(letters['total']['output_letters'], 0)

if __name__ == '__main__':
    unittest.main()