import streamlit as st
import pandas as pd
import os
from fpdf import FPDF
from datetime import datetime
import altair as alt

LOG_FILE = "bmi_log.csv"
FONT_PATH = "ipaexg.ttf"  # 必ずアプリのフォルダに配置

def load_log():
    if os.path.exists(LOG_FILE):
        return pd.read_csv(LOG_FILE)
    else:
        return pd.DataFrame(columns=["日時", "身長(m)", "体重(kg)", "腹囲(cm)", "BMI", "性別",
                                     "ランニング(km)", "自転車(km)", "水泳(km)"])

def save_log(entry):
    df = load_log()
    df = pd.concat([df, pd.DataFrame([entry])], ignore_index=True)
    df.to_csv(LOG_FILE, index=False, encoding="utf-8-sig")  # 日本語対策

st.set_page_config(page_title="健康チェックアプリ", layout="centered")
st.title("🏃‍♀️ 健康チェックアプリ＋運動ログ")
st.markdown("BMI・腹囲・運動距離・ログ保存・グラフ・PDF診断まで対応")

with st.form("health_form"):
    st.subheader("📥 入力フォーム")
    height = st.number_input("身長 (m)", min_value=0.5, max_value=2.5, step=0.01)
    weight = st.number_input("体重 (kg)", min_value=0.0, max_value=300.0, step=0.1)
    waist = st.number_input("腹囲 (cm)", min_value=30.0, max_value=200.0, step=0.1)
    gender = st.radio("性別", ["男性", "女性"], horizontal=True)
    run = st.number_input("🏃‍♀️ ランニング距離 (km)", min_value=0.0, step=0.1)
    bike = st.number_input("🚴‍♂️ 自転車距離 (km)", min_value=0.0, step=0.1)
    swim = st.number_input("🏊 水泳距離 (km)", min_value=0.0, step=0.1)
    submitted = st.form_submit_button("✅ 診断・保存")

if submitted and height > 0 and weight > 0:
    bmi = weight / (height ** 2)
    ideal_weight = 22 * (height ** 2)

    st.subheader("📊 結果")
    st.success(f"適正体重（BMI 22）: {ideal_weight:.2f} kg")
    st.info(f"BMI: {bmi:.2f}")

    st.subheader("🩺 BMI評価")
    if bmi < 18.5:
        st.warning("やせ型")
    elif bmi < 25:
        st.success("標準体型")
    elif bmi < 30:
        st.warning("肥満（1度）")
    else:
        st.error("高度肥満")

    st.subheader("📐 腹囲評価")
    if gender == "男性":
        st.write("基準：85cm未満")
        st.success("正常") if waist < 85 else st.error("メタボの可能性あり")
    else:
        st.write("基準：90cm未満")
        st.success("正常") if waist < 90 else st.error("メタボの可能性あり")

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = {
        "日時": now, "身長(m)": height, "体重(kg)": weight, "腹囲(cm)": waist,
        "BMI": round(bmi, 2), "性別": gender,
        "ランニング(km)": run, "自転車(km)": bike, "水泳(km)": swim
    }
    save_log(entry)
    st.success("✅ ログを保存しました")

# データ読み込み
df = load_log()

# 運動距離の列が存在しない場合は追加（初期値0.0）
for col in ["ランニング(km)", "自転車(km)", "水泳(km)"]:
    if col not in df.columns:
        df[col] = 0.0

# 列の順番を揃える（任意）
expected_cols = ["日時", "身長(m)", "体重(kg)", "腹囲(cm)", "BMI", "性別", "ランニング(km)", "自転車(km)", "水泳(km)"]
df = df.reindex(columns=expected_cols)

if not df.empty:
    st.subheader("📒 ログ履歴")
    st.dataframe(df.tail(10), use_container_width=True)

    st.download_button("⬇️ CSVダウンロード", df.to_csv(index=False, encoding="utf-8-sig").encode(), file_name="bmi_log.csv")

    st.subheader("📈 グラフ表示")
    df_plot = df.copy()
    df_plot["日時"] = pd.to_datetime(df_plot["日時"])

    bmi_chart = alt.Chart(df_plot).mark_line(point=True).encode(
        x="日時:T", y="BMI:Q", tooltip=["日時", "BMI"]
    ).properties(title="BMIの推移")
    st.altair_chart(bmi_chart, use_container_width=True)

    # 距離グラフ
    df_plot = df.copy()
    df_plot["日時"] = pd.to_datetime(df_plot["日時"])

    # 存在しない列があっても落ちないよう保証
    expected_cols = ["ランニング(km)", "自転車(km)", "水泳(km)"]
    for col in expected_cols:
        if col not in df_plot.columns:
            df_plot[col] = 0.0

    # データをlong形式に変換
    df_melted = df_plot.melt(
        id_vars=["日時"],
        value_vars=expected_cols,
        var_name="種目",
        value_name="距離"
    )
    df_melted["種目"] = df_melted["種目"].astype(str)

    # Altair グラフ
    dist_chart = alt.Chart(df_melted).mark_bar().encode(
        x=alt.X("日時:T", title="日付"),
        y=alt.Y("距離:Q", title="距離 (km)"),
        color=alt.Color("種目:N", title="種目"),
        tooltip=["日時", "種目", "距離"]
    ).properties(title="運動距離の推移")

    st.altair_chart(dist_chart, use_container_width=True)

    st.subheader("📄 PDF出力")
    if st.button("📤 PDF診断書を生成"):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('IPAexGothic', '', FONT_PATH, uni=True)
        pdf.set_font("IPAexGothic", '', 12)
        pdf.cell(200, 10, txt="健康診断書", ln=1, align='C')
        for k, v in df.iloc[-1].items():
            pdf.cell(200, 10, txt=f"{k}: {v}", ln=1)
        pdf.output("bmi_report.pdf")
        with open("bmi_report.pdf", "rb") as f:
            st.download_button("📥 ダウンロード", f, file_name="bmi_report.pdf")
else:
    st.info("まだログがありません")
