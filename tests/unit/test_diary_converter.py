"""
Unit tests for the diary converter module
"""

import os
import unittest
from pathlib import Path
from diary_converter.diary_converter import DiaryConverter

class TestDiaryConverter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(__file__).parent.parent  # tests/ ディレクトリ
        self.fixtures_dir = self.test_dir / "fixtures"
        self.input_file = self.fixtures_dir / "test_input.md"
        self.output_file = self.test_dir / "output" / "test_output.md"
        self.template_file = self.fixtures_dir / "test_template.md"
        
        # Create output directory if it doesn't exist
        self.output_file.parent.mkdir(exist_ok=True)
        
        # Ensure API key is set
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY environment variable is not set")

    def test_conversion(self):
        """Test the basic conversion functionality."""
        converter = DiaryConverter(
            model="gemini-2.0-flash-001",
            template_path=str(self.template_file),
            debug=True
        )
        
        # Perform conversion
        converter.convert(
            str(self.input_file),
            str(self.output_file)
        )
        
        # Verify output file exists
        self.assertTrue(self.output_file.exists())
        
        # Verify output file is not empty
        self.assertGreater(self.output_file.stat().st_size, 0)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove output file if it exists
        if self.output_file.exists():
            self.output_file.unlink()

if __name__ == '__main__':
    unittest.main()
