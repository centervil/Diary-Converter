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

    def __init__(self, model="gemini-2.0-flash-001", template_path="./templates/zenn_template.md", 
                 debug=False, project_name=None, issue_number=None, prev_article_slug=None):
        """初期化"""
        self.model_name = model
        self.template_path = template_path
        self.debug = debug
        self.project_name = project_name  # プロジェクト名
        self.issue_number = issue_number  # 連番（Issue番号）
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

    def extract_template_sections(self, template_content):
        """テンプレートから各セクションを抽出する"""
        # frontmatterを抽出
        try:
            post = frontmatter.loads(template_content)
            template_fm = post.metadata
            if not template_fm and self.debug:
                print("警告: テンプレートからfrontmatterを抽出できませんでした。デフォルト値を使用します。")
        except Exception as e:
            if self.debug:
                print(f"警告: テンプレートからfrontmatterを抽出できませんでした: {e}")
            template_fm = {}

        # デフォルト値を設定
        if not template_fm:
            template_fm = {
                "title": "[プロジェクト名] 開発日記 #[連番]: [テーマ名]",
                "emoji": "📝",
                "type": "tech",
                "topics": ["開発日記", "プログラミング"],
                "published": False
            }

        # メッセージボックスを抽出
        message_box_match = re.search(r':::message\n(.*?)\n:::', template_content, re.DOTALL)
        message_box = message_box_match.group(0) if message_box_match else ""
        
        # 関連リンクセクションを抽出
        related_links_match = re.search(r'## 関連リンク\n\n(.*?)(?=\n\n#|\n\n---|\Z)', template_content, re.DOTALL)
        related_links = related_links_match.group(0) if related_links_match else ""
        
        # 記述ガイドラインを抽出
        guidelines_match = re.search(r'## 記述ガイドライン.*', template_content, re.DOTALL)
        guidelines = guidelines_match.group(0) if guidelines_match else ""
        
        # 変換プロセスを抽出
        conversion_process_match = re.search(r'## 開発日記からの変換プロセス.*', template_content, re.DOTALL)
        conversion_process = conversion_process_match.group(0) if conversion_process_match else ""
        
        # テンプレート構造（メインコンテンツ部分）を抽出
        # frontmatter、メッセージボックス、関連リンク、ガイドライン、変換プロセスを除く
        template_structure = template_content
        
        # frontmatterを除去
        template_structure = re.sub(r'^---\n.*?\n---\n', '', template_structure, flags=re.DOTALL)
        
        # メッセージボックスを除去（あれば）
        if message_box:
            template_structure = template_structure.replace(message_box, "")
        
        # 関連リンクセクションを除去（あれば）
        if related_links:
            template_structure = template_structure.replace(related_links, "")
        
        # ガイドラインと変換プロセスを除去
        if guidelines:
            template_structure = template_structure.split(guidelines)[0]
        elif conversion_process:
            template_structure = template_structure.split(conversion_process)[0]
        
        # 余分な空行を整理
        template_structure = re.sub(r'\n{3,}', '\n\n', template_structure.strip())
        
        return {
            "frontmatter": template_fm,
            "message_box": message_box,
            "related_links": related_links,
            "guidelines": guidelines,
            "conversion_process": conversion_process,
            "template_structure": template_structure
        }

    def generate_prompt(self, content, date, theme, cycle_article_link="", template_content=None):
        """Gemini APIに送信するプロンプトを生成する"""
        if not template_content:
            raise ValueError("テンプレート内容が提供されていません")

        # テンプレートから各セクションを抽出
        template_sections = self.extract_template_sections(template_content)
        template_fm = template_sections["frontmatter"]
        guidelines = template_sections["guidelines"]
        template_structure = template_sections["template_structure"]
        
        # テーマ名を設定
        theme_name = theme.replace("-", " ").title()
        
        # プロジェクト名とIssue番号を設定
        project_name = self.project_name or "プロジェクト"
        issue_number = self.issue_number or "1"
        
        # frontmatterテンプレート
        # テンプレートのfrontmatterを基に、動的な値を置換
        title_template = template_fm.get("title", "[プロジェクト名] 開発日記 #[連番]: [テーマ名]")
        title = title_template.replace("[プロジェクト名]", project_name) \
                             .replace("[連番]", issue_number) \
                             .replace("[テーマ名]", theme_name)
        
        frontmatter_template = f"""---
title: "{title}"
emoji: "{template_fm.get('emoji', '📝')}"
type: "{template_fm.get('type', 'tech')}"
topics: {template_fm.get('topics', ['開発日記', 'プログラミング'])}
published: {str(template_fm.get('published', False)).lower()}
---"""

        # LLMモデル名と開発サイクル紹介記事のリンクを設定
        llm_model_info = f"この記事は{self.model_name}によって自動生成されています。"
        cycle_article_info = ""
        if cycle_article_link:
            cycle_article_info = f"私の毎日の開発サイクルについては、{cycle_article_link}をご覧ください。"

        # メッセージボックステンプレート
        # テンプレートのメッセージボックスがあれば使用し、なければ新規作成
        if template_sections["message_box"]:
            message_box_template = template_sections["message_box"] \
                .replace("[LLM Model名]", self.model_name)
            
            # 開発サイクル記事リンクの置換
            if cycle_article_link:
                message_box_template = re.sub(
                    r'\[LLM対話で実現する継続的な開発プロセス\]\(.*?\)', 
                    f'[LLM対話で実現する継続的な開発プロセス]({cycle_article_link})', 
                    message_box_template
                )
        else:
            message_box_template = f""":::message
{llm_model_info}
{cycle_article_info}
:::"""

        # 関連リンクセクションテンプレート
        # テンプレートの関連リンクセクションがあれば使用し、なければ新規作成
        if template_sections["related_links"]:
            repo_name = self.project_name or "[リポジトリ名]"
            repo_link = f"https://github.com/centervil/{repo_name}"
            prev_article_link = f"https://zenn.dev/centervil/articles/{self.prev_article_slug}" if self.prev_article_slug else "https://zenn.dev/centervil/articles/[前回の記事スラッグ]"
            
            related_links_section = template_sections["related_links"] \
                .replace("[プロジェクト名]", project_name) \
                .replace("[リポジトリ名]", repo_name) \
                .replace("https://github.com/centervil/[リポジトリ名]", repo_link)
            
            # 前回の記事リンクの置換
            if self.prev_article_slug:
                related_links_section = re.sub(
                    r'https://zenn.dev/centervil/articles/\[前回の記事スラッグ\]', 
                    prev_article_link, 
                    related_links_section
                )
        else:
            repo_name = self.project_name or "[リポジトリ名]"
            repo_link = f"https://github.com/centervil/{repo_name}"
            prev_article_link = f"https://zenn.dev/centervil/articles/{self.prev_article_slug}" if self.prev_article_slug else "https://zenn.dev/centervil/articles/[前回の記事スラッグ]"
            prev_title = "前回のタイトル"
            
            related_links_section = f"""## 関連リンク

- **プロジェクトリポジトリ**: [{project_name}]({repo_link})
- **前回の開発日記**: [{prev_title}]({prev_article_link})
"""

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

7. メッセージボックスの直後に以下の関連リンクセクションを追加してください：

{related_links_section}

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
    parser.add_argument("--project-name", default="", help="プロジェクト名")
    parser.add_argument("--issue-number", default="", help="連番（Issue番号）")
    parser.add_argument("--prev-article", default="", help="前回の記事スラッグ")
    args = parser.parse_args()

    try:
        converter = DiaryConverter(
            model=args.model,
            template_path=args.template,
            debug=args.debug,
            project_name=args.project_name,
            issue_number=args.issue_number,
            prev_article_slug=args.prev_article
        )
        converter.convert(args.source, args.destination, args.cycle_article)
    except Exception as e:
        print(f"エラー: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
