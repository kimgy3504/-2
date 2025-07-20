import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="출석부", layout="wide")

# 초기 설정
students = ["1.강정원", "2.고민서", "3.권지연", "4.김가령", "7.김예르미", "8.박수빈", "9.송가은", "10.이려흔", "12.임보배", "13.임지예", "15.정지윤", "16.지혜원", "17.최수민", "18.하다빈", "19.한유진"]
periods = ["1차시", "2차시", "3차시", "4차시", "5차시"]
status_options = ["출석", "결석", "지각", "조퇴"]

regular_absents = {
    "4.김가령": [("5차시", ["금"])]
}

DATA_PATH = "./data/attendance_data.csv"  # 상대 경로, data 폴더 밑에 저장

# 폴더 없으면 생성하는 함수
def save_data(df):
    folder = os.path.dirname(DATA_PATH)
    if not os.path.exists(folder):
        os.makedirs(folder)
    df.to_csv(DATA_PATH, index=False)

def load_data():
    if os.path.exists(DATA_PATH):
        return pd.read_csv(DATA_PATH)
    else:
        return pd.DataFrame(columns=["날짜", "이름", "차시", "상태", "사유"])

# 오늘 날짜 선택
selected_date = st.date_input("출석 날짜 선택", value=datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")
weekday_str = selected_date.strftime("%a")
weekday_kor = {
    "Mon": "월", "Tue": "화", "Wed": "수",
    "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
}[weekday_str]

# 출석 체크 초기화
if "check_states" not in st.session_state:
    st.session_state.check_states = {}
if "reasons" not in st.session_state:
    st.session_state.reasons = {}

for period in periods:
    for name in students:
        key = f"{date_str}_{period}_{name}"
        if key not in st.session_state.check_states:
            st.session_state.check_states[key] = False
        if key not in st.session_state.reasons:
            st.session_state.reasons[key] = ""

# 정기 결석 자동 반영
for name, rules in regular_absents.items():
    for period, days in rules:
        if weekday_kor in days:
            key = f"{date_str}_{period}_{name}"
            st.session_state.check_states[key] = True
            st.session_state.reasons[key] = "정기결석"

st.subheader("📋 출석 체크 (결석자만 체크)")

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

# 임시 저장 데이터 로드
attendance_df = load_data()
# students에 없는 이름은 제외
attendance_df = attendance_df[attendance_df["이름"].isin(students)]

# 임시 저장 버튼
if st.button("💾 출석 기록 저장(체크 표시하고 꼭 눌러야 저장 됨!)"):
    # 기존 데이터 중 같은 날짜+학생+차시 삭제
    for period in periods:
        attendance_df = attendance_df[~(
            (attendance_df["날짜"] == date_str) &
            (attendance_df["차시"] == period) &
            (attendance_df["이름"].isin(students))
        )]

    # 새로운 데이터 생성
    new_records = []
    for period in periods:
        for name in students:
            key = f"{date_str}_{period}_{name}"
            if st.session_state.check_states[key]:
                status = "결석"
                reason = st.session_state.reasons[key]
            else:
                status = "출석"
                reason = ""
            new_records.append({
                "날짜": date_str,
                "이름": name,
                "차시": period,
                "상태": status,
                "사유": reason
            })

    attendance_df = pd.concat([attendance_df, pd.DataFrame(new_records)], ignore_index=True)
    save_data(attendance_df)
    st.success("출석 기록이 저장되었습니다!")

if not attendance_df.empty:
    today_df = attendance_df[attendance_df["날짜"] == date_str]
    summary = []

    for period in periods:
        period_df = today_df[today_df["차시"] == period]
        total = len(students)

        # 정기 결석자 이름 집합
        regular_absent_names = set()
        for name, rules in regular_absents.items():
            for p, days in rules:
                if p == period and weekday_kor in days:
                    regular_absent_names.add(name)

        # 출석 처리된 학생 중 정기 결석자 제외
        present_names = set(period_df[period_df["상태"] == "출석"]["이름"])
        actual_present = len(present_names - regular_absent_names)

        # 결석자 (정기 결석 제외)
        absent_names = set(period_df[period_df["상태"] == "결석"]["이름"])
        absent_names_only = absent_names - regular_absent_names

        # 출석률 계산
        possible_present = total - len(regular_absent_names)
        attendance_rate = (
            (actual_present / possible_present) * 100
            if possible_present > 0 else 0
        )

        summary.append({
            "차시": period,
            "자습 총 인원": total,
            "정기 결석": len(regular_absent_names),
            "총원": possible_present,
            "현원": actual_present,
            "결원": len(absent_names_only),
            "결원 번호,이름": ", ".join(sorted(absent_names_only)) if absent_names_only else "-",
            "출석률": f"{attendance_rate:.0f}%"
        })

    st.subheader("📈 자습 인원(칠판에 적을 내용)")
    st.dataframe(pd.DataFrame(summary).set_index("차시"), use_container_width=True)

# 출석 기록 테이블
if not attendance_df.empty:
    today_df = attendance_df[attendance_df["날짜"] == date_str]
    pivot_status = today_df.pivot(index="이름", columns="차시", values="상태").fillna("")
    pivot_reason = today_df.pivot(index="이름", columns="차시", values="사유").fillna("")
    display_df = pivot_status.copy()
    for r in display_df.index:
        for c in display_df.columns:
            status = display_df.loc[r, c]
            reason = pivot_reason.loc[r, c]
            if status == "결석":
                display_df.loc[r, c] = f"❌ {reason}"
            elif status == "출석":
                display_df.loc[r, c] = "✅"
 # 개인별 자습 기록 출력 (students 기준으로만 출력)
st.subheader("📝 개인별 자습 기록")
for student in sorted(students):
