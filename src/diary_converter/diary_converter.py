#!/usr/bin/env python3
"""
開発日記変換ツール

ProjectLogs以下の開発日記をLLM API（Gemini）を利用して加工し、
articles配下にZenn公開用日記として配置するスクリプト
"""

import os
import sys
import argparse
import frontmatter
import google.generativeai as genai
from datetime import datetime
import re

class TemplateManager:
    """テンプレート管理クラス（シンプル化版）"""
    
    def __init__(self, template_path, debug=False):
        """初期化"""
        self.template_path = template_path
        self.debug = debug
        
    def resolve_template_path(self):
        """テンプレートパスを解決する"""
        # GitHub Actions環境かどうかを判定
        github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
        action_path = os.environ.get("GITHUB_ACTION_PATH")

        if not os.path.isabs(self.template_path):
            # Docker環境かどうかを判定（/appディレクトリの存在で簡易判定）
            is_docker = os.path.exists('/app') and os.path.isdir('/app')
            
            if github_actions and action_path:
                # GitHub Actions環境で相対パスの場合、アクションのルートからの相対パスとして解決
                template_path = os.path.join(action_path, self.template_path)
                if self.debug:
                    print(f"GitHub Actions環境: アクションルートからの相対パスで解決: {template_path}")
            elif is_docker:
                # Docker環境の場合、/appからの相対パスとして解決
                template_path = os.path.join('/app', self.template_path)
                if self.debug:
                    print(f"Docker環境: /appからの相対パスで解決: {template_path}")
            else:
                # ローカル環境など、スクリプトの実行ディレクトリからの相対パス
                script_dir = os.path.dirname(os.path.abspath(__file__))
                # templatesディレクトリはsrcの一つ上の階層にある想定
                base_dir = os.path.dirname(script_dir)
                template_path = os.path.join(base_dir, self.template_path)
                if self.debug:
                    print(f"ローカル環境: スクリプトベースからの相対パスで解決: {template_path}")
        else:
            # 絶対パスの場合はそのまま使用
            template_path = self.template_path
            if self.debug:
                print(f"絶対パスとして解決: {template_path}")
        
        return template_path
            
    def load_template(self):
        """テンプレートファイルを読み込む"""
        try:
            template_path = self.resolve_template_path()
            
            # テンプレートファイルの存在確認
            if not os.path.exists(template_path):
                if self.debug:
                    print(f"テンプレートファイル '{template_path}' が見つかりません")
                    print(f"カレントディレクトリ: {os.getcwd()}")
                    print(f"スクリプトディレクトリ: {os.path.dirname(os.path.abspath(__file__))}")
                    github_actions = os.environ.get("GITHUB_ACTIONS") == "true"
                    if github_actions:
                        print(f"GITHUB_ACTION_PATH: {os.environ.get('GITHUB_ACTION_PATH')}")
                raise FileNotFoundError(f"テンプレートファイル '{template_path}' が見つかりません")

            with open(template_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            raise IOError(f"テンプレートファイル読み込み中にエラーが発生しました: {e}")
    
    def prepare_template(self, template_content, model_name, serial_number, prev_article_slug):
        """テンプレートを準備する（プレースホルダーを置換する）"""
        # テンプレートのプレースホルダーを置換
        prepared_template = template_content

        # モデル名の置換
        prepared_template = prepared_template.replace("[LLM Model名]", model_name)

        # 連番の置換
        prepared_template = prepared_template.replace("[連番]", serial_number)
        
        # 前回の記事スラッグの置換
        if prev_article_slug:
            # 単純な文字列置換に変更
            prepared_template = prepared_template.replace("[前回の記事スラッグ]", prev_article_slug)
        # else:
            # スラッグがない場合、リンク行全体を削除するか、プレースホルダーを残すか検討が必要
            # 現状ではプレースホルダーが残る
        
        return prepared_template

class DiaryConverter:
    """開発日記をZenn公開用の記事に変換するクラス"""

    def __init__(self, model="gemini-2.0-flash-001",
                 debug=False, prev_article_slug=None, template_path=None):
        """初期化"""
        self.model_name = model
        # template_path引数が指定されていれば使用し、なければ環境変数から取得、それもなければデフォルト値
        template_path = template_path or os.environ.get("TEMPLATE_PATH", "./templates/zenn_template.md")
        self.template_manager = TemplateManager(template_path, debug)
        self.debug = debug
        self.prev_article_slug = prev_article_slug  # 前回の記事スラッグ
        self.setup_api()

    def setup_api(self):
        """Gemini APIの設定"""
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY 環境変数が設定されていません")
        genai.configure(api_key=api_key)

    def read_source_diary(self, file_path):
        """開発日記ファイルを読み込む"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            raise IOError(f"ファイル読み込み中にエラーが発生しました: {e}")

    def extract_date_from_filename(self, file_path):
        """ファイル名から日付を抽出する"""
        filename = os.path.basename(file_path)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            return date_match.group(1)
        # 日付が見つからない場合はNoneを返すなど、エラーハンドリングを検討
        return None

    def extract_serial_number_from_filename(self, file_path):
        """ファイル名から通し番号を抽出する"""
        filename = os.path.basename(file_path)
        # 新しい命名規則 (YYYY-MM-DD_{通し番号}_development.md) から通し番号を抽出
        match = re.search(r'^\d{4}-\d{2}-\d{2}_(\d+)_development\.md$', filename)
        if match:
            return match.group(1)
        # 通し番号が見つからない場合はNoneを返すなど、エラーハンドリングを検討
        return None

    def generate_prompt(self, content, template_content):
        """Gemini APIに送信するプロンプトを生成する（シンプル化版）"""
        if not template_content:
            raise ValueError("テンプレート内容が提供されていません")
        
        # LLM指示部分を抽出
        llm_instructions_match = re.search(r'<!-- LLM_INSTRUCTIONS_START -->(.*?)<!-- LLM_INSTRUCTIONS_END -->', template_content, re.DOTALL)
        llm_instructions = llm_instructions_match.group(1) if llm_instructions_match else ""
        
        # プロンプトを生成
        prompt = f"""
{llm_instructions}

# 入力された開発日記
{content}
"""
        return prompt

    def convert_with_gemini(self, content, template_content):
        """Gemini APIを使用して開発日記を変換する（シンプル化版）"""
        prompt = self.generate_prompt(content, template_content)

        try:
            # 最新バージョンのライブラリに対応した呼び出し方法
            generation_config = {
                "temperature": 0.2,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4096,
            }

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                }
            ]

            model = genai.GenerativeModel(
                model_name=self.model_name,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"Gemini APIでのエラー: {e}")

    def save_converted_article(self, content, file_path):
        """変換された記事を保存する"""
        try:
            # 出力ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            if self.debug:
                print(f"記事を保存しました: {file_path}")
                print("記事の内容:")
                print("-----------------------------------")
                print(content)
                print("-----------------------------------")
        except Exception as e:
            raise IOError(f"ファイル保存中にエラーが発生しました: {e}")

    def convert(self, source_file, destination_file):
        """開発日記をZenn記事に変換する（シンプル化版）"""
        try:
            # 入力ファイルを読み込む
            content = self.read_source_diary(source_file)

            # テンプレートを読み込む
            template_content = self.template_manager.load_template()

            # ファイル名から日付と通し番号を抽出
            date = self.extract_date_from_filename(source_file)
            serial_number = self.extract_serial_number_from_filename(source_file)

            if not date or not serial_number:
                raise ValueError(f"ファイル名から日付または通し番号を抽出できませんでした: {source_file}")

            if self.debug:
                print(f"日付: {date}")
                print(f"通し番号: {serial_number}")

            # テンプレートを準備（プレースホルダーを置換）
            prepared_template = self.template_manager.prepare_template(
                template_content,
                self.model_name,
                serial_number,
                self.prev_article_slug
            )

            # Gemini APIで変換
            # LLMはテンプレート構造を含む完全な記事を生成すると期待される
            llm_generated_content = self.convert_with_gemini(
                content, prepared_template # プロンプト生成には準備済みテンプレートを使う
            )

            # LLMが生成した内容をそのまま保存
            self.save_converted_article(llm_generated_content, destination_file)

            return True
        except Exception as e:
            if self.debug:
                print(f"エラー: {e}")
            raise

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description="開発日記をZenn公開用に変換するツール")
    parser.add_argument("source", help="変換元の開発日記ファイルパス")
    parser.add_argument("destination", help="変換先のZenn記事ファイルパス")
    parser.add_argument("--model", default="gemini-2.0-flash-001", help="使用するGeminiモデル名")
    parser.add_argument("--debug", action="store_true", help="デバッグモードを有効にする")
    parser.add_argument("--template", default="./templates/zenn_template.md", help="使用するテンプレートファイルのパス")
    # --project-name と --issue-number は削除
    parser.add_argument("--prev-article", default="", help="前回の記事スラッグ")
    args = parser.parse_args()

    converter = DiaryConverter(
        model=args.model,
        debug=args.debug,
        template_path=args.template,
        # project_name と issue_number は削除
        prev_article_slug=args.prev_article
    )

    try:
        converter.convert(args.source, args.destination)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
