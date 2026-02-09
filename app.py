import streamlit as st
import google.generativeai as genai
import streamlit.components.v1 as components
import json
import re
import os

# ==========================================
# 1. 設定 & Geminiモデル準備
# ==========================================
st.set_page_config(page_title="J-Suno Tool V14", page_icon="🎵", layout="wide")

# ---------------------------------------------------------
# ★修正ポイント：APIキーの読み込み処理 (安全版)
# ---------------------------------------------------------
try:
    # Streamlit Cloudの「Secrets」からキーを取得
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
except:
    # ローカルなどSecretsがない場合。
    # ★重要：ここには絶対に本物のキーを書かないでください！（GitHubでバレます）
    GEMINI_API_KEY = "KEY_NOT_SET"

# キーが設定されていない場合の安全策
if GEMINI_API_KEY == "KEY_NOT_SET":
    # 警告は出しますが、アプリ自体は落ちないようにします
    pass 

try:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash') 
except Exception as e:
    st.error(f"API設定エラー: {e}")

# 画面の横スクロールを防止するCSS
st.markdown("""
    <style>
    .stApp {
        overflow-x: hidden;
    }
    iframe {
        width: 100% !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. 関数定義 (AI & コピーボタン)
# ==========================================

def custom_copy_button(text, unique_key):
    # JavaScript用にエスケープ処理
    escaped_text = text.replace("\n", "\\n").replace("'", "\\'").replace('"', '\\"')
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        body {{
            margin: 0; padding: 0; width: 100%; display: flex; justify-content: center;
        }}
        .copy-btn {{
            background-color: #ffffff; color: #333333; border: 1px solid #cccccc;
            border-radius: 5px; padding: 6px 12px; font-family: sans-serif;
            font-size: 14px; font-weight: bold; cursor: pointer; display: flex;
            align-items: center; justify-content: center; gap: 8px; 
            transition: all 0.2s ease; width: 98%; margin-top: 5px; box-sizing: border-box;
        }}
        .copy-btn:hover {{ background-color: #f0f0f0; border-color: #999999; }}
        .copy-btn:active {{ transform: translateY(1px); }}
        @media (max-width: 640px) {{
            .copy-btn {{ font-size: 16px; padding: 10px; }}
        }}
    </style>
    </head>
    <body>
        <button id="btn_{unique_key}" class="copy-btn" onclick="copyToClipboard()">
            <span>📄</span> Copy to Clipboard
        </button>
        <script>
        function copyToClipboard() {{
            const text = "{escaped_text}";
            const btn = document.getElementById("btn_{unique_key}");
            navigator.clipboard.writeText(text).then(function() {{
                btn.innerHTML = "✅ Copied!";
                btn.style.backgroundColor = "#e6fffa"; btn.style.borderColor = "#38a169";
                setTimeout(function() {{
                    btn.innerHTML = '<span>📄</span> Copy to Clipboard';
                    btn.style.backgroundColor = "#ffffff"; btn.style.borderColor = "#cccccc";
                }}, 3000);
            }});
        }}
        </script>
    </body>
    </html>
    """
    components.html(html_code, height=50)

def generate_suno_pack(user_prompt):
    prompt = f"""
    あなたはSuno AIのエキスパートです。
    ユーザーの要望: {user_prompt}
    
    以下のJSON形式で出力してください。
    1. style: Sunoの"Style of Music"タグ（英語）。
    2. title: 曲のタイトル。
    3. lyrics: 構造タグ付きフルコーラス歌詞。

    出力フォーマット:
    {{
        "style": "Genre, Vibe, Instruments",
        "title": "Title Name",
        "lyrics": "[Intro]\\n..."
    }}
    """
    try:
        response = model.generate_content(prompt)
        match = re.search(r'\{.*\}', response.text, re.DOTALL)
        if match: return json.loads(match.group(0))
    except: return None

def rewrite_lyrics(current_lyrics, instruction):
    prompt = f"""
    あなたは歌詞編集マシンです。感情を持たず、結果だけを出力してください。
    会話文禁止。出力は修正後の歌詞だけにすること。
    元歌詞: {current_lyrics}
    修正指示: {instruction}
    """
    response = model.generate_content(prompt)
    return response.text.strip()

# ==========================================
# 3. 画面構築 (UI)
# ==========================================
st.title("🎵 J-Suno Tool")
st.caption("AI Music Prompt Generator & Studio")

st.markdown("""
**「Suno AIで、もっと自由に曲を作ろう。」** このアプリは、あなたの頭の中にある「曲のイメージ」を、Suno AIが理解できる**「英語のタグ」「タイトル」「構成付きの歌詞」**に一瞬で変換する魔法のツールです。
""")

st.write("") 

tab_create, tab_edit = st.tabs(["📝 レシピを作る", "🚀 今後のアップデート"])

# --- タブ1: 生成画面 ---
with tab_create:
    st.markdown("### 1. イメージ入力")
    
    # ⚡ クイック入力ボタン（個別のキーワードを設定）
    st.caption("⚡ 人気のスタイルを試す")
    q_cols = st.columns(4)
    
    # ジャンルごとの個別設定
    presets = {
        "アニソン": "勇気が湧く、明るい王道アニソン。サビで盛り上がる構成。",
        "ボカロ": "切ないメロディのボカロポップ。ピアノと電子音が特徴的。",
        "シティポップ": "夜のドライブに合う、おしゃれで都会的なシティポップ。",
        "J-ROCK": "魂を揺さぶる、激しいギターリフのJ-ROCK。"
    }
    
    if "input_text" not in st.session_state:
        st.session_state.input_text = ""

    # ボタンをクリックした時の動作
    for i, (style, description) in enumerate(presets.items()):
        if q_cols[i].button(style, use_container_width=True, key=f"btn_{style}"):
            st.session_state.input_text = description
            st.rerun()

    col_in1, col_in2 = st.columns([4, 1])
    with col_in1:
        user_input = st.text_area(
            "どんな曲を作りたい？", 
            value=st.session_state.input_text,
            placeholder="例：夜のドライブに合う、おしゃれなLo-fi HipHop",
            height=80, 
            label_visibility="collapsed",
            key="main_input_area"
        )
    with col_in2:
        if st.button("🚀 生成", type="primary", use_container_width=True, key="btn_generate_main"):
            if GEMINI_API_KEY == "KEY_NOT_SET":
                st.error("⚠️ APIキーを設定してください！")
            else:
                with st.spinner("AIプロデューサーが思考中..."):
                    data = generate_suno_pack(user_input)
                    if data:
                        st.session_state.generated_data = data
                    else:
                        st.error("生成に失敗しました。")

    st.divider()

    # 2. 確認 & コピー セクション
    if "generated_data" in st.session_state and st.session_state.generated_data:
        data = st.session_state.generated_data
        st.markdown("### 2. 確認 & コピー")
        
        # --- Suno.comへの直通ボタン（エラー回避のためkeyを削除） ---
        st.link_button(
            "🔥 Suno.com を開いて作成を開始する", 
            "https://suno.com", 
            type="secondary", 
            use_container_width=True
        )
        st.info("💡 ジャンル・タイトル・歌詞をコピーしてから、上のボタンでSunoを開いてください。（タイトルはつけなくても作成することができます。）")
        st.write("") 

        c1, c2 = st.columns(2)
        with c1:
            st.caption("🎹 Style (ジャンル)")
            new_style = st.text_area("Style", value=data.get('style', ''), height=80, key="style_input", label_visibility="collapsed")
            st.session_state.generated_data['style'] = new_style
            custom_copy_button(new_style, "style_btn")

        with c2:
            st.caption("🏷️ Title (タイトル)")
            new_title = st.text_area("Title", value=data.get('title', ''), height=80, key="title_input", label_visibility="collapsed")
            st.session_state.generated_data['title'] = new_title
            custom_copy_button(new_title, "title_btn")

        st.write("") 
        
        # 歌詞エリア
        l_col, r_col = st.columns([3, 2])
        with l_col:
            st.caption("🎤 Lyrics (歌詞)")
            new_lyrics = st.text_area("Lyrics", value=data.get('lyrics', ''), height=500, key="lyrics_input", label_visibility="collapsed")
            st.session_state.generated_data['lyrics'] = new_lyrics
            custom_copy_button(new_lyrics, "lyrics_btn")

        with r_col:
            st.caption("🤖 AI修正")
            st.info("歌詞の一部を変えたいときはここに指示してください。")
            rewrite_inst = st.text_area("修正指示", height=150, placeholder="例：サビをもっと情熱的にして", label_visibility="collapsed", key="ai_rewrite_input")
            
            if st.button("書き換え実行", type="primary", use_container_width=True, key="btn_rewrite_execute"):
                if GEMINI_API_KEY == "KEY_NOT_SET":
                    st.error("⚠️ APIキーが設定されていません。")
                else:
                    with st.spinner("修正中..."):
                        rewritten = rewrite_lyrics(new_lyrics, rewrite_inst)
                        st.session_state.generated_data['lyrics'] = rewritten
                        st.rerun()

# --- タブ2: 予告ページ ---
with tab_edit:
    st.header("🚧 AI Audio Studio (Coming Soon)")
    st.info("最強の編集機能を実装予定です。")
    st.markdown("""
    ### 📅 実装予定の機能
    * **Stem Separation** (ボーカル抽出)
    * **Key & Tempo Change** (キー変更)
    * **Audio Mastering** (音圧アップ)
    
    次回の大型アップデートをお待ちください！
    """)
    
    st.image("https://media.giphy.com/media/aw61sTqyJ9aHm/giphy.gif", use_column_width=True, caption="Development in progress...")