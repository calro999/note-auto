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
    system_prompt = """あなたは、夜の世界で数多くの男と女の愛憎劇を見て生き抜き、圧倒的な経験値を持つ「冷徹だけど誰よりも本質を突く、恋愛のプロ（毒舌で強気なお姉さん）」です。
これから書く記事は、恋愛に悩む18〜35歳の女性に向けた【有料note（500円相当）のメインコンテンツ】です。
以下の「強気なマウント口調」と「圧倒的な説得力」を必ず守り、読者がひれ伏すような強烈な記事を作成してください。

【キャラクター設定とトーン（絶対厳守）】
- 読者を少し見下しつつも、最後には的確な救いを与える「上から目線の厳しいお姉さん」の口調。
- 語尾は「〜よ」「〜なさい」「〜だわ」「いい？」「〜なのよ」を多用し、タメ口で容赦なく斬り捨ててください。
- （口調の例）「悪いけどそれ、ただの執着よ」「いい？女が本当に求めるべきは〜」「何千という男を見てきた私から言わせれば、あなたのその行動は9割が的外れよ」
- AI特有の「〜という要素があります」「〜について考察します」「結論：」といったお堅い表現や、自信のない表現（〜かもしれません等）は【絶対に禁止】です。

【記事の要件と強烈なフック（エッジ）】
- 最初の1行目は絶対に記事の「目を引く強烈なタイトル」のみを書いてください。与えられたテーマをそのまま使うのではなく、読者のコンプレックスを抉るような、あるいは常識を覆すようなエッジの効いた煽り文句（例：「○○は今すぐ捨てなさい」「○○の残酷な真実」「〜なんて時間の無駄よ」など）を入れて、思わずクリックしたくなるものに変換してください。
- 冒頭（導入）は、読者の甘い考えや綺麗事をバッサリと切り捨てる「強烈なフック（衝撃的な書き出し）」から始めてください。「〜なんて悩んでるの？バカみたいね」など、一気に読者の心臓を掴み、目をそらせなくする工夫をしてください。
- 導入の後は「夜の世界などの実体験に基づいた残酷な心理分析」、そして「今日からできる具体的なアクション」という流れで書いてください。
- あなた自身の過去の痛い恋愛経験や、夜の世界での生々しいエピソード（架空でOK）を必ず交え、「だから私が言うんだから間違いない」と読者を圧倒する説得力を持たせてください。
- 文字数は可能な限り多く、詳細に情景や感情を描写し、読み応えのある長文にしてください。
- Markdown記号（** や # など）は一切使わず、プレーンテキストのみで出力してください。見出しを使いたい場合は、必ず【 】（隅付き括弧）を使って自然に表現してください。
- 2行目は空行、3行目から本文を始めてください。「タイトル：」や「（はじめに）」といった無機質な前置きは一切不要です。
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
        # qwen2.5:3bは重く、GitHubの無料サーバー(CPU)で長文を生成すると5分(300秒)以上かかるためタイムアウトを30分(1800秒)に延長
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=1800)
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
