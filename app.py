"""政治MBTI診断 (Streamlit)

- 第1層: 4軸タイプ判定 (経済 / 統治 / 価値観 / 改革)
- 第2層: 争点プロフィール (タイプ計算には不算入)
- 1問1画面・タップで自動送り。Streamlit内部のDOMには依存しない
  (st.button / st.progress / 自前HTMLのみ) ので、PC・スマホで崩れにくい。

動作確認の目安: streamlit >= 1.30
起動: streamlit run political_mbti_app.py
"""

import csv
import io
import random

import streamlit as st

st.set_page_config(page_title="政治MBTI診断", page_icon="🗳️", layout="centered")

GREEN = "#33a474"
PURPLE = "#88619a"
GRAY = "#9ea0a5"

# 自前HTML用の最小限のCSS。Streamlitのダーク/ライトどちらでも読めるよう色は継承。
st.markdown(
    f"""
<style>
    .q-text {{
        text-align: center;
        font-size: 1.3rem;
        font-weight: 700;
        line-height: 1.7;
        margin: 28px 0 24px 0;
    }}
    .ab-wrap {{
        display: flex; flex-direction: column; gap: 10px; margin: 24px 0;
    }}
    .ab-box {{
        border-radius: 12px; padding: 14px 16px; line-height: 1.6;
        font-weight: 600; border: 2px solid;
    }}
    .ab-a {{ border-color: {GREEN}; }}
    .ab-b {{ border-color: {PURPLE}; }}
    .ab-tag {{ font-weight: 800; margin-right: 8px; }}
    .ab-a .ab-tag {{ color: {GREEN}; }}
    .ab-b .ab-tag {{ color: {PURPLE}; }}
    .result-type {{
        font-size: 3.6rem; font-weight: 900; text-align: center;
        letter-spacing: 0.12em; margin: 4px 0 0 0; color: #FF5722;
    }}
    .result-nick {{
        text-align: center; font-size: 1.2rem; font-weight: 700;
        margin-bottom: 18px;
    }}
    .axis {{ margin: 22px 0 6px 0; }}
    .axis-name {{ font-weight: 800; margin-bottom: 4px; }}
    .axis-head {{
        display: flex; justify-content: space-between;
        font-size: 0.9rem; font-weight: 700; gap: 8px;
    }}
    .bar {{
        position: relative; display: flex; width: 100%; height: 18px;
        border-radius: 10px; overflow: hidden; margin-top: 6px;
        background: #e0e0e0;
    }}
    .bar::after {{
        content: ""; position: absolute; left: 50%; top: 0; bottom: 0;
        width: 2px; background: #ffffff;
    }}
    .axis-note {{ font-size: 0.85rem; opacity: 0.75; margin-top: 4px; }}
    .issue-group {{ font-weight: 800; margin: 20px 0 6px 0; }}
    .issue-row {{
        display: flex; justify-content: space-between; align-items: center;
        padding: 8px 0; border-bottom: 1px solid rgba(128,128,128,0.25);
        gap: 12px;
    }}
    .issue-label {{ flex: 1; }}
    .dots {{ display: flex; gap: 6px; align-items: center; }}
    .dot {{ width: 14px; height: 14px; border-radius: 50%; display: inline-block; }}
    .issue-na {{ font-size: 0.85rem; opacity: 0.6; }}
    .legend {{
        display: flex; justify-content: space-between;
        font-size: 0.8rem; opacity: 0.7; margin-top: 4px;
    }}
</style>
""",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# 設問データ
#   kind: "agree" (賛否) / "ab" (2択)
#   dir : +1 = 賛成(A)するほど左側の文字(B/L/P/R)に寄る, -1 = 右側(S/A/T/C)に寄る
#   quick: クイック版(16問)に含めるか
# ---------------------------------------------------------------------------
QUESTIONS = [
    # ---- 経済軸 E : B(国に頼る) ⇔ S(自分で備える) ----
    {"id": "E1", "axis": "E", "kind": "agree", "dir": 1, "quick": True,
     "text": "税金が高くなっても、病院代や学費の負担が軽くなるほうがいい"},
    {"id": "E2", "axis": "E", "kind": "agree", "dir": -1, "quick": True,
     "text": "税金や保険料が安くなるなら、国がしてくれることが減ってもいい"},
    {"id": "E3", "axis": "E", "kind": "agree", "dir": 1, "quick": False,
     "text": "仕事を失ったり病気になったりした人は、国がしっかり支えてほしい"},
    {"id": "E4", "axis": "E", "kind": "agree", "dir": -1, "quick": False,
     "text": "頑張った人が、そうでない人よりずっと多く稼げる社会のほうがいい"},
    {"id": "E5", "axis": "E", "kind": "agree", "dir": 1, "quick": False,
     "text": "お金持ちや大きな会社は、今よりたくさん税金を払ってもいい"},
    {"id": "E6", "axis": "E", "kind": "agree", "dir": -1, "quick": False,
     "text": "国があれこれ口を出すより、会社や個人の自由にやらせたほうが暮らしは良くなる"},
    {"id": "EA1", "axis": "E", "kind": "ab", "dir": 1, "quick": True,
     "a": "仕事を失ったら、国がしばらく生活を支えてくれる",
     "b": "仕事を失っても、まずは自分で何とかする"},
    {"id": "EA2", "axis": "E", "kind": "ab", "dir": -1, "quick": True,
     "a": "税金は誰でも同じくらいにして、頑張った分は自分のものにする",
     "b": "大企業やお金持ちから、多めに税金を取る"},
    {"id": "EA3", "axis": "E", "kind": "ab", "dir": 1, "quick": False,
     "a": "老後は、国の年金が中心の暮らし",
     "b": "老後は、自分の貯金や投資が中心の暮らし"},
    # ---- 統治軸 G : L(自由) ⇔ A(秩序) ----
    {"id": "G1", "axis": "G", "kind": "agree", "dir": 1, "quick": True,
     "text": "多少社会の秩序が乱れても、個人の自由はできるだけ制限されないほうがよい"},
    {"id": "G2", "axis": "G", "kind": "agree", "dir": -1, "quick": True,
     "text": "犯罪やテロを防ぐためなら、街中のカメラ増設など、ある程度の監視は受け入れられる"},
    {"id": "G3", "axis": "G", "kind": "agree", "dir": 1, "quick": True,
     "text": "政府に批判的な意見でも、自由に発信できる社会が守られるべきだ"},
    {"id": "G4", "axis": "G", "kind": "agree", "dir": -1, "quick": False,
     "text": "社会が混乱したときは、強い指導者が物事を決めたほうがうまくいく"},
    # G5/G6 は「世界観」の暫定設問。試作版データで統治軸に乗るか要検証。
    {"id": "G5", "axis": "G", "kind": "agree", "dir": -1, "quick": True,
     "text": "平和を守るには、相手に攻めにくいと思わせるだけの力が必要だ"},
    {"id": "G6", "axis": "G", "kind": "agree", "dir": 1, "quick": False,
     "text": "対立している国とも、話し合いと国際ルールを重ねれば、争いは防げる"},
    # ---- 価値観軸 V : P(多様性) ⇔ T(伝統) ----
    {"id": "V1", "axis": "V", "kind": "agree", "dir": 1, "quick": True,
     "text": "子どもには、周りに合わせることより、自分の頭で考えて行動することを教えたい"},
    {"id": "V2", "axis": "V", "kind": "agree", "dir": -1, "quick": True,
     "text": "昔から続く慣習や家族のかたちは、変えずに受け継ぐ価値がある"},
    {"id": "V3", "axis": "V", "kind": "agree", "dir": 1, "quick": True,
     "text": "身近に、自分と違う文化や生き方の人が増えるのはよいことだ"},
    {"id": "V4", "axis": "V", "kind": "agree", "dir": -1, "quick": True,
     "text": "社会のまとまりのためには、価値観や生活習慣がある程度そろっていたほうがよい"},
    {"id": "V5", "axis": "V", "kind": "agree", "dir": 1, "quick": False,
     "text": "結婚や家族のあり方は、人それぞれが自由に選べばよい"},
    {"id": "V6", "axis": "V", "kind": "agree", "dir": -1, "quick": False,
     "text": "家庭や職場で、男女に期待される役割が多少違うのは自然なことだ"},
    # ---- 改革軸 R : R(改革) ⇔ C(安定) ----
    {"id": "R1", "axis": "R", "kind": "agree", "dir": 1, "quick": True,
     "text": "うまくいっていない制度は、混乱があっても思い切って作り直すべきだ"},
    {"id": "R2", "axis": "R", "kind": "agree", "dir": -1, "quick": True,
     "text": "制度は少しずつ手直ししていくほうが、失敗が少なくてよい"},
    {"id": "R3", "axis": "R", "kind": "agree", "dir": 1, "quick": True,
     "text": "前例や慣習にしばられない新しい人や政党に、政治を任せてみたい"},
    {"id": "R4", "axis": "R", "kind": "agree", "dir": -1, "quick": True,
     "text": "長く続いてきた仕組みにはそれなりの理由があるので、まず尊重すべきだ"},
    {"id": "R5", "axis": "R", "kind": "agree", "dir": 1, "quick": False,
     "text": "今の日本は、大きな変化が必要な段階にある"},
    {"id": "R6", "axis": "R", "kind": "agree", "dir": -1, "quick": False,
     "text": "変化を急ぐより、今の暮らしの安定を守ることを優先したい"},
]

# 第2層: 争点プロフィール (タイプ計算には使わない)
ISSUES = [
    ("I1", "安保・外交", "防衛力の強化"),
    ("I2", "安保・外交", "憲法9条の改正"),
    ("I3", "エネルギー", "原子力発電の活用（再稼働・新設）"),
    ("I4", "社会", "同性婚の法制化"),
    ("I5", "社会", "選択的夫婦別姓の導入"),
    ("I6", "社会", "外国人労働者の受け入れ拡大"),
    ("I7", "経済", "消費税の減税"),
    ("I8", "経済", "国債を発行しての景気対策（財政出動）"),
    ("I9", "経済", "最低賃金の大幅な引き上げ"),
    ("I10", "統治・制度", "憲法への緊急事態条項の新設"),
    ("I11", "統治・制度", "SNS上の誹謗中傷への規制強化"),
    ("I12", "統治・制度", "国会議員の定数削減"),
]
for _id, _group, _label in ISSUES:
    QUESTIONS.append(
        {"id": _id, "axis": None, "kind": "issue", "dir": 0, "quick": False,
         "group": _group, "label": _label, "text": f"{_label}に賛成ですか？"}
    )

QMAP = {q["id"]: q for q in QUESTIONS}
QUICK_IDS = [q["id"] for q in QUESTIONS if q["axis"] and q["quick"]]
MORE_IDS = [q["id"] for q in QUESTIONS if q["axis"] and not q["quick"]]
ISSUE_IDS = [q["id"] for q in QUESTIONS if q["kind"] == "issue"]

# 軸の定義 (表示順 = タイプ文字の並び順)
AXES = {
    "E": {"name": "経済", "left": ("B", "国に頼る", "大きな政府・再分配"),
          "right": ("S", "自分で備える", "小さな政府・市場")},
    "G": {"name": "統治", "left": ("L", "自由", "個人・権利を重視"),
          "right": ("A", "秩序", "治安・まとまりを重視")},
    "V": {"name": "価値観", "left": ("P", "多様性", "個人の選択・新しい価値観"),
          "right": ("T", "伝統", "慣習・既存の規範")},
    "R": {"name": "改革姿勢", "left": ("R", "改革", "現状を大きく変える"),
          "right": ("C", "安定", "少しずつ・今を守る")},
}

# タイプのニックネーム (仮)。評価的に聞こえない表現に調整してください。
NICKNAMES = {
    "BLPR": "理想を掲げる改革派", "BLPC": "寄り添うリベラル派",
    "BLTR": "人情派の改革者", "BLTC": "暮らしを守る堅実派",
    "BAPR": "制度で変える設計派", "BAPC": "制度で支える安定派",
    "BATR": "強い国を立て直す再建派", "BATC": "守りの福祉国家派",
    "SLPR": "自由な挑戦者", "SLPC": "マイペース個人主義者",
    "SLTR": "自立の改革派", "SLTC": "自己責任の堅実派",
    "SAPR": "効率重視の改革者", "SAPC": "現実主義の管理者",
    "SATR": "市場と強い国の変革派", "SATC": "秩序と自立の守り手",
}

AGREE_OPTIONS = [
    ("🟢 賛成", 2),
    ("🌿 どちらかといえば賛成", 1),
    ("⚪ どちらともいえない", 0),
    ("🪻 どちらかといえば反対", -1),
    ("🟣 反対", -2),
]
AB_OPTIONS = [
    ("🟢 Aに近い", 2),
    ("🌿 ややA", 1),
    ("⚪ どちらでもない", 0),
    ("🪻 ややB", -1),
    ("🟣 Bに近い", -2),
]


# ---------------------------------------------------------------------------
# 状態管理
# ---------------------------------------------------------------------------
def init_state():
    ss = st.session_state
    if "page" not in ss:
        ss.page = "intro"      # intro / quiz / result
        ss.answers = {}        # id -> -2..2 / None(わからない)
        ss.queue = []
        ss.pos = 0
        ss.stage = "base"      # base / more / issues
        ss.seed = random.randrange(10**9)


def start_quiz(stage, ids):
    ss = st.session_state
    rng = random.Random(f"{ss.seed}-{stage}")
    shuffled = list(ids)
    rng.shuffle(shuffled)
    ss.queue = [i for i in shuffled if i not in ss.answers]
    ss.pos = 0
    ss.stage = stage
    ss.page = "quiz" if ss.queue else "result"


def answer(qid, val):
    ss = st.session_state
    ss.answers[qid] = val
    ss.pos += 1
    if ss.pos >= len(ss.queue):
        ss.page = "result"


def go_back():
    ss = st.session_state
    if ss.pos > 0:
        ss.pos -= 1


def show_result():
    st.session_state.page = "result"


def reset_all():
    for k in list(st.session_state.keys()):
        del st.session_state[k]


# ---------------------------------------------------------------------------
# 計算
# ---------------------------------------------------------------------------
def axis_score(axis):
    """-1(右側) 〜 +1(左側) の比率と、有効回答数を返す。回答3問未満はNone。"""
    ans = st.session_state.answers
    total, n = 0, 0
    for q in QUESTIONS:
        if q["axis"] != axis:
            continue
        v = ans.get(q["id"])
        if v is None:
            continue
        total += v * q["dir"]
        n += 1
    if n < 3:
        return None, n
    return total / (2 * n), n


def strength_label(ratio, left, right):
    a = abs(ratio)
    side = left if ratio >= 0 else right
    if a < 0.15:
        return "ほぼ中央（バランス型）"
    if a < 0.5:
        return f"やや {side[0]}（{side[1]}）寄り"
    return f"{side[0]}（{side[1]}）寄り"


# ---------------------------------------------------------------------------
# 画面
# ---------------------------------------------------------------------------
def render_intro():
    st.title("🗳️ 政治MBTI診断")
    st.write(
        "政党名ではなく、暮らしや社会についての「考え方」から、"
        "あなたの政治的な傾向を4つの軸でタイプにします。"
        "正解はありません。直感で答えてください。"
    )
    st.caption("※ 娯楽・自己理解のための診断です。投票先を推薦するものではありません。")
    st.write("")
    st.button(
        "⚡ クイック診断（16問・約3分）",
        on_click=start_quiz, args=("base", QUICK_IDS),
        use_container_width=True, type="primary",
    )
    st.button(
        "🔍 じっくり診断（27問・約6分）",
        on_click=start_quiz, args=("base", QUICK_IDS + MORE_IDS),
        use_container_width=True,
    )


def render_quiz():
    ss = st.session_state
    q = QMAP[ss.queue[ss.pos]]
    total = len(ss.queue)

    if ss.stage != "base":
        st.button("← 結果に戻る", on_click=show_result, key="to_result")

    st.progress(ss.pos / total, text=f"{ss.pos + 1} / {total}")

    if q["kind"] == "ab":
        st.markdown(
            f"""
<div class="ab-wrap">
  <div class="ab-box ab-a"><span class="ab-tag">A</span>{q["a"]}</div>
  <div class="ab-box ab-b"><span class="ab-tag">B</span>{q["b"]}</div>
</div>
<div class="q-text" style="font-size:1.05rem;margin-top:0;">どちらに近いですか？</div>
""",
            unsafe_allow_html=True,
        )
        options = AB_OPTIONS
    else:
        st.markdown(f'<div class="q-text">{q["text"]}</div>', unsafe_allow_html=True)
        options = AGREE_OPTIONS

    for label, val in options:
        st.button(
            label, key=f'{q["id"]}_{val}', on_click=answer,
            args=(q["id"], val), use_container_width=True,
        )
    st.button(
        "わからない / 答えたくない", key=f'{q["id"]}_na', on_click=answer,
        args=(q["id"], None), use_container_width=True,
    )
    if ss.pos > 0:
        st.button("← ひとつ前に戻る", key=f'{q["id"]}_back', on_click=go_back)


def axis_bar_html(axis_key, ratio, n):
    info = AXES[axis_key]
    left, right = info["left"], info["right"]
    pct_left = (ratio + 1) / 2 * 100
    return f"""
<div class="axis">
  <div class="axis-name">{info["name"]}</div>
  <div class="axis-head">
    <span style="color:{GREEN};">{left[0]}　{left[1]}</span>
    <span style="color:{PURPLE};">{right[1]}　{right[0]}</span>
  </div>
  <div class="bar">
    <div style="width:{pct_left:.1f}%;background:{GREEN};"></div>
    <div style="width:{100 - pct_left:.1f}%;background:{PURPLE};"></div>
  </div>
  <div class="axis-note">{strength_label(ratio, left, right)}（{n}問に回答）</div>
</div>
"""


def issue_dots_html(val):
    colors = {2: GREEN, 1: "#8fd3b4", 0: "#c9cacd", -1: "#c5aad2", -2: PURPLE}
    dots = ""
    for v in (2, 1, 0, -1, -2):
        selected = v == val
        dots += (
            f'<span class="dot" style="background:{colors[v]};'
            f'opacity:{1 if selected else 0.18};'
            f'transform:scale({1.3 if selected else 0.85});"></span>'
        )
    return f'<div class="dots">{dots}</div>'


def render_issue_profile():
    ans = st.session_state.answers
    st.markdown("### 🧭 争点プロフィール")
    st.caption(
        "タイプとは別に、個別の争点での立ち位置を表示します。"
        "タイプと違う位置があっても自然なことです。"
    )
    st.markdown(
        '<div class="legend"><span>賛成</span><span>反対</span></div>',
        unsafe_allow_html=True,
    )
    groups = []
    for _, g, _ in ISSUES:
        if g not in groups:
            groups.append(g)
    html = ""
    for g in groups:
        html += f'<div class="issue-group">{g}</div>'
        for iid, grp, label in ISSUES:
            if grp != g:
                continue
            val = ans.get(iid)
            right = '<span class="issue-na">わからない</span>' if val is None \
                else issue_dots_html(val)
            html += (
                f'<div class="issue-row"><span class="issue-label">{label}</span>'
                f"{right}</div>"
            )
    st.markdown(html, unsafe_allow_html=True)


def answers_csv():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "axis", "dir", "value"])
    for qid, val in st.session_state.answers.items():
        q = QMAP[qid]
        w.writerow([qid, q["axis"] or "issue", q["dir"], "" if val is None else val])
    return buf.getvalue()


def render_result():
    ss = st.session_state
    st.markdown("## 📊 あなたの診断結果")

    letters, rows = "", []
    for key, info in AXES.items():
        ratio, n = axis_score(key)
        if ratio is None:
            letters += "?"
            rows.append((key, None, n))
        else:
            side = info["left"] if ratio >= 0 else info["right"]
            letters += side[0]
            rows.append((key, ratio, n))

    st.markdown(f'<div class="result-type">{letters}</div>', unsafe_allow_html=True)
    nick = NICKNAMES.get(letters)
    if nick:
        st.markdown(f'<div class="result-nick">{nick}</div>', unsafe_allow_html=True)

    for key, ratio, n in rows:
        if ratio is None:
            st.markdown(
                f'<div class="axis"><div class="axis-name">{AXES[key]["name"]}</div>'
                f'<div class="axis-note">回答が足りないため判定保留です（{n}問）。</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(axis_bar_html(key, ratio, n), unsafe_allow_html=True)

    st.write("")
    more_left = [i for i in MORE_IDS if i not in ss.answers]
    issues_left = [i for i in ISSUE_IDS if i not in ss.answers]

    if more_left:
        st.button(
            f"🎯 精度アップ（あと{len(more_left)}問）",
            on_click=start_quiz, args=("more", MORE_IDS),
            use_container_width=True,
        )

    if issues_left:
        st.button(
            f"🧭 争点プロフィールを見る（{len(issues_left)}問）",
            on_click=start_quiz, args=("issues", ISSUE_IDS),
            use_container_width=True, type="primary",
        )
    else:
        render_issue_profile()

    st.write("")
    with st.expander("回答データをCSVで保存（試作版の検証用）"):
        st.download_button(
            "CSVをダウンロード", data=answers_csv(),
            file_name="political_mbti_answers.csv", mime="text/csv",
        )
    st.button("🔄 最初からやり直す", on_click=reset_all, use_container_width=True)
    st.caption("※ 娯楽・自己理解のための診断です。投票先を推薦するものではありません。")


# ---------------------------------------------------------------------------
init_state()
page = st.session_state.page
if page == "intro":
    render_intro()
elif page == "quiz":
    render_quiz()
else:
    render_result()
