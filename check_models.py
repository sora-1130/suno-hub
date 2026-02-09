import google.generativeai as genai
import streamlit as st
import os

# --- APIキーの取得ロジック ---
# まずは Streamlit の secrets.toml から探す
try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # secrets がない場合は環境変数から探す（ローカル実行用）
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# キーが空の場合の警告
if not GEMINI_API_KEY:
    print("❌ エラー: APIキーが見つかりません。")
    print("secrets.toml に設定するか、一時的に環境変数に入れてください。")
    # 安全のため、ここで入力を求めることも可能
    # GEMINI_API_KEY = input("使用するAPIキーを入力してください（保存はされません）: ")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

    print("✅ 接続成功。あなたのキーで使えるモデル一覧:")
    print("-" * 40)

    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f"可用モデル: {m.name}")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")

    print("-" * 40)