import streamlit as st
import pandas as pd
from datetime import datetime
import json

# ----------------- 설정 -----------------

students = ["홍길동", "김철수", "이영희", "박지민", "최수정"]
periods = ["1교시", "2교시", "3교시"]

# 정기 결석 정보
regular_absents = {
    "최수정": [("1교시", ["월", "수"]), ("2교시", ["금"])]
}

# ----------------- 초기화 -----------------

if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame()

# ----------------- 날짜 및 요일 -----------------

today = datetime.now()
date_str = today.strftime("%Y-%m-%d")
weekday_kor = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

# ----------------- 출석 입력 -----------------

st.title("📝 출석 체크")
name = st.selectbox("이름을 선택하세요", students)
period = st.selectbox("차시를 선택하세요", periods)
status = st.radio("출석 상태", ("출석", "결석"))
reason = ""

# 정기 결석자면 사유 자동 처리
is_regular_absent = False
if name in regular_absents:
    for p, days in regular_absents[name]:
        if p == period and weekday_kor in days:
            is_regular_absent = True
            reason = "정기 결석"
            break

if not is_regular_absent and status == "결석":
    reason = st.text_input("결석 사유를 입력하세요")

if st.button("✅ 임시 출석 기록에 추가"):
    new_row = pd.DataFrame([{
        "날짜": date_str,
        "이름": name,
        "차시": period,
        "상태": status,
        "사유": reason
    }])
    st.session_state.temp_attendance = pd.concat([st.session_state.temp_attendance, new_row], ignore_index=True)

# ----------------- 차시별 요약 -----------------

if not st.session_state.temp_attendance.empty:
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]

    summary_data = []
    for p in periods:
        period_df = today_df[today_df["차시"] == p]

        # 정기 결석자 추출
        regular_absent_keys = set()
        for name, rules in regular_absents.items():
            for rp, days in rules:
                if rp == p and weekday_kor in days:
                    regular_absent_keys.add(name)
        regular_absent_count = len(regular_absent_keys)

        total = len(students) - regular_absent_count
        period_absentees = period_df[(period_df["상태"] == "결석") & (~period_df["이름"].isin(regular_absent_keys))]
        absent_names = list(period_absentees["이름"])
        present = len(period_df[period_df["상태"] == "출석"])
        actual_present = present
        absent = len(absent_names)
        attendance_rate = f"{(actual_present / total * 100):.0f}%" if total > 0 else "0%"

        summary_data.append({
            "차시": p,
            "총원": total,
            "출석자 수": present,
            "결석자 수": absent,
            "정기 결석자 수": regular_absent_count,
            "결석자 명단": ", ".join(absent_names),
            "출석률": attendance_rate
        })

    st.subheader("📈 차시별 출석 요약 정보")
    st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

# ----------------- 임시 출석 기록 -----------------

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

    # 입력 순서대로 정렬
    display_df = display_df.reindex(st.session_state.temp_attendance["이름"].drop_duplicates(), fill_value="")

    st.subheader("🗂️ 임시 출석 기록 (수정용)")
    st.dataframe(display_df, use_container_width=True)

# ----------------- 저장 기능 -----------------

if st.button("📌 출석 최종 저장"):
    # 여기에 Google Sheets 저장 또는 파일 저장 로직 추가 가능
    st.success("출석 정보가 저장되었습니다.")
    # 저장 후 임시 데이터 초기화
    st.session_state.temp_attendance = pd.DataFrame()
