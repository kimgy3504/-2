import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="출석부", layout="wide")

# 초기 설정
students = ["김가령", "이지은", "박서준", "최수빈", "정우성"]
periods = ["1차시", "2차시", "3차시", "4차시", "5차시"]
status_options = ["출석", "결석", "지각", "조퇴"]

# 정기 결석 예시 (학생명: [(차시, [요일 목록])] )
regular_absents = {
    "김가령": [("2차시", ["월", "수"])],         # 매주 월, 수요일 2차시 결석
    "이지은": [("1차시", ["금"]), ("2차시", ["금"])], # 매주 금요일 1,2차시 결석
    "정우성": [("1차시", ["화", "수", "목"])],    # 매주 화, 수, 목 1차시 결석
}

# 오늘 날짜 선택
selected_date = st.date_input("출석 날짜 선택", value=datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")
weekday_str = selected_date.strftime("%a")  # 요일 영어 약어 (Mon, Tue, ...)
weekday_kor = {
    "Mon": "월", "Tue": "화", "Wed": "수",
    "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
}[weekday_str]
pretty_date = selected_date.strftime("%Y년 %m월 %d일")

# 출석 체크 초기화 (날짜 바뀌면 초기화됨)
if "check_states" not in st.session_state:
    st.session_state.check_states = {}

if "reasons" not in st.session_state:
    st.session_state.reasons = {}

for period in periods:
    for name in students:
        key = f"{date_str}_{period}_{name}"
        # 날짜 바뀌면 상태 초기화
        if key not in st.session_state.check_states:
            st.session_state.check_states[key] = False
        if key not in st.session_state.reasons:
            st.session_state.reasons[key] = ""

# 정기 결석 자동 반영
regular_checked = set()
for name, rules in regular_absents.items():
    for period, days in rules:
        if weekday_kor in days:
            key = f"{date_str}_{period}_{name}"
            st.session_state.check_states[key] = True
            st.session_state.reasons[key] = "정기결석"
            regular_checked.add(key)

st.subheader(f"📋 출석 체크 (결석자만 체크) - {pretty_date} ({weekday_kor})")

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

# 임시 출석 기록 저장 초기화
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame(
        columns=["날짜", "이름", "차시", "상태", "사유"]
    )

# 출석 저장 버튼
if st.button("💾 임시 출석 기록"):
    # 기존 해당 날짜+학생+차시 데이터 삭제
    for period in periods:
        st.session_state.temp_attendance = st.session_state.temp_attendance[
            ~(
                (st.session_state.temp_attendance["날짜"] == date_str) &
                (st.session_state.temp_attendance["차시"] == period) &
                (st.session_state.temp_attendance["이름"].isin(students))
            )
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

# 📈 차시별 출석 요약 정보 (임시 저장 위에 표시)
if not st.session_state.temp_attendance.empty:
    df = st.session_state.temp_attendance
    today_df = df[df["날짜"] == date_str]

    summary_data = []
    for period in periods:
        period_df = today_df[today_df["차시"] == period]
        total = len(students)

        # 정기 결석자 이름 집합
        regular_absent_names = set()
        for name, rules in regular_absents.items():
            for p, days in rules:
                if p == period and weekday_kor in days:
                    regular_absent_names.add(name)

        # 출석자 이름 집합
        present_names = set(period_df[period_df["상태"] == "출석"]["이름"])

        # 실제 출석자 = 출석자 - 정기 결석자
        actual_present_names = present_names - regular_absent_names
        actual_present = len(actual_present_names)

        # 결석자 중 정기 결석자 제외
        absent_names = set(period_df[period_df["상태"] == "결석"]["이름"])
        absent_names_actual = absent_names - regular_absent_names
        absent = len(absent_names_actual)

        attendance_rate = (
            (actual_present / (total - len(regular_absent_names))) * 100
            if (total - len(regular_absent_names)) > 0 else 0
        )

        summary_data.append({
            "차시": period,
            "총 학생 수": total,
            "출석자 수": len(present_names),
            "정기 결석자 수": len(regular_absent_names),
            "실제 출석자 수": actual_present,
            "결석자 수": absent,
            "결석하는 사람": ", ".join(sorted(absent_names_actual)),
            "출석률": f"{attendance_rate:.0f}%"
        })

    st.subheader(f"📈 차시별 출석 요약 정보 - {pretty_date} ({weekday_kor})")
    summary_df = pd.DataFrame(summary_data).set_index("차시")
    st.dataframe(summary_df, use_container_width=True)

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
    st.subheader(f"📄 임시 출석 기록 - {pretty_date} ({weekday_kor})")
    st.dataframe(display_df, use_container_width=True)
