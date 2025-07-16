import streamlit as st
import pandas as pd
import datetime

# 학생 목록과 차시 설정
students = ["강정원", "고민서", "권지연", "김가령", "김나형", "김예르미", "박수빈", "송가은", "이려흔", "이수아", "임보배", "정지윤", "지혜원", "최수민", "하다빈", "한유진"]
periods = ["1차시", "2차시"]

# 정기 결석 설정
regular_absents = {
    "고민서": [("both", [1])],   
    "권지연": [("2nd", [0, 3, 5])],
    "김가령": [("both", [4])],
    "김나형": [("2nd", [0, 2, 5])],
    "김예르미": [("both", [4])],
    "이려흔":[("both", [2,5])],
    "이수아": [("both", [4, 5])],
    "정지윤": [("both", [5])],
    "최수민": [("both", [0])], "최수민": [("2nd", [5])],
    "하다빈": [("both", [0])],
    "한유진":[("2nd", [0, 3, 5])],
}

st.title("📝 출석부 (날짜별 초기화 + 정기 결석 + 출석 요약)")

# 오늘 날짜 및 자동 초기화
today = datetime.date.today()
date = st.date_input("출석 날짜", today)
date_str = date.strftime("%Y-%m-%d")
weekday = date.weekday()

# 날짜 변경 시 상태 초기화
if "selected_date" not in st.session_state:
    st.session_state.selected_date = date

if st.session_state.selected_date != date:
    for key in list(st.session_state.keys()):
        if "_cb" in key or "_rs" in key:
            del st.session_state[key]
    st.session_state.selected_date = date

# 임시 및 최종 기록 초기화
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
if "final_attendance" not in st.session_state:
    st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
if "summary_data" not in st.session_state:
    st.session_state.summary_data = []

# 출석 체크 UI
st.subheader("📋 출석 체크 (결석자만 체크)")

absent_students_period = {period: [] for period in periods}
reasons_period = {period: {} for period in periods}

for period in periods:
    st.markdown(f"### ▶ {period} 출석 체크")
    for name in students:
        auto_absent = False
        reason = ""
        if name in regular_absents:
            for pattern, days in regular_absents[name]:
                if weekday in days:
                    if pattern == "both":
                        auto_absent = True
                        reason = "정기 결석 (1,2차시)"
                    elif pattern == "2nd" and period == "2차시":
                        auto_absent = True
                        reason = "정기 결석 (2차시)"
        key_cb = f"{name}_{period}_cb"
        key_rs = f"{name}_{period}_rs"

        if auto_absent:
            st.markdown(f"❗ **{name}**: {reason} (자동 처리)")
            absent_students_period[period].append(name)
            reasons_period[period][name] = reason
        else:
            col1, col2 = st.columns([1, 4])
            with col1:
                if st.checkbox(f"{name}", key=key_cb):
                    absent_students_period[period].append(name)
            with col2:
                if name in absent_students_period[period]:
                    reasons_period[period][name] = st.text_input(
                        f"{name} 결석 사유 ({period})", key=key_rs
                    )
                else:
                    reasons_period[period][name] = ""

# ✅ 임시 저장 버튼 클릭 시 출석 기록 + 요약 정보 저장
if st.button("💾 임시 출석 기록 저장"):
    for period in periods:
        st.session_state.temp_attendance = st.session_state.temp_attendance[
            ~((st.session_state.temp_attendance["날짜"] == date_str) &
              (st.session_state.temp_attendance["차시"] == period) &
              (st.session_state.temp_attendance["이름"].isin(students)))
        ]
        for name in students:
            if name in absent_students_period[period]:
                status = "결석"
                reason = reasons_period[period].get(name, "")
            else:
                status = "출석"
                reason = ""
            st.session_state.temp_attendance.loc[len(st.session_state.temp_attendance)] = [
                date_str, period, name, status, reason
            ]

    # ✅ 출석 요약 정보 생성
    summary_data = []
    for period in periods:
        data = st.session_state.temp_attendance
        total = len(students)
        absents = data[(data["날짜"] == date_str) & (data["차시"] == period) & (data["상태"] == "결석")]
        present = total - len(absents)
        summary_data.append({
            "차시": period,
            "출석": present,
            "결석": len(absents)
        })
    st.session_state.summary_data = summary_data
    st.success("✅ 임시 출석 기록이 저장되었습니다.")

# ✅ 출석 요약 정보 표시
if st.session_state.summary_data:
    st.subheader("📈 출석 요약 정보")
    st.table(pd.DataFrame(st.session_state.summary_data))

# ✅ 피벗: 이름 세로 / 차시별 상태·사유 가로
def pivot_attendance(df):
    if df.empty:
        return df
    pivoted = df.pivot_table(
        index=["날짜", "이름"],
        columns="차시",
        values=["상태", "사유"],
        aggfunc="first",
        fill_value=""
    )
    pivoted.columns = [f"{col2} {col1}" for col1, col2 in pivoted.columns]
    return pivoted.reset_index().sort_values(by=["날짜", "이름"]).reset_index(drop=True)

# ✅ 임시 출석 기록 보기 및 수정
st.subheader("📝 임시 출석 기록 (학생별 1줄 보기)")

if not st.session_state.temp_attendance.empty:
    pivot_temp = pivot_attendance(st.session_state.temp_attendance)
    edited_temp = st.data_editor(pivot_temp, num_rows="dynamic", key="temp_editor")

    # 다시 세로 형태로 풀기
    rows = []
    for _, row in edited_temp.iterrows():
        for period in periods:
            상태 = row.get(f"{period} 상태", "")
            사유 = row.get(f"{period} 사유", "")
            rows.append({
                "날짜": row["날짜"],
                "이름": row["이름"],
                "차시": period,
                "상태": 상태,
                "사유": 사유,
            })
    st.session_state.temp_attendance = pd.DataFrame(rows)

# ✅ 최종 저장
if st.button("✅ 최종 출석 기록 저장"):
    st.session_state.final_attendance = st.session_state.final_attendance[
        st.session_state.final_attendance["날짜"] != date_str
    ]
    st.session_state.final_attendance = pd.concat([
        st.session_state.final_attendance,
        st.session_state.temp_attendance
    ], ignore_index=True)
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.summary_data = []
    st.success("🎉 최종 출석 기록이 저장되었습니다.")

# ✅ 최종 출석 기록 보기
st.subheader("📊 최종 출석 기록 (학생별 1줄 보기)")

if not st.session_state.final_attendance.empty:
    pivot_final = pivot_attendance(st.session_state.final_attendance)
    edited_final = st.data_editor(pivot_final, num_rows="dynamic", key="final_editor")

    # 되돌리기
    rows = []
    for _, row in edited_final.iterrows():
        for period in periods:
            상태 = row.get(f"{period} 상태", "")
            사유 = row.get(f"{period} 사유", "")
            rows.append({
                "날짜": row["날짜"],
                "이름": row["이름"],
                "차시": period,
                "상태": 상태,
                "사유": 사유,
            })
    st.session_state.final_attendance = pd.DataFrame(rows)
