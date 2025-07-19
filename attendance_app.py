
import streamlit as st
import pandas as pd
import datetime

# --- 설정 ---
students = ["김가령", "이서연", "박지우", "최민준", "정하윤"]
periods = ["1차시", "2차시", "3차시", "4차시", "5차시"]

# 정기 결석 정보 설정: (요일, 차시)
regular_absents = {
    "김가령": [("월요일", ["5차시"]), ("수요일", ["1차시", "2차시"])],
    "이서연": [("화요일", ["2차시"])],
    "정하윤": [("목요일", ["3차시"])]
}

# --- 날짜 선택 ---
today = datetime.date.today()
date = st.date_input("출석 날짜를 선택하세요", today)
date_str = date.strftime("%Y-%m-%d")
day_name = date.strftime("%A")  # 요일 (예: Monday)
weekdays_kr = {
    "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
    "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"
}
day_name_kr = weekdays_kr.get(day_name, day_name)

# --- 세션 상태 초기화 ---
if "check_states" not in st.session_state or st.session_state.get("last_checked_date") != date_str:
    st.session_state.check_states = {}
    st.session_state.reasons = {}
    st.session_state.last_checked_date = date_str

if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "이름", "차시", "상태", "사유"])

# --- 출석 체크 ---
st.subheader("📋 출석 체크 (결석자만 체크)")
for period in periods:
    st.markdown(f"### ⏰ {period}")
    for name in students:
        is_regular_absent = any(
            (day == day_name_kr and period in periods_) for (day, periods_) in regular_absents.get(name, [])
        )
        if is_regular_absent:
            continue

        key = f"{date_str}_{period}_{name}"
        checked = st.checkbox(f"{name} 결석", key=key)
        st.session_state.check_states[key] = checked

        if checked:
            reason_key = f"{key}_reason"
            reason = st.text_input(f"사유 입력 ({name}, {period})", key=reason_key)
            st.session_state.reasons[reason_key] = reason

# --- 출석 요약 정보 ---
summary = {}
for period in periods:
    present_count = 0
    absent_count = 0
    for name in students:
        is_regular_absent = any(
            (day == day_name_kr and period in periods_) for (day, periods_) in regular_absents.get(name, [])
        )
        if is_regular_absent:
            continue

        key = f"{date_str}_{period}_{name}"
        if st.session_state.check_states.get(key, False):
            absent_count += 1
        else:
            present_count += 1
    summary[period] = {"출석": present_count, "결석": absent_count}

st.subheader("📈 출석 요약 정보")
for period in periods:
    st.markdown(f"**{period}**: 출석 {summary[period]['출석']}명 / 결석 {summary[period]['결석']}명")

# --- 임시 출석 기록 ---
st.subheader("📝 임시 출석 기록")

if st.button("기록 저장"):
    # 기존 데이터 중 오늘 날짜의 해당 차시와 학생에 대한 것 제거
    for period in periods:
        st.session_state.temp_attendance = st.session_state.temp_attendance[
            ~((st.session_state.temp_attendance["날짜"] == date_str) &
              (st.session_state.temp_attendance["차시"] == period) &
              (st.session_state.temp_attendance["이름"].isin(students)))
        ]

    # 현재 체크 상태를 저장
    new_data = []
    for period in periods:
        for name in students:
            is_regular_absent = any(
                (day == day_name_kr and period in periods_) for (day, periods_) in regular_absents.get(name, [])
            )
            if is_regular_absent:
                status = "정기결석"
                reason = "정기결석"
            else:
                key = f"{date_str}_{period}_{name}"
                checked = st.session_state.check_states.get(key, False)
                status = "결석" if checked else "출석"
                reason_key = f"{key}_reason"
                reason = st.session_state.reasons.get(reason_key, "") if checked else ""

            new_data.append({"날짜": date_str, "이름": name, "차시": period, "상태": status, "사유": reason})

    st.session_state.temp_attendance = pd.concat(
        [st.session_state.temp_attendance, pd.DataFrame(new_data)],
        ignore_index=True
    )

# --- 테이블 출력: 이름은 세로, 차시는 가로 ---
df = st.session_state.temp_attendance
if not df.empty:
    pivot = df.pivot_table(index=["이름"], columns="차시", values=["상태", "사유"], aggfunc="first")
    pivot.columns = [f"{col[1]}_{col[0]}" for col in pivot.columns]  # (상태, 1차시) -> 1차시_상태
    pivot = pivot.reset_index()
    st.dataframe(pivot)
