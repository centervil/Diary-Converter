"""
End-to-end integration tests for the diary converter
"""

import os
import unittest
import subprocess
from pathlib import Path

class TestEndToEnd(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.project_root = Path(__file__).parent.parent.parent  # Diary-Converter/ ディレクトリ
        self.test_dir = Path(__file__).parent.parent  # tests/ ディレクトリ
        self.fixtures_dir = self.test_dir / "fixtures"
        # Use the actual file in the fixtures directory
        fixture_files = list(self.fixtures_dir.glob("*.md"))
        if not fixture_files:
            raise FileNotFoundError(f"No markdown files found in {self.fixtures_dir}")
        self.input_file = fixture_files[0] # Use the first markdown file found
        self.output_file = self.test_dir / "output" / "integration_test_output.md"
        # Use the actual template file from the templates directory
        self.template_file = self.project_root / "templates" / "zenn_template.md"

        # Create output directory if it doesn't exist
        self.output_file.parent.mkdir(exist_ok=True)
        
        # Ensure API key is set
        if not os.getenv("GOOGLE_API_KEY"):
            self.skipTest("GOOGLE_API_KEY environment variable is not set")

    def test_cli_execution(self):
        """Test the command-line execution of the diary converter."""
        # Build the command
        cmd = [
            "python", "-m", "diary_converter.diary_converter",
            str(self.input_file),
            str(self.output_file),
            "--debug",
            "--template", str(self.template_file)
        ]
        
        # Execute the command
        try:
            result = subprocess.run(
                cmd,
                cwd=str(self.project_root),
                check=True,
                capture_output=True,
                text=True
            )
            
            # Print output for debugging
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            
            # Verify output file exists
            self.assertTrue(self.output_file.exists())
            
            # Verify output file is not empty
            self.assertGreater(self.output_file.stat().st_size, 0)
            
        except subprocess.CalledProcessError as e:
            self.fail(f"Command execution failed: {e}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")

    def tearDown(self):
        """Clean up after each test method."""
        # Remove output file if it exists
        if self.output_file.exists():
            self.output_file.unlink()

if __name__ == '__main__':
    unittest.main()
