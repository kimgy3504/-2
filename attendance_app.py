import streamlit as st
import pandas as pd
import datetime
import os

st.set_page_config(page_title="출석부", layout="wide")

DATA_PATH = "/mnt/data/attendance_data.csv"  # 서버에서 저장할 경로 (환경에 따라 조정)

# 초기 설정
students = ["김가령", "이지은", "박서준", "최수빈", "정우성"]
periods = ["1차시", "2차시", "3차시", "4차시", "5차시"]
status_options = ["출석", "결석", "지각", "조퇴"]

regular_absents = {
    "김가령": [("2차시", ["월", "수"])],          # 매주 월, 수요일 2차시 결석
    "이지은": [("1차시", ["금"]), ("2차시", ["금"])],  # 매주 금요일 1,2차시 결석
    "정우성": [("1차시", ["화", "수", "목"])],     # 매주 화, 수, 목 1차시 결석
}

weekday_map = {
    "Mon": "월", "Tue": "화", "Wed": "수",
    "Thu": "목", "Fri": "금", "Sat": "토", "Sun": "일"
}

# CSV 파일 불러오기 함수
def load_data():
    if os.path.exists(DATA_PATH):
        df = pd.read_csv(DATA_PATH)
        # 날짜 형식 보장
        if "날짜" in df.columns:
            df["날짜"] = pd.to_datetime(df["날짜"]).dt.date
        return df
    else:
        return pd.DataFrame(columns=["날짜", "이름", "차시", "상태", "사유"])

# CSV 파일 저장 함수
def save_data(df):
    df.to_csv(DATA_PATH, index=False)

# 오늘 날짜 선택
selected_date = st.date_input("출석 날짜 선택", value=datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")
weekday_kor = weekday_map[selected_date.strftime("%a")]

# 출석 데이터 불러오기
attendance_df = load_data()

# 해당 날짜 데이터 필터링
today_df = attendance_df[attendance_df["날짜"] == selected_date]

# 출석 체크 상태 초기화 (체크박스용)
if "check_states" not in st.session_state:
    st.session_state.check_states = {}
if "reasons" not in st.session_state:
    st.session_state.reasons = {}

# 초기 체크박스 상태 세팅 (결석은 True, 출석은 False)
for period in periods:
    for name in students:
        key = f"{date_str}_{period}_{name}"
        # 기존 임시 상태가 없으면 초기화
        if key not in st.session_state.check_states:
            # 오늘 데이터에서 기존 상태 찾아서 초기화
            row = today_df[(today_df["이름"] == name) & (today_df["차시"] == period)]
            if not row.empty:
                is_absent = row.iloc[0]["상태"] == "결석"
                st.session_state.check_states[key] = is_absent
                st.session_state.reasons[key] = row.iloc[0]["사유"]
            else:
                st.session_state.check_states[key] = False
                st.session_state.reasons[key] = ""

# 정기 결석 자동 반영 (임시 상태에 강제로 적용)
for name, rules in regular_absents.items():
    for period_rule, days in rules:
        if weekday_kor in days:
            key = f"{date_str}_{period_rule}_{name}"
            st.session_state.check_states[key] = True
            st.session_state.reasons[key] = "정기결석"

st.subheader("📋 출석 체크 (결석자만 체크)")

# 차시별 출석 체크 UI
for period in periods:
    st.markdown(f"### {period}")
    cols = st.columns(len(students))
    for i, name in enumerate(students):
        key = f"{date_str}_{period}_{name}"
        with cols[i]:
            checked = st.checkbox(
                label=name,
                value=st.session_state.check_states.get(key, False),
                key=key
            )
            st.session_state.check_states[key] = checked
            if checked:
                reason = st.text_input(
                    label=f"사유({name})",
                    value=st.session_state.reasons.get(key, ""),
                    key=f"reason_{key}"
                )
                st.session_state.reasons[key] = reason
            else:
                st.session_state.reasons[key] = ""

# 임시 저장 버튼
if st.button("💾 임시 출석 기록 저장"):
    # 기존 데이터에서 오늘 날짜+학생+차시 데이터 삭제
    attendance_df = attendance_df[
        ~(
            (attendance_df["날짜"] == selected_date) &
            (attendance_df["이름"].isin(students)) &
            (attendance_df["차시"].isin(periods))
        )
    ]

    # 새 데이터 추가
    new_records = []
    for period in periods:
        for name in students:
            key = f"{date_str}_{period}_{name}"
            is_absent = st.session_state.check_states.get(key, False)
            reason = st.session_state.reasons.get(key, "")
            status = "결석" if is_absent else "출석"
            new_records.append({
                "날짜": selected_date,
                "이름": name,
                "차시": period,
                "상태": status,
                "사유": reason if is_absent else ""
            })

    new_df = pd.DataFrame(new_records)

    attendance_df = pd.concat([attendance_df, new_df], ignore_index=True)
    save_data(attendance_df)
    st.success("임시 출석 기록이 저장되었습니다!")

# 📈 차시별 출석 요약 정보 계산 및 표시
summary_data = []
for period in periods:
    period_df = attendance_df[
        (attendance_df["날짜"] == selected_date) &
        (attendance_df["차시"] == period)
    ]
    total_students = len(students)
    # 정기 결석자 이름 집합
    regular_absent_names = set()
    for name, rules in regular_absents.items():
        for p, days in rules:
            if p == period and weekday_kor in days:
                regular_absent_names.add(name)

    # 출석자 이름 집합 (상태가 출석인 학생)
    present_names = set(period_df[period_df["상태"] == "출석"]["이름"])

    # 실제 출석자 = 출석자 - 정기 결석자
    actual_present_names = present_names - regular_absent_names
    actual_present = len(actual_present_names)

    # 결석자 수 (정기 결석자 제외)
    absent_names = set(period_df[period_df["상태"] == "결석"]["이름"]) - regular_absent_names
    absent = len(absent_names)

    attendance_rate = (actual_present / (total_students - len(regular_absent_names)) * 100) if (total_students - len(regular_absent_names)) > 0 else 0

    summary_data.append({
        "차시": period,
        "총원(학생수-정기결석자)": total_students - len(regular_absent_names),
        "출석자 수": len(present_names),
        "결석자 수": absent,
        "정기 결석자 수": len(regular_absent_names),
        "실제 출석자 수": actual_present,
        "출석률": f"{attendance_rate:.0f}%",
        "결석하는 사람들": ", ".join(sorted(absent_names)) if absent_names else "-"
    })

st.subheader("📈 차시별 출석 요약 정보")
st.dataframe(pd.DataFrame(summary_data).set_index("차시"), use_container_width=True)

# 📝 출석 기록 테이블 (가로: 차시, 세로: 이름)
if not attendance_df.empty:
    today_df = attendance_df[attendance_df["날짜"] == selected_date]
    pivot_status = today_df.pivot(index="이름", columns="차시", values="상태").fillna("")
    pivot_reason = today_df.pivot(index="이름", columns="차시", values="사유").fillna("")
    display_df = pivot_status.copy()

    for row in display_df.index:
        for col in display_df.columns:
            status = display_df.loc[row, col]
            reason = pivot_reason.loc[row, col]
            if status == "결석":
                display_df.loc[row, col] = f"❌ {reason}"
            elif status == "출석":
                display_df.loc[row, col] = "✅"

    st.subheader("📄 임시 출석 기록")
    st.dataframe(display_df, use_container_width=True)
