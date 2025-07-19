import streamlit as st
import pandas as pd
from datetime import date
import json

# 날짜 및 요일
today = date.today()
date_str = today.strftime("%Y-%m-%d")
weekday_kor = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

# 초기 설정
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame()

# 학생 목록 및 차시 설정
students = ["김가령", "홍길동", "이영희", "박철수", "최지훈"]
periods = ["1교시", "2교시", "3교시"]

# 정기 결석자 정의
regular_absents = {
    "이영희": [("1교시", ["월", "수", "금"])],
    "박철수": [("2교시", ["화", "목"])],
}

st.title("📚 출석 체크 앱")

# ✍ 출석 입력
st.header("✅ 결석자 입력")
selected_period = st.selectbox("차시 선택", periods)
absentees = st.multiselect("결석자 선택", students, key="absentees")
absent_reasons = {}

for name in absentees:
    absent_reasons[name] = st.text_input(f"{name}의 결석 사유:", key=f"reason_{name}")

# 💾 임시 저장
if st.button("임시 저장"):
    temp_rows = []
    for student in students:
        status = "결석" if student in absentees else "출석"
        reason = absent_reasons.get(student, "") if status == "결석" else ""
        
        # 정기 결석자인 경우는 저장 안 함
        is_regular_absent = any(
            p == selected_period and weekday_kor in days
            for p, days in regular_absents.get(student, [])
        )
        if is_regular_absent:
            continue
        
        temp_rows.append({
            "날짜": date_str,
            "이름": student,
            "차시": selected_period,
            "상태": status,
            "사유": reason,
        })

    if not st.session_state.temp_attendance.empty:
        st.session_state.temp_attendance = pd.concat(
            [st.session_state.temp_attendance, pd.DataFrame(temp_rows)],
            ignore_index=True
        )
    else:
        st.session_state.temp_attendance = pd.DataFrame(temp_rows)
    st.success("임시 저장 완료!")

# 📄 임시 출석 기록 표시
if not st.session_state.temp_attendance.empty:
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]

    pivot = today_df.pivot(index="이름", columns="차시", values="상태").fillna("")
    reason_pivot = today_df.pivot(index="이름", columns="차시", values="사유").fillna("")
    display_df = pivot.copy()

    for row in display_df.index:
        for col in display_df.columns:
            status = pivot.loc[row, col]
            reason = reason_pivot.loc[row, col]
            if status == "결석":
                display_df.loc[row, col] = f"❌ {reason}"
            elif status == "출석":
                display_df.loc[row, col] = "✅"

    # 순서 맞추기
    display_df = display_df.reindex(students)
    st.subheader("📝 임시 출석 기록")
    st.dataframe(display_df, use_container_width=True)

# 📈 출석 요약 정보
if not st.session_state.temp_attendance.empty:
    summary_data = []
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]

    for period in periods:
        period_df = today_df[today_df["차시"] == period]

        # 정기 결석자 명단
        regular_absent_keys = {
            name for name, rules in regular_absents.items()
            for p, days in rules
            if p == period and weekday_kor in days
        }

        # 실제 결석자 명단 (정기 결석 제외)
        actual_absentees = period_df[
            (period_df["상태"] == "결석") & (~period_df["이름"].isin(regular_absent_keys))
        ]["이름"].tolist()

        total = len(students) - len(regular_absent_keys)
        present = len(period_df[period_df["상태"] == "출석"])
        absent = len(actual_absentees)
        attendance_rate = f"{(present / total * 100):.0f}%" if total > 0 else "0%"

        summary_data.append({
            "차시": period,
            "총원": total,
            "출석자 수": present,
            "결석자 수": absent,
            "정기 결석자 수": len(regular_absent_keys),
            "결석자 명단": ", ".join(actual_absentees),
            "출석률": attendance_rate
        })

    st.subheader("📈 차시별 출석 요약 정보 (정기 결석자 제외)")
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

if st.button("📌 출석 최종 저장"):
    # 여기에 Google Sheets 저장 또는 파일 저장 로직 추가 가능
    st.success("출석 정보가 저장되었습니다.")
    # 저장 후 임시 데이터 초기화
    st.session_state.temp_attendance = pd.DataFrame()
