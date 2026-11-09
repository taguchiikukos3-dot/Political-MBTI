import streamlit as st
import pandas as pd

# ページ設定
st.set_page_config(page_title="政治MBTI診断", page_icon="🗳️", layout="centered")

# カスタムCSS（MBTI風の7つの丸UIを再現する魔法）
st.markdown("""
<style>
    /* 質問テキストを中央揃えで読みやすく */
    .question-text {
        text-align: center;
        font-size: 1.3rem;
        font-weight: bold;
        margin-top: 40px;
        margin-bottom: 25px;
        color: #2c3e50;
        line-height: 1.5;
    }
    
    /* 「同意する」「反対する」のラベル */
    .labels-container {
        display: flex;
        justify-content: space-between;
        padding: 0 10%;
        font-weight: bold;
        margin-bottom: -15px;
    }
    .agree-label { color: #33a474; font-size: 1.1rem; }
    .disagree-label { color: #88619a; font-size: 1.1rem; }

    /* Streamlitの標準ラジオボタンテキストを非表示にする */
    div[role="radiogroup"] label p {
        display: none !important;
    }

    /* 7つの丸を均等に横並び配置 */
    div[role="radiogroup"] {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 80%;
        margin: 0 auto 40px auto;
        padding: 20px 0;
        border-bottom: 1px solid #f0f2f6;
    }

    /* 丸のサイズを左右対称で変える（16Personalities風） */
    div[role="radiogroup"] > label:nth-child(1) { transform: scale(2.0); }
    div[role="radiogroup"] > label:nth-child(2) { transform: scale(1.5); }
    div[role="radiogroup"] > label:nth-child(3) { transform: scale(1.1); }
    div[role="radiogroup"] > label:nth-child(4) { transform: scale(0.9); }
    div[role="radiogroup"] > label:nth-child(5) { transform: scale(1.1); }
    div[role="radiogroup"] > label:nth-child(6) { transform: scale(1.5); }
    div[role="radiogroup"] > label:nth-child(7) { transform: scale(2.0); }

    /* 結果画面のテキストスタイル */
    .result-type {
        font-size: 4rem;
        font-weight: 900;
        color: #FF5722;
        text-align: center;
        margin: 10px 0 30px 0;
        letter-spacing: 0.1em;
    }
</style>
""", unsafe_allow_html=True)

st.title("🗳️ 政治MBTI診断")
st.write("以下の22の質問に対し、直感で選んでください。")

# 内部計算用のスコアマッピング（画面の文字はCSSで消えます）
scale_mapping = {
    "opt1": 3,   # 強く同意
    "opt2": 2,   # 同意
    "opt3": 1,   # やや同意
    "opt4": 0,   # 中立
    "opt5": -1,  # やや反対
    "opt6": -2,  # 反対
    "opt7": -3   # 強く反対
}
option_labels = list(scale_mapping.keys())

# 設問データ
questions = [
    # ① 経済軸：【B】大きな政府(平等) vs 【S】小さな政府(成長)
    {"id": "q01", "axis": "BS", "dir": 1, "text": "経済の成長よりも、貧富の差をなくすことのほうが大切だ"},
    {"id": "q02", "axis": "BS", "dir": -1, "text": "行政のサービスが手薄になっても、税金が安い社会のほうがいい"},
    {"id": "q03", "axis": "BS", "dir": 1, "text": "税金が高くなっても、年金や医療が充実している社会がいい"},
    {"id": "q04", "axis": "BS", "dir": -1, "text": "自分のことは自分で責任を持つべきだ"},
    {"id": "q05", "axis": "BS", "dir": -1, "text": "がんばった人の収入がとても高いのは当然だ"},
    {"id": "q06", "axis": "BS", "dir": 1, "text": "政府がお金を使って景気を良くするべきだ"},

    # ② 統治軸：【L】自由(個人尊重) vs 【A】権威(秩序・統制)
    {"id": "q07", "axis": "LA", "dir": 1, "text": "治安を守ることよりも個人のプライバシーが大切だ"},
    {"id": "q08", "axis": "LA", "dir": 1, "text": "国があれこれルールを決めるのはよくない"},
    {"id": "q09", "axis": "LA", "dir": -1, "text": "国のルールや秩序が何よりも大切だ"},
    {"id": "q10", "axis": "LA", "dir": -1, "text": "犯罪を防ぐために、街中の監視カメラで国が人々を監視してもよい"},
    {"id": "q11", "axis": "LA", "dir": -1, "text": "テロなどを防ぐために、国がネット上のやり取りを監視してもよい"},
    {"id": "q12", "axis": "LA", "dir": 1, "text": "言論の自由や表現の自由を大切にすべきだ"},

    # ③ 価値観軸：【P】進歩(多様性) vs 【T】伝統(規範維持)
    {"id": "q13", "axis": "PT", "dir": 1, "text": "同性婚を法律で認めるべきだ"},
    {"id": "q14", "axis": "PT", "dir": 1, "text": "希望すれば夫婦で別の名字にできる「選択的夫婦別姓」を認めるべきだ"},
    {"id": "q15", "axis": "PT", "dir": 1, "text": "外国人が増えることで、日本の社会や文化は多様になって豊かになると思う"},
    {"id": "q16", "axis": "PT", "dir": 1, "text": "同性カップルも、男女のカップルと同じように立派に子育てができる"},
    {"id": "q17", "axis": "PT", "dir": -1, "text": "日本の古き良き文化や伝統的な価値観は、これからも大切に守っていくべきだ"},
    {"id": "q18", "axis": "PT", "dir": 1, "text": "男女格差をなくす特別な取り組みに賛成だ"},

    # ④ 姿勢軸：【R】改革(現状打破) vs 【C】安定(漸進・維持)
    {"id": "q19", "axis": "RC", "dir": 1, "text": "今の社会の仕組みを根本からガラッと変えるべきだ"},
    {"id": "q20", "axis": "RC", "dir": -1, "text": "今の日本の仕組みを大切にするべきだ"},
    {"id": "q21", "axis": "RC", "dir": 1, "text": "既存のルールやしがらみをぶっ壊すような、強いリーダーが必要だ"},
    {"id": "q22", "axis": "RC", "dir": 1, "text": "今の日本の仕組みや憲法は、時代に合わせて作り直す必要がある"}
]

# フォームの作成
with st.form("mbti_form"):
    answers = {}
    for i, q in enumerate(questions):
        # 質問文とラベル
        st.markdown(f'<div class="question-text">Q{i+1}. {q["text"]}</div>', unsafe_allow_html=True)
        st.markdown('''
            <div class="labels-container">
                <span class="agree-label">同意する</span>
                <span class="disagree-label">反対する</span>
            </div>
        ''', unsafe_allow_html=True)
        
        # UI上はCSSで丸だけになるラジオボタン
        ans = st.radio(
            label=f"Q{i+1}", 
            options=option_labels, 
            index=3, # デフォルトは中央(中立)
            key=q["id"],
            label_visibility="collapsed",
            horizontal=True
        )
        answers[q["id"]] = scale_mapping[ans]
    
    st.write("")
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
        max_scores[axis] += 3 

    # アルファベットの判定
    type_B = "B" if scores["BS"] >= 0 else "S"
    type_L = "L" if scores["LA"] >= 0 else "A"
    type_P = "P" if scores["PT"] >= 0 else "T"
    type_R = "R" if scores["RC"] >= 0 else "C"
    
    final_type = f"{type_B}{type_L}{type_P}{type_R}"

    st.markdown("---")
    st.markdown("## 📊 あなたの診断結果")
    st.markdown(f'<div class="result-type">{final_type}</div>', unsafe_allow_html=True)

    st.markdown("### 各パラメーターの傾向")
    
    axes_info = [
        {"id": "BS", "left": "B: 大きな政府 (再分配・平等)", "right": "S: 小さな政府 (市場・成長)"},
        {"id": "LA", "left": "L: 自由 (個人・権利尊重)", "right": "A: 権威 (治安・秩序維持)"},
        {"id": "PT", "left": "P: 進歩 (多様性・新価値観)", "right": "T: 伝統 (歴史・既存規範)"},
        {"id": "RC", "left": "R: 改革 (現状打破・急進)", "right": "C: 安定 (現状維持・漸進)"}
    ]

    for axis in axes_info:
        raw_score = scores[axis["id"]]
        max_s = max_scores[axis["id"]]
        percentage = ((raw_score + max_s) / (max_s * 2)) * 100
        
        left_color = "#33a474" if raw_score >= 0 else "#B0BEC5"
        right_color = "#88619a" if raw_score < 0 else "#B0BEC5"

        st.markdown(f"""
        <div style="margin-top: 20px;">
            <div style="display: flex; justify-content: space-between; font-size: 0.9rem;">
                <span style="color: {left_color}; font-weight: bold;">{axis["left"]}</span>
                <span style="color: {right_color}; font-weight: bold;">{axis["right"]}</span>
            </div>
            <div style="width: 100%; background-color: #e0e0e0; border-radius: 12px; height: 20px; margin-top: 5px; overflow: hidden; display: flex;">
                <div style="width: {percentage}%; background-color: #33a474; height: 100%; transition: width 0.5s;"></div>
                <div style="width: {100 - percentage}%; background-color: #88619a; height: 100%; transition: width 0.5s;"></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
