import os
import json
import random
import requests
import time

# --- 設定 ---
OLLAMA_API_URL = "http://localhost:11434/api/generate"
WEBHOOK_URL = os.environ.get("MAKE_WEBHOOK_URL")
MODEL_NAME = "gemma2:2b" # GitHub Actionsで動く軽量かつ優秀なモデルを想定

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
            "num_predict": 4096, # 生成トークン数の上限を増やす
            "temperature": 0.7
        }
    }

    print(f"[{theme}] の記事を生成中...")
    start_time = time.time()
    
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=300) # 最大5分待ち
        response.raise_for_status()
        result = response.json()
        text = result.get("response", "")
        
        elapsed_time = time.time() - start_time
        print(f"生成完了 (所要時間: {elapsed_time:.1f}秒, 文字数: {len(text)}文字)")
        
        return text
    except Exception as e:
        print(f"記事生成中にエラーが発生しました: {e}")
        return None

def send_to_make(title, content):
    """MakeのWebhookへデータを送信する"""
    if not WEBHOOK_URL:
        print("エラー: MAKE_WEBHOOK_URL が設定されていません。")
        return False
        
    payload = {
        "title": title,
        "content": content
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=payload)
        response.raise_for_status()
        print("Makeへの送信が成功しました！")
        return True
    except Exception as e:
        print(f"Makeへの送信中にエラーが発生しました: {e}")
        return False

def main():
    # テーマをランダムに選択
    theme = random.choice(THEMES)
    
    # 記事を生成
    full_text = generate_article(theme)
    if not full_text:
        return
        
    # 最初の行をタイトル、それ以降を本文として分割
    lines = full_text.strip().split('\n')
    title = lines[0].strip('#').strip() # 見出し記号がついていた場合のために除去
    content = '\n'.join(lines[1:]).strip()
    
    # Webhookへ送信
    send_to_make(title, content)

if __name__ == "__main__":
    main()
