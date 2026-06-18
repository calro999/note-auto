import os
import random
import requests
import time
import json
from playwright.sync_api import sync_playwright

# --- 設定 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
NOTE_EMAIL = os.environ.get("NOTE_EMAIL")
NOTE_PASSWORD = os.environ.get("NOTE_PASSWORD")
NOTE_COOKIES = os.environ.get("NOTE_COOKIES")
MODEL_NAME = "qwen2.5:3b"

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
    system_prompt = """あなたは、恋愛心理学に精通し、自身も数々の恋愛経験と失敗を乗り越えてきた「プロの恋愛コンサルタント（年上のお姉さん）」です。
これから書く記事は、読者が「お金を払ってでも読みたい」と感動し、深く共感する【有料note（500円相当）のメインコンテンツ】として販売されます。
以下の点に全力を注いで、圧倒的に高品質で血の通った記事を作成してください。

【キャラクター設定とトーン】
- 読者に寄り添い、優しくも時に厳しく本質を突く「頼れる年上のお姉さん」の口調。「〜だよね」「〜してみてほしいな」「実は私も昔…」など、人間味のある自然なタメ口や親しみやすい表現を使ってください。
- AIが書いたとバレる表現（「〜という要素があります」「〜について考察します」「結論：」「【具体的なアドバイス】」などのお堅い表現やテンプレ表現）は【絶対に禁止】です。まるでカフェで親友が真剣にアドバイスしてくれているような、感情の乗った文章にしてください。

【記事の要件】
- 読者の心を揺さぶる「リアルな共感（読者の痛みの代弁）」から始め、次に「具体的な心理分析」、そして「明日から実践できるマインドセットや行動」という流れで深く語ってください。
- あなた自身の過去の痛い恋愛経験や失敗談（架空でOK）を赤裸々に語り、そこから得た教訓を必ず交えてください。読者はあなたの実体験に一番価値を感じます。
- 文字数は可能な限り多く、詳細に情景や感情を描写し、読み応えのある長文にしてください。
- Markdown記号（** や # など）は一切使わず、プレーンテキストのみで出力してください。見出しを使いたい場合は、必ず【 】（隅付き括弧）を使って自然に表現してください。
- 最初の1行目は絶対に記事の「魅力的なタイトル」のみを書き、2行目は空行、3行目から本文を始めてください。「タイトル：」や「（はじめに）」といった無機質な前置きは一切不要です。
"""

    prompt = f"今日の記事のテーマは「{theme}」です。このテーマについて、有料noteとして販売できるレベルの、読者の心に深く刺さる圧倒的なお悩み解決記事をプレーンテキストで執筆してください。"

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
        
        # Markdown記号を強制的に除去（AIが指示を無視した場合の保険）
        text = text.replace('**', '').replace('__', '')
        # #見出しを隅付き括弧に変換
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            if line.startswith('### '):
                line = f"【{line.replace('### ', '').strip()}】"
            elif line.startswith('## '):
                line = f"【{line.replace('## ', '').strip()}】"
            elif line.startswith('# '):
                line = f"【{line.replace('# ', '').strip()}】"
            cleaned_lines.append(line)
        text = '\n'.join(cleaned_lines)
        
        elapsed_time = time.time() - start_time
        print(f"生成完了 (所要時間: {elapsed_time:.1f}秒, 文字数: {len(text)}文字)")
        
        return text
    except Exception as e:
        print(f"記事生成中にエラーが発生しました: {e}")
        return None

def post_to_note_via_playwright(title, content):
    """Playwrightを使ってnoteにログインし、記事を投稿する"""
    print("noteへの自動投稿プロセスを開始します...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900}, # PC版の広い画面サイズを強制
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Cookieを利用したログイン回避
        if NOTE_COOKIES:
            print("Cookieを利用してログイン状態を復元します...")
            try:
                cookies = json.loads(NOTE_COOKIES)
                context.add_cookies(cookies)
                print("Cookieの読み込みに成功しました。")
            except Exception as e:
                print(f"Cookieの形式が不正です: {e}")
        elif not NOTE_EMAIL or not NOTE_PASSWORD:
            print("エラー: ログイン情報（Cookie または EMAIL/PASSWORD）が設定されていません。")
            return False

        page = context.new_page()
        
        try:
            if not NOTE_COOKIES:
                print("ログインページへアクセス中...")
                page.goto("https://note.com/login", wait_until="load")
                time.sleep(2)
                
                print("ログイン情報を入力中...")
                page.fill('#email', NOTE_EMAIL)
                page.fill('#password', NOTE_PASSWORD)
                
                login_btn = page.locator('.o-login__button button')
                login_btn.wait_for(state="visible")
                page.wait_for_timeout(1000)
                login_btn.click(force=True)
                
                print("ログイン完了を待機中...")
                try:
                    page.wait_for_url(lambda url: "login" not in url, timeout=10000)
                except Exception:
                    pass 
                    
                time.sleep(3)
                page.screenshot(path="step1_after_login.png", full_page=True)
                
                if "login" in page.url:
                    print("エラー: ログイン画面から遷移していません。認証失敗かBot検知の可能性があります。")
                    return False

            print("記事作成ページへアクセス中...")
            page.goto("https://note.com/intent/post", wait_until="load")
            time.sleep(5)
            page.screenshot(path="step2_editor_loaded.png", full_page=True)
            
            # 未ログイン状態でリダイレクトされていないかチェック
            if "login" in page.url:
                print("エラー: 未ログイン状態と判定されログイン画面にリダイレクトされました。Cookieが期限切れか不正です。")
                return False

            print("タイトルと本文を入力中...")
            title_input = page.locator('textarea[placeholder*="タイトル"], .editor-titleInput')
            if title_input.count() > 0:
                title_input.first.fill(title)
            else:
                page.keyboard.type(title)
                page.keyboard.press("Enter")
            
            time.sleep(1)
            
            body_input = page.locator('.ProseMirror, [contenteditable="true"]').last
            if body_input.count() > 0:
                body_input.click()
                page.keyboard.insert_text(content)
            else:
                page.keyboard.press("Tab")
                page.keyboard.insert_text(content)
            
            print("記事の入力が完了しました。")
            
            # noteの自動保存（下書き保存）が確実に走るように長めに待機
            print("noteのオートセーブ（下書き保存）を待機しています（15秒）...")
            time.sleep(15)
            page.screenshot(path="step4_draft_saved.png", full_page=True)
            print("下書きの保存が完了しました！ブラウザを終了します。")

        except Exception as e:
            print(f"Playwright操作中にエラーが発生しました: {e}")
            try:
                page.screenshot(path="error_screenshot.png", full_page=True)
                print("エラー発生時のスクリーンショットを保存しました。")
            except Exception as ss_e:
                print(f"スクリーンショットの保存にも失敗しました: {ss_e}")
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
