import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="政治MBTI診断", page_icon="🗳️", layout="centered")

# カスタムCSS（デザインを整える）
st.markdown("""
<style>
    .question-box {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 25px;
        border-left: 5px solid #4CAF50;
    }
    .result-type {
        font-size: 3.5rem;
        font-weight: 900;
        color: #FF5722;
        text-align: center;
        margin: 20px 0;
        letter-spacing: 0.1em;
    }
    .axis-title {
        font-weight: bold;
        font-size: 1.1rem;
        margin-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗳️ 政治MBTI診断 (16タイプ)")
st.write("以下の22の質問に対し、あなたの考えに最も近いものを直感で選んでください。")

# 7段階の選択肢とスコアの定義
options = {
    "強く賛成": 3,
    "賛成": 2,
    "やや賛成": 1,
    "どちらとも言えない": 0,
    "やや反対": -1,
    "反対": -2,
    "強く反対": -3
}
option_labels = list(options.keys())

# 設問データ (direction: 1 なら「賛成」で左極(B/L/P/R)へ、-1 なら右極(S/A/T/C)へ)
questions = [
    # ① 経済軸：【B】大きな政府(平等) vs 【S】小さな政府(成長)
    {"id": "q01", "axis": "BS", "dir": 1, "text": "経済競争力を多少犠牲にしても、いまは社会的格差の是正を優先すべきだ"},
    {"id": "q02", "axis": "BS", "dir": -1, "text": "社会福祉など政府のサービスが悪くなっても、税金のかからない小さな政府の方が良い"},
    {"id": "q03", "axis": "BS", "dir": 1, "text": "税負担は大きくても、福祉などの行政サービスが充実した社会を目指すべきだ"},
    {"id": "q04", "axis": "BS", "dir": 1, "text": "自分のことは自分で面倒を見るよりも、国民が安心して暮らせるよう国がもっと責任を持つべきだ"},
    {"id": "q05", "axis": "BS", "dir": 1, "text": "個々人の努力を刺激するよう収入の開きを大きくするより、収入はもっと平等にすべきだ"},
    {"id": "q06", "axis": "BS", "dir": 1, "text": "当面は財政再建のために歳出を抑えるのではなく、景気対策のために財政出動を行うべきだ"},

    # ② 統治軸：【L】自由(個人尊重) vs 【A】権威(秩序・統制)
    {"id": "q07", "axis": "LA", "dir": -1, "text": "治安を守るためなら、プライバシーや個人の権利が制約されるのは当然だ"},
    {"id": "q08", "axis": "LA", "dir": 1, "text": "行政機関による規制で安全を守るより、規制を極力なくして民間の自由な活動と自己責任に委ねるべきだ"},
    {"id": "q09", "axis": "LA", "dir": 1, "text": "国家の秩序や安全よりも、個人の自由や権利を優先して守るべきだ"},
    {"id": "q10", "axis": "LA", "dir": -1, "text": "犯罪防止のためなら、政府が公共の場で人々を監視カメラで監視するのもやむを得ない"},
    {"id": "q11", "axis": "LA", "dir": -1, "text": "テロ対策などのためなら、政府がインターネット上の情報交換を監視する権利を認めるべきだ"},
    {"id": "q12", "axis": "LA", "dir": 1, "text": "国家の秩序の維持よりも、言論の自由の擁護を重視すべきだ"},

    # ③ 価値観軸：【P】進歩(多様性) vs 【T】伝統(規範維持)
    {"id": "q13", "axis": "PT", "dir": 1, "text": "男性同士、女性同士の結婚を法律で認めるべきだ"},
    {"id": "q14", "axis": "PT", "dir": 1, "text": "夫婦が望む場合には、結婚後もそれぞれ結婚前の名字を名乗ることを法律で認めるべきだ"},
    {"id": "q15", "axis": "PT", "dir": 1, "text": "在留外国人が増えると、日本の社会や文化は多様で豊かになる"},
    {"id": "q16", "axis": "PT", "dir": 1, "text": "同性同士のカップルも異性同士のカップルと同じように立派な親になれる"},
    {"id": "q17", "axis": "PT", "dir": -1, "text": "日本の文化や伝統的価値観は優れており、これまで以上に大切に維持すべきだ"},
    {"id": "q18", "axis": "PT", "dir": 1, "text": "理工系の大学入試などで、女性を優先する「女性枠」を設けるなど、積極的な格差是正措置に納得できる"},

    # ④ 姿勢軸：【R】改革(現状打破) vs 【C】安定(漸進・維持)
    {"id": "q19", "axis": "RC", "dir": 1, "text": "今の社会の仕組みは、漸進的な変化ではなく、抜本的な改革によって根本的に変えなければならない"},
    {"id": "q20", "axis": "RC", "dir": 1, "text": "今の日本には、大きな社会変革が必要な時期だ"},
    {"id": "q21", "axis": "RC", "dir": 1, "text": "いまの政治・行政のしがらみを打ち破るような、強い指導者による改革が必要だ"},
    {"id": "q22", "axis": "RC", "dir": 1, "text": "いまの憲法は、時代に合わせて変える必要がある"}
]

# セッションステートの初期化（結果表示フラグ）
if 'show_results' not in st.session_state:
    st.session_state.show_results = False

# フォームの作成
with st.form("mbti_form"):
    answers = {}
    for i, q in enumerate(questions):
        st.markdown(f'<div class="question-box"><b>Q{i+1}. {q["text"]}</b></div>', unsafe_allow_html=True)
        # horizontal=Trueで横並びに
        ans = st.radio(
            label=f"Q{i+1}の回答", 
            options=option_labels, 
            index=3, # デフォルトは「どちらとも言えない」
            key=q["id"],
            label_visibility="collapsed",
            horizontal=True
        )
        answers[q["id"]] = options[ans]
        st.write("---")
    
    submitted = st.form_submit_button("診断結果を見る 🔍", use_container_width=True)

# 診断結果の計算と表示
if submitted:
    scores = {"BS": 0, "LA": 0, "PT": 0, "RC": 0}
    max_scores = {"BS": 0, "LA": 0, "PT": 0, "RC": 0}

    # 各軸のスコア計算
    for q in questions:
        axis = q["axis"]
        val = answers[q["id"]]
        scores[axis] += val * q["dir"]
        max_scores[axis] += 3 # 各問の最大絶対値は3

    # アルファベットの判定
    type_B = "B" if scores["BS"] >= 0 else "S"
    type_L = "L" if scores["LA"] >= 0 else "A"
    type_P = "P" if scores["PT"] >= 0 else "T"
    type_R = "R" if scores["RC"] >= 0 else "C"
    
    final_type = f"{type_B}{type_L}{type_P}{type_R}"

    st.markdown("## 📊 あなたの診断結果")
    st.markdown(f'<div class="result-type">{final_type}</div>', unsafe_allow_html=True)

    # 各軸の割合（パーセンテージ）を計算してバーを表示
    st.markdown("### 各パラメーターの傾向")
    
    axes_info = [
        {"id": "BS", "left": "B: 大きな政府 (再分配・平等)", "right": "S: 小さな政府 (市場・成長)"},
        {"id": "LA", "left": "L: 自由 (個人・権利尊重)", "right": "A: 権威 (治安・秩序維持)"},
        {"id": "PT", "left": "P: 進歩 (多様性・新価値観)", "right": "T: 伝統 (歴史・既存規範)"},
        {"id": "RC", "left": "R: 改革 (現状打破・急進)", "right": "C: 安定 (現状維持・漸進)"}
    ]

    for axis in axes_info:
        # スコアを0〜100%に正規化 (左極が100%, 右極が0%)
        # 例: スコアが0なら50%
        raw_score = scores[axis["id"]]
        max_s = max_scores[axis["id"]]
        percentage = ((raw_score + max_s) / (max_s * 2)) * 100
        
        left_color = "#2196F3" if raw_score >= 0 else "#B0BEC5"
        right_color = "#F44336" if raw_score < 0 else "#B0BEC5"

        st.markdown(f"""
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between;">
                <span style="color: {left_color}; font-weight: bold;">{axis["left"]}</span>
                <span style="color: {right_color}; font-weight: bold;">{axis["right"]}</span>
            </div>
            <div style="width: 100%; background-color: #e0e0e0; border-radius: 8px; height: 24px; margin-top: 5px; overflow: hidden; display: flex;">
                <div style="width: {percentage}%; background-color: #2196F3; height: 100%; transition: width 0.5s;"></div>
                <div style="width: {100 - percentage}%; background-color: #F44336; height: 100%; transition: width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.info("※ このスコアは各設問への回答（-3〜+3）を合算し、左極への傾き（青）と右極への傾き（赤）の強さを可視化したものです。")
