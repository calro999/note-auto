import os
import json
import requests
import time
from playwright.sync_api import sync_playwright

# --- 設定 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
NOTE_EMAIL = os.environ.get("NOTE_EMAIL")
NOTE_PASSWORD = os.environ.get("NOTE_PASSWORD")
NOTE_COOKIES = os.environ.get("NOTE_COOKIES")
MODEL_NAME = "qwen2.5:3b"
THEMES_FILE = "used_themes.json"

def call_ollama(system_prompt, prompt, timeout=1800, max_tokens=4096):
    """Ollama APIを呼び出してテキストを生成する汎用関数"""
    payload = {
        "model": MODEL_NAME,
        "system": system_prompt,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": max_tokens,
            "temperature": 0.7
        }
    }
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        return result.get("response", "").strip()
    except Exception as e:
        print(f"Ollama APIの呼び出し中にエラーが発生しました: {e}")
        return ""

def get_new_theme():
    """過去のテーマを回避し、新しい恋愛相談テーマを生成する（ステップ0）"""
    print("ステップ0：過去のテーマを回避して新規テーマを生成中...")
    used_themes = []
    if os.path.exists(THEMES_FILE):
        try:
            with open(THEMES_FILE, "r", encoding="utf-8") as f:
                used_themes = json.load(f)
        except Exception:
            pass
            
    system_prompt = "あなたは優秀なコンテンツディレクターです。"
    prompt = f"""
18〜35歳の女性が真剣に悩む、リアルな「恋愛相談のテーマ（お悩み）」を1つだけ提案してください。
ただし、以下の過去のテーマとは【絶対に被らない】ようにしてください。

【過去のテーマリスト】
{json.dumps(used_themes, ensure_ascii=False)}

出力は、テーマの文章1行のみにしてください。
（例：マッチングアプリで3回目のデートに繋がらない時の会話のコツ）
"""
    new_theme = call_ollama(system_prompt, prompt, timeout=300)
    
    if new_theme:
        used_themes.append(new_theme)
        with open(THEMES_FILE, "w", encoding="utf-8") as f:
            json.dump(used_themes, f, ensure_ascii=False, indent=2)
        return new_theme
    else:
        return "自分に自信がない女性が、愛される女性に変わるためのマインドセット"

def generate_outline(theme):
    """構成案（見出し）を作成する（ステップ1）"""
    print("ステップ1：構成案（見出し）を作成中...")
    system_prompt = "あなたは優秀な編集者です。メタ発言は絶対にせず、指定された形式で結果のみを出力してください。"
    prompt = f"""
以下のテーマで有料note（500円）の記事を書きます。
テーマ：「{theme}」

この記事の論理的で魅力的な見出し（H2）を4つ作成してください。
構成は以下の流れにしてください。
1. 読者の痛みの代弁と問題提起（導入）
2. 残酷だけど知るべき心理や真実（分析）
3. 今日からできる具体的なアクションや考え方（実践）
4. まとめと救いの言葉（結論）

以下の形式で出力してください。
見出し1: （テキスト）
見出し2: （テキスト）
見出し3: （テキスト）
見出し4: （テキスト）
"""
    return call_ollama(system_prompt, prompt, timeout=300)

def optimize_title(theme, outline):
    """SEOを意識しつつエッジの効いたタイトルを作成する（ステップ2）"""
    print("ステップ2：タイトルと構成のブラッシュアップ中...")
    system_prompt = "あなたは天才的なWebライターです。メタ発言は一切せず、タイトルのみを出力してください。"
    prompt = f"""
以下のテーマと構成で有料note記事を書きます。

【テーマ】
{theme}
【構成】
{outline}

この記事が思わずクリックしたくなるような、強烈でエッジの効いたタイトルを1つだけ提案してください。
【条件】
- SEOとSNSの拡散を意識し、30〜40文字程度にすること。
- 「〇〇は今すぐ捨てなさい」「〜の残酷な真実」など、読者の常識を覆す煽り文句を入れること。
- 出力はタイトルのテキスト1行のみ。
"""
    title = call_ollama(system_prompt, prompt, timeout=300)
    title = title.replace("タイトル：", "").replace("タイトル:", "").strip('「」"\'')
    return title

def write_section(title, outline, section_name, is_intro=False):
    """見出しごとに記事を執筆する（ステップ3）"""
    print(f"ステップ3：見出し「{section_name}」の執筆中...")
    
    system_prompt = """あなたは、夜の世界のリアルを知るからこそ、傷ついた女性に深く寄り添い、優しくも的確に導いてくれる「頼れるお姉さん（恋愛コンサルタント）」です。

【絶対厳守ルール】
1. メタ発言の禁止：「【上から目線の〜】」「【寄り添い型】」といった指示文や、Markdown記号（** や #）は【絶対に出力しないでください】。
2. ペルソナ：夜の世界で多くの男女を見てきた経験を活かし、毒舌すぎず、説得力と包容力を持った口調（「〜だよね」「〜してみて」「いい？」「〜なのよ」）で話してください。
3. 構成：あなたの夜の世界での実体験や失敗談（架空でOK）を必ず自然な形で交えてください。
"""
    
    intro_instruction = """
あなたは記事の【導入（冒頭）】部分を書いています。
読者の甘い考えや綺麗事を優しくもバッサリと切り捨てる「強烈なフック」から始め、一気に読者の心臓を掴んでください。
見出しのタイトルは書かず、いきなり本文から書き始めてください。
""" if is_intro else f"""
あなたは記事の【{section_name}】という見出しの部分を書いています。
見出しのタイトル（【{section_name}】）を最初に1行書き、その次の行から本文を書いてください。
"""

    prompt = f"""
記事タイトル：{title}
全体構成：
{outline}

上記の情報を踏まえ、以下の指示に従って執筆してください。
{intro_instruction}

文字数は可能な限り長く、詳細に、情景や感情を描写して、1000文字以上の読み応えのある長文にしてください。
"""
    return call_ollama(system_prompt, prompt, timeout=600)

def refine_article(draft):
    """違和感の修正と表現の強化（ステップ4）"""
    print("ステップ4：表現の違和感チェックとトーン統一中...")
    system_prompt = "あなたは優秀な校正者です。メタ発言はせず、修正後の文章のみを出力してください。"
    prompt = f"""
以下の恋愛相談記事のドラフトを校正してください。

【校正ルール】
1. 意味不明な文章、不自然な英単語の混ざり、AI特有の堅苦しい表現（「結論：」「〜について考察します」「こんにちは」）を削除・修正してください。
2. 「【上から目線】」「【夜の世界での生々しいエピソード】」など、プロンプトの指示文がそのまま漏洩している部分があれば完全に削除してください。
3. Markdown記号（** や # や __）はすべて削除し、プレーンテキストにしてください。
4. 全体のトーンを「夜の世界を知る頼れるお姉さん（タメ口、〜だよね、〜なのよ）」に統一してください。

【ドラフト】
{draft}
"""
    if len(draft) > 6000:
        return draft.replace('**', '').replace('__', '')
        
    refined = call_ollama(system_prompt, prompt, timeout=900)
    refined = refined.replace('**', '').replace('__', '').replace('### ', '【').replace('## ', '【').replace('# ', '【')
    return refined

def post_to_note_via_playwright(title, content):
    """Playwrightを使ってnoteに下書き保存する（ステップ5）"""
    if not NOTE_EMAIL or not NOTE_PASSWORD:
        print("エラー: NOTE_EMAIL または NOTE_PASSWORD が設定されていません。")
        return False

    print("ステップ5：noteへの自動入力（下書き保存）プロセスを開始します...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1440, 'height': 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        if NOTE_COOKIES:
            print("Cookieを利用してログイン状態を復元します...")
            try:
                cookies = json.loads(NOTE_COOKIES)
                context.add_cookies(cookies)
                print("Cookieの読み込みに成功しました。")
            except Exception as e:
                print(f"Cookieの形式が不正です: {e}")
        else:
            print("Cookieが設定されていません。EMAIL/PASSWORDでのログインを試みます。")
            
        page = context.new_page()
        
        try:
            if not NOTE_COOKIES:
                page.goto("https://note.com/login", wait_until="load")
                time.sleep(2)
                page.fill('#email', NOTE_EMAIL)
                page.fill('#password', NOTE_PASSWORD)
                login_btn = page.locator('.o-login__button button')
                login_btn.wait_for(state="visible")
                page.wait_for_timeout(1000)
                login_btn.click(force=True)
                try:
                    page.wait_for_url(lambda url: "login" not in url, timeout=10000)
                except Exception:
                    pass 
                time.sleep(3)
                if "login" in page.url:
                    print("エラー: ログイン画面から遷移していません。")
                    return False

            print("記事作成ページへアクセス中...")
            page.goto("https://note.com/intent/post", wait_until="load")
            time.sleep(5)
            
            if "login" in page.url:
                print("エラー: 未ログイン状態と判定されログイン画面にリダイレクトされました。")
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
            
            print("noteのオートセーブ（下書き保存）を待機しています（15秒）...")
            time.sleep(15)
            page.screenshot(path="step5_draft_saved.png", full_page=True)
            print("下書きの保存が完了しました！ブラウザを終了します。")

        except Exception as e:
            print(f"Playwright操作中にエラーが発生しました: {e}")
            try:
                page.screenshot(path="error_screenshot.png", full_page=True)
            except:
                pass
        finally:
            browser.close()

def main():
    print("=== 記事自動生成パイプライン開始 ===")
    
    # ステップ0: テーマ生成
    theme = get_new_theme()
    print(f"決定したテーマ: {theme}\n")
    
    # ステップ1: 構成案作成
    outline = generate_outline(theme)
    print(f"構成案:\n{outline}\n")
    
    # ステップ2: タイトル作成
    title = optimize_title(theme, outline)
    print(f"最適化されたタイトル: {title}\n")
    
    # 見出しの抽出
    sections = []
    for line in outline.split('\n'):
        if line.startswith('見出し'):
            sections.append(line.split(':', 1)[-1].strip())
            
    if not sections:
        sections = ["導入", "心理分析", "具体的なアクション", "まとめ"]
        
    # ステップ3: 見出しごとの個別執筆
    full_draft_parts = []
    for i, section in enumerate(sections):
        is_intro = (i == 0)
        part = write_section(title, outline, section, is_intro)
        full_draft_parts.append(part)
        print(f"--- 見出し {i+1} 完了 ---")
        
    full_draft = "\n\n".join(full_draft_parts)
    
    # ステップ4: 違和感修正
    final_content = refine_article(full_draft)
    print(f"最終文字数: {len(final_content)}文字\n")
    
    # ステップ5: noteへ下書き保存
    post_to_note_via_playwright(title, final_content)
    
    print("=== 全プロセス完了 ===")

if __name__ == "__main__":
    main()
