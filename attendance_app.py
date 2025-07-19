import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="출석부", layout="wide")

# 초기 설정
students = ["1.강정원", "2.고민서", "3.권지연", "4.김가령", "7.김예르미", "8.박수빈", "9.송가은", "10.이려흔", "12.임보배", "13.임지예", "15.정지윤", "16.지혜원", "17.최수민", "18.하다빈", "19.한유진"]
periods = ["1차시", "2차시", "3차시", "4차시", "5차시"]
status_options = ["출석", "결석", "지각", "조퇴"]
regular_absents = {
    "4.김가령": [("5차시", ["금"])]      # 매주 금요일 5차시 결석
}

# 오늘 날짜 선택
selected_date = st.date_input("출석 날짜 선택", value=datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")
weekday_str = selected_date.strftime("%a")  # 요일 (Mon, Tue,...)
weekday_kor = {
    "Mon": "월", "Tue": "화", "Wed": "수",
    "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
}[weekday_str]

# 출석 체크 초기화
if "check_states" not in st.session_state:
    st.session_state.check_states = {}

if "reasons" not in st.session_state:
    st.session_state.reasons = {}

# 이전 날짜 저장용
if "last_date" not in st.session_state:
    st.session_state.last_date = None

# --- 날짜가 바뀌면 체크 상태 초기화 및 정기 결석 자동 반영 ---
if "last_date" not in st.session_state:
    st.session_state.last_date = None

if st.session_state.last_date != date_str:
    # 상태 초기화
    for period in periods:
        for name in students:
            key = f"{date_str}_{period}_{name}"
            st.session_state.check_states[key] = False
            st.session_state.reasons[key] = ""
    # 정기 결석 자동 반영
    for name, rules in regular_absents.items():
        for period, days in rules:
            if weekday_kor in days:
                key = f"{date_str}_{period}_{name}"
                st.session_state.check_states[key] = True
                st.session_state.reasons[key] = "정기결석"

    st.session_state.last_date = date_str



# 체크박스 테이블
for period in periods:
    st.markdown(f"### {period}")
    cols = st.columns(len(students))
    for i, name in enumerate(students):
        key = f"{date_str}_{period}_{name}"
        with cols[i]:
            st.session_state.check_states[key] = st.checkbox(
                name,
                value=st.session_state.check_states.get(key, False),
                key=key
            )
            if st.session_state.check_states[key]:
                st.session_state.reasons[key] = st.text_input(
                    f"사유({name})",
                    value=st.session_state.reasons.get(key, ""),
                    key=f"reason_{key}"
                )
            else:
                st.session_state.reasons[key] = ""

# 임시 출석 기록 저장
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame(
        columns=["날짜", "이름", "차시", "상태", "사유"]
    )

# 출석 저장 버튼
if st.button("💾 임시 출석 기록"):
    # 날짜와 학생, 차시에 맞는 기존 데이터 삭제
    for period in periods:
        st.session_state.temp_attendance = st.session_state.temp_attendance[
            ~((st.session_state.temp_attendance["날짜"] == date_str) &
              (st.session_state.temp_attendance["차시"] == period) &
              (st.session_state.temp_attendance["이름"].isin(students)))
        ]

    # 새로 체크된 항목 저장
    new_data = []
    for period in periods:
        for name in students:
            key = f"{date_str}_{period}_{name}"
            if st.session_state.check_states[key]:
                reason = st.session_state.reasons[key]
                new_data.append({
                    "날짜": date_str,
                    "이름": name,
                    "차시": period,
                    "상태": "결석",
                    "사유": reason
                })
            else:
                new_data.append({
                    "날짜": date_str,
                    "이름": name,
                    "차시": period,
                    "상태": "출석",
                    "사유": ""
                })

    st.session_state.temp_attendance = pd.concat([
        st.session_state.temp_attendance,
        pd.DataFrame(new_data)
    ], ignore_index=True)

# 📈 차시별 출석 요약 정보
if not st.session_state.temp_attendance.empty:
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]

        summary_data = []
    for period in periods:
        period_df = today_df[today_df["차시"] == period]

        # 정기 결석자 명단
        regular_absent_keys = set()
        for name, rules in regular_absents.items():
            for p, days in rules:
                if p == period and weekday_kor in days:
                    regular_absent_keys.add(name)
        regular_absent_count = len(regular_absent_keys)

        total = len(students) - regular_absent_count  # 총원 = 학생수 - 정기 결석자 수

        present = len(period_df[period_df["상태"] == "출석"])
        absent = len(period_df[period_df["상태"] == "결석"])
        actual_present = present  # 실제 출석자 = 출석자 수 (정기 결석자는 결석에 포함 안 시켰으니 그대로)

        attendance_rate = (
            f"{(actual_present / total * 100):.0f}%" if total > 0 else "0%"
        )

        summary_data.append({
            "차시": period,
            "총원": total,
            "출석자 수": present,
            "결석자 수": absent,
            "정기 결석자 수": regular_absent_count,
            "실제 출석자 수": actual_present,
            "출석률": attendance_rate
        })

    st.subheader("📈 차시별 출석 요약 정보 (총원 = 학생수 - 정기 결석자)")
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)


# 📝 출석 기록 테이블 (가로: 차시, 세로: 이름)
if not st.session_state.temp_attendance.empty:
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]
    pivot = today_df.pivot(index="이름", columns="차시", values="상태").fillna("")
    reason_pivot = today_df.pivot(index="이름", columns="차시", values="사유").fillna("")
    display_df = pivot.copy()
    for row in display_df.index:
        for col in display_df.columns:
            status = display_df.loc[row, col]
            reason = reason_pivot.loc[row, col]
            if status == "결석":
                display_df.loc[row, col] = f"❌ {reason}"
            elif status == "출석":
                display_df.loc[row, col] = "✅"
    st.subheader("📄 임시 출석 기록")
    st.dataframe(display_df, use_container_width=True)

