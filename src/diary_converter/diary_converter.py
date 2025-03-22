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

class DiaryConverter:
    """開発日記をZenn公開用の記事に変換するクラス"""

    def __init__(self, model="gemini-2.0-flash-001", template_path="./templates/zenn_template.md", debug=False):
        """初期化"""
        self.model_name = model
        self.template_path = template_path
        self.debug = debug
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

    def read_template(self):
        """テンプレートファイルを読み込む"""
        try:
            # 相対パスを解決
            if not os.path.isabs(self.template_path):
                # スクリプトの実行ディレクトリからの相対パス
                script_dir = os.path.dirname(os.path.abspath(__file__))
                template_path = os.path.join(script_dir, self.template_path)
            else:
                template_path = self.template_path

            # テンプレートファイルの存在確認
            if not os.path.exists(template_path):
                if self.debug:
                    print(f"テンプレートファイル '{template_path}' が見つかりません")
                    print(f"カレントディレクトリ: {os.getcwd()}")
                    print(f"スクリプトディレクトリ: {os.path.dirname(os.path.abspath(__file__))}")
                raise FileNotFoundError(f"テンプレートファイル '{template_path}' が見つかりません")

            with open(template_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return content
        except Exception as e:
            raise IOError(f"テンプレートファイル読み込み中にエラーが発生しました: {e}")

    def extract_date_from_filename(self, file_path):
        """ファイル名から日付を抽出する"""
        filename = os.path.basename(file_path)
        date_match = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
        if date_match:
            return date_match.group(1)
        return datetime.now().strftime("%Y-%m-%d")

    def extract_theme_from_filename(self, file_path):
        """ファイル名からテーマを抽出する"""
        filename = os.path.basename(file_path)
        # 日付部分を除去
        theme_part = re.sub(r'\d{4}-\d{2}-\d{2}-', '', filename)
        # 拡張子を除去
        theme = os.path.splitext(theme_part)[0]
        return theme

    def generate_prompt(self, content, date, theme, cycle_article_link="", template_content=None):
        """Gemini APIに送信するプロンプトを生成する"""
        if not template_content:
            raise ValueError("テンプレート内容が提供されていません")

        # テンプレートからfrontmatterを抽出
        try:
            post = frontmatter.loads(template_content)
            template_fm = post.metadata

            if not template_fm:
                if self.debug:
                    print("警告: テンプレートからfrontmatterを抽出できませんでした。デフォルト値を使用します。")
                template_fm = {
                    "title": f"{date} [テーマ名]",
                    "emoji": "📝",
                    "type": "tech",
                    "topics": ["開発日記", "プログラミング"],
                    "published": False
                }
            elif self.debug:
                print(f"テンプレートからfrontmatterを抽出しました: {template_fm}")
        except Exception as e:
            if self.debug:
                print(f"警告: テンプレートからfrontmatterを抽出できませんでした: {e}")
            template_fm = {
                "title": f"{date} [テーマ名]",
                "emoji": "📝",
                "type": "tech",
                "topics": ["開発日記", "プログラミング"],
                "published": False
            }

        # テンプレートの記述ガイドラインを抽出
        guidelines_match = re.search(r'## 記述ガイドライン.*', template_content, re.DOTALL)
        guidelines = guidelines_match.group(0) if guidelines_match else ""

        # テンプレートの構造を抽出（frontmatterとガイドライン部分を除く）
        template_structure = template_content
        if guidelines_match:
            template_structure = template_content.split(guidelines_match.group(0))[0]

        # frontmatterを除去
        template_structure = re.sub(r'^---\n.*?\n---\n', '', template_structure, flags=re.DOTALL)

        # LLMモデル名と開発サイクル紹介記事のリンクを設定
        llm_model_info = f"この記事は{self.model_name}によって自動生成されています。"
        cycle_article_info = ""
        if cycle_article_link:
            cycle_article_info = f"私の毎日の開発サイクルについては、{cycle_article_link}をご覧ください。"

        # テーマ名を設定
        theme_name = theme.replace("-", " ").title()

        # frontmatterテンプレート
        frontmatter_template = f"""---
title: "{date} {theme_name}"
emoji: "{template_fm.get('emoji', '📝')}"
type: "{template_fm.get('type', 'tech')}"
topics: {template_fm.get('topics', ['開発日記', 'プログラミング'])}
published: {str(template_fm.get('published', False)).lower()}
---"""

        # メッセージボックステンプレート
        message_box_template = f""":::message
{llm_model_info}
{cycle_article_info}
:::"""

        prompt = f"""以下の開発日記を、Zenn公開用の記事に変換してください。

# 入力された開発日記
{content}

# 変換ルール
1. 「会話ログ」セクションは、対話形式ではなく、ストーリー形式に書き直してください
2. 技術的な内容は保持しつつ、読みやすく整理してください
3. 「所感」セクションを充実させ、開発者の視点や感想を追加してください
4. マークダウン形式を維持し、コードブロックなどは適切に整形してください
5. 記事の先頭に以下のfrontmatterを追加してください：

{frontmatter_template}

6. frontmatterの直後に以下のメッセージボックスを追加してください：

{message_box_template}

# テンプレート構造
以下のテンプレート構造に従って記事を作成してください。各セクションの目的と内容を理解し、開発日記の内容に合わせて適切に変換してください：

{template_structure}

# 記述ガイドライン
{guidelines}

# 出力形式
frontmatterを含むマークダウン形式の完全な記事を出力してください。テンプレートの構造に従いつつ、開発日記の内容を適切に反映させてください。
以下の点に注意してください：
1. コードブロックは必要な場合のみ使用し、記事全体をコードブロックで囲まないでください
2. 記事の先頭や末尾に余分なコードブロックマーカー（```）を付けないでください
3. 記事の先頭に```markdownなどの言語指定を付けないでください
"""
        return prompt

    def convert_with_gemini(self, content, date, theme, cycle_article_link="", template_content=None):
        """Gemini APIを使用して開発日記を変換する"""
        prompt = self.generate_prompt(content, date, theme, cycle_article_link, template_content)

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

    def convert(self, source_file, destination_file, cycle_article_link=""):
        """開発日記をZenn記事に変換する"""
        try:
            # 入力ファイルを読み込む
            content = self.read_source_diary(source_file)

            # テンプレートを読み込む
            template_content = self.read_template()

            # ファイル名から日付とテーマを抽出
            date = self.extract_date_from_filename(source_file)
            theme = self.extract_theme_from_filename(source_file)

            # Gemini APIで変換
            converted_content = self.convert_with_gemini(
                content, date, theme, cycle_article_link, template_content
            )

            # 変換結果を保存
            self.save_converted_article(converted_content, destination_file)

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
    parser.add_argument("--cycle-article", default="", help="開発サイクルの紹介記事へのリンク")
    args = parser.parse_args()

    try:
        converter = DiaryConverter(
            model=args.model,
            template_path=args.template,
            debug=args.debug
        )
        converter.convert(args.source, args.destination, args.cycle_article)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
