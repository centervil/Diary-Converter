"""
Unit tests for the diary converter module
"""

import os
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock # MagicMock を追加
from diary_converter.diary_converter import DiaryConverter

class TestDiaryConverter(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.test_dir = Path(__file__).parent.parent  # tests/ ディレクトリ
        self.fixtures_dir = self.test_dir / "fixtures"
        self.project_root = Path(__file__).parent.parent.parent # Diary-Converter/ ディレクトリを追加
        self.input_file = self.fixtures_dir / "test_input.md"
        self.output_file = self.test_dir / "output" / "test_output.md"
        # Use the actual template file from the templates directory
        self.template_file = self.project_root / "templates" / "zenn_template.md"

        # Create output directory if it doesn't exist
        self.output_file.parent.mkdir(exist_ok=True)

        # APIキーのチェックは不要 (モックするため)
        # if not os.getenv("GOOGLE_API_KEY"):
        #     self.skipTest("GOOGLE_API_KEY environment variable is not set")

    # genai.GenerativeModel をモック化
    # DiaryConverterクラスが定義されているモジュール内の 'genai.GenerativeModel' を指定
    @patch('diary_converter.diary_converter.genai.GenerativeModel')
    def test_conversion(self, MockGenerativeModel):
        """Test the basic conversion functionality using mocks."""
        
        # モックの設定: generate_content が呼ばれたらテンプレート構造を含むダミーテキストを返す
        mock_response = MagicMock()
        # テンプレートに含まれる見出しと、モック応答を示すテキストを含むように変更
        mock_response.text = """---
title: "Mock Title"
emoji: "🧪"
type: "tech"
topics: ["mock"]
published: false
---
## はじめに
Mocked LLM response content for unit test.
"""
        mock_instance = MockGenerativeModel.return_value
        mock_instance.generate_content.return_value = mock_response

        converter = DiaryConverter(
            # model名はモックするので実際には使われないが、指定は必要
            model="gemini-2.0-flash-001", 
            template_path=str(self.template_file),
            debug=True # デバッグ出力を有効にしておく
        )
        
        # Perform conversion
        converter.convert(
            str(self.input_file),
            str(self.output_file)
        )
        
        # モックが呼び出されたことを確認
        MockGenerativeModel.assert_called_once() # モデルがインスタンス化されたか
        # generate_content が適切な引数で呼び出されたか確認 (より詳細なテスト)
        # 実際のプロンプト内容に合わせて期待値を調整する必要がある
        # mock_instance.generate_content.assert_called_once_with(...) 
        mock_instance.generate_content.assert_called_once() # 少なくとも1回呼ばれたか

        # Verify output file exists
        self.assertTrue(self.output_file.exists())
        
        # Verify output file is not empty
        self.assertGreater(self.output_file.stat().st_size, 0)
        
        # Verify output content contains mocked response
        with open(self.output_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # テンプレートとモック応答が組み合わさった結果を確認
            # モック応答に含まれるテキストを確認
            self.assertIn("Mocked LLM response content for unit test.", content)
            # モック応答に含まれるテンプレート構造の一部を確認
            self.assertIn("## はじめに", content)
            # モック応答に含まれるFrontmatterの一部を確認
            self.assertIn("emoji: \"🧪\"", content)

    def tearDown(self):
        """Clean up after each test method."""
        # Remove output file if it exists
        if self.output_file.exists():
            self.output_file.unlink()

if __name__ == '__main__':
    unittest.main()
