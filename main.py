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

【キャラクター設定・語り口】
- 読者にとって「頼れる年上のお姉さん」の立ち位置。威厳を保ちつつも、少しラフで親しみやすい口調（「〜だよね」「〜してみて！」「〜だと思うな」など、タメ口や親身な表現を交えた話し方）。
- AI特有の「〜するのがいいかもしれません」「〜という側面もあります」「〜と言えるでしょう」といった回りくどい表現や、自信のない曖昧な表現は【絶対に】使わないこと。ズバッと断定し、頼りがいのあるアドバイスをしてください。
- 実体験（架空でOK）を交えつつ、具体的な解決策を提案してください。

【記事の要件】
- 文字数は必ず【最低でも5000文字以上】の長文にすること。非常に詳細に語ってください。
- noteのエディタに直接テキストを入力するため、Markdown形式（**太字** や # 見出し など）は【一切使用禁止】です。強調したい場所は「」を使ったり、見出しは【 】（隅付き括弧）を使うなど、プレーンテキストのみで読みやすい構成にしてください。
- 最初の行は記事の「タイトル」として1行だけで書き、次の行から本文を書き始めてください。
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
            
            time.sleep(3)
            page.screenshot(path="step3_after_typing.png", full_page=True)
            
            print("公開ボタンを押下中...")
            # ページをスクロールしながら公開ボタンを探す
            page.evaluate("window.scrollTo(0, 0)")
            time.sleep(1)
            
            btn_found = False
            for _ in range(15): # 最大15回スクロールしながら探す
                # 多様なボタン名に対応
                publish_settings_btn = page.locator('text="公開に進む", text="公開設定", text="公開する", text="公開", text="投稿する"').locator('visible=true').first
                
                if publish_settings_btn.count() > 0:
                    publish_settings_btn.click(force=True)
                    btn_found = True
                    print("最初の公開ボタンを発見してクリックしました！")
                    break
                
                # 見つからなければ下にスクロール
                page.mouse.wheel(0, 800)
                time.sleep(1)
            
            if btn_found:
                time.sleep(3)
                page.screenshot(path="step4_publish_settings.png", full_page=True)
                
                # パネルの中の最終確認ボタン
                submit_btn = page.locator('button:has-text("投稿する"), button:has-text("公開"), text="今すぐ投稿"').locator('visible=true').last
                if submit_btn.count() > 0:
                    submit_btn.click(force=True)
                    print("noteへの投稿完了ボタンを押しました！")
                else:
                    print("最終確認の投稿ボタンが見つかりませんでした。")
                
                time.sleep(5)
                page.screenshot(path="step5_after_publish.png", full_page=True)
            else:
                print("最初の公開ボタンが見つかりませんでした。画面の状態を確認してください。")
                # ボタンが見つからず失敗した場合でも、noteの下書き自動保存が走るように10秒待機する
                print("下書き保存のため10秒待機します...")
                time.sleep(10)

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
