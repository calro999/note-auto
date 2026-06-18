import os
import random
import requests
import time
from playwright.sync_api import sync_playwright

# --- 設定 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
NOTE_EMAIL = os.environ.get("NOTE_EMAIL")
NOTE_PASSWORD = os.environ.get("NOTE_PASSWORD")
MODEL_NAME = "gemma2:2b"

# ランダムなテーマのリスト
THEMES = [
    "出会いがない社会人のための自然な恋の始め方",
    "LINEの返信が遅い彼氏の心理と、焦らないための心の持ち方",
    "「都合のいい女」から本命の彼女に昇格するためのステップ",
    "過去の恋愛のトラウマを乗り越えて、新しい恋に踏み出す方法",
    "職場恋愛で周りにバレずに愛を育むコツと注意点",
    "マッチングアプリで「会ってみたい」と思わせるプロフィールとメッセージ",
    "長続きするカップルとすぐに別れるカップルの決定的な違い",
    "結婚を焦る気持ちとの向き合い方と、自分らしい幸せの見つけ方",
    "遠距離恋愛を成功させるためのコミュニケーションの秘訣",
    "彼の浮気を疑ってしまった時の、正しい対処法と心の整理の仕方",
    "自分に自信がない女性が、愛される女性に変わるためのマインドセット",
    "友達以上恋人未満の関係から一歩踏み出すための勇気の出し方"
]

def generate_article(theme):
    """Ollama APIを使用して記事を生成する"""
    system_prompt = """あなたは、恋愛に悩む18〜35歳の女性に向けた恋愛アドバイザーです。
以下のキャラクター設定を守って記事を書いてください。

【キャラクター設定】
- 実体験を交えつつ、優しく語りかける「少し大人な女性」のトーン。
- 読者に寄り添い、励まし、具体的な解決策を提案する。
- 丁寧な言葉遣い（です・ます調）だが、親しみやすさがある。

【記事の要件】
- 文字数は必ず【最低でも5000文字以上】の長文にすること。非常に詳細に、具体例や自身の体験談（架空で構いません）を豊富に盛り込んでください。
- 見出し（## や ###）を適切に配置し、読みやすい構成にすること。
- 最初の行は記事の「タイトル」とし、見出し記号（#）はつけずにプレーンテキストで書いてください。
- タイトルの次の行から本文を書き始めてください。
"""

    prompt = f"今日の記事のテーマは「{theme}」です。このテーマについて、読者の心に響く、5000文字以上の充実したお悩み解決記事を執筆してください。"

    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": 4096,
            "temperature": 0.7
        }
    }

    print(f"[{theme}] の記事を生成中...")
    start_time = time.time()
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300)
        response.raise_for_status()
        result = response.json()
        text = result.get("response", "")
        
        elapsed_time = time.time() - start_time
        print(f"生成完了 (所要時間: {elapsed_time:.1f}秒, 文字数: {len(text)}文字)")
        
        return text
    except Exception as e:
        print(f"記事生成中にエラーが発生しました: {e}")
        return None

def post_to_note_via_playwright(title, content):
    """Playwrightを使ってnoteにログインし、記事を投稿する"""
    if not NOTE_EMAIL or not NOTE_PASSWORD:
        print("エラー: NOTE_EMAIL または NOTE_PASSWORD が設定されていません。")
        return False

    print("noteへの自動投稿プロセスを開始します...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Bot検知を少しでも回避するための設定
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 1. ログインページへアクセス
            print("ログインページへアクセス中...")
            page.goto("https://note.com/login")
            page.wait_for_load_state("networkidle")
            
            # 2. 認証情報の入力
            print("ログイン情報を入力中...")
            # noteのログインフォームに合わせてセレクタを指定（変更される可能性があります）
            page.fill('input[type="email"], input[name="login"]', NOTE_EMAIL)
            page.fill('input[type="password"], input[name="password"]', NOTE_PASSWORD)
            
            # ログインボタンをクリック
            page.click('button[type="submit"], button:has-text("ログイン")')
            
            # ログイン完了を待機（ダッシュボード等の要素が現れるまで、あるいはURLが変わるまで）
            page.wait_for_load_state("networkidle")
            time.sleep(3) # 念のため待機
            
            # 3. 記事作成ページへアクセス
            print("記事作成ページへアクセス中...")
            page.goto("https://note.com/intent/post")
            page.wait_for_load_state("networkidle")
            time.sleep(2) # エディタの初期化待ち
            
            # 4. タイトルと本文の入力
            print("タイトルと本文を入力中...")
            # タイトルの入力（プレースホルダーやクラス名で要素を探す）
            title_input = page.locator('textarea[placeholder*="タイトル"], .editor-titleInput')
            if title_input.count() > 0:
                title_input.first.fill(title)
            else:
                # 見つからない場合は強制的に最初の入力可能領域にタイプする
                page.keyboard.type(title)
                page.keyboard.press("Enter")
            
            time.sleep(1)
            
            # 本文の入力（ProseMirrorエディタの領域）
            body_input = page.locator('.ProseMirror, [contenteditable="true"]').last
            if body_input.count() > 0:
                body_input.click()
                page.keyboard.insert_text(content)
            else:
                page.keyboard.press("Tab")
                page.keyboard.insert_text(content)
            
            time.sleep(2)
            
            # 5. 公開処理
            print("公開ボタンを押下中...")
            # 「公開設定」ボタン
            publish_settings_btn = page.locator('button:has-text("公開設定")')
            if publish_settings_btn.count() > 0:
                publish_settings_btn.first.click()
                time.sleep(2)
                
                # 「投稿する」ボタン
                submit_btn = page.locator('button:has-text("投稿する"), button:has-text("公開")').last
                submit_btn.click()
                print("noteへの投稿が完了しました！")
                
                # 投稿完了画面が表示されるまで待機
                time.sleep(5)
            else:
                print("公開設定ボタンが見つかりませんでした。下書きとして保存されている可能性があります。")

        except Exception as e:
            print(f"Playwright操作中にエラーが発生しました: {e}")
            # エラー時の状況確認のためにスクリーンショットを保存
            page.screenshot(path="error_screenshot.png")
            print("エラー発生時のスクリーンショットを 'error_screenshot.png' に保存しました。")
        finally:
            browser.close()

def main():
    theme = random.choice(THEMES)
    
    full_text = generate_article(theme)
    if not full_text:
        return
        
    lines = full_text.strip().split('\n')
    title = lines[0].strip('#').strip()
    content = '\n'.join(lines[1:]).strip()
    
    # Playwrightで直接投稿
    post_to_note_via_playwright(title, content)

if __name__ == "__main__":
    main()
