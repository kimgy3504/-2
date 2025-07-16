import streamlit as st
import pandas as pd
import datetime

students = ["홍길동", "김철수", "이영희"]
periods = ["1차시", "2차시"]

regular_absents = {
    "이영희": {"pattern": "once", "days": [2]},       # 매주 수요일 1,2차시 모두 결석
    "김철수": {"pattern": "twice", "days": [1, 3]},  # 매주 화,목 2차시만 결석
}

st.title("📝 출석부 (1,2차시 분리 + 정기 결석 패턴 반영)")

today = datetime.date.today()
last_date = st.session_state.get("last_date", None)
if last_date != today:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.last_date = today

date = st.date_input("출석 날짜", today)
date_str = date.strftime("%Y-%m-%d")
weekday = date.weekday()

st.subheader("📋 출석 체크 (결석자만 체크)")

absent_students = {name: {period: False for period in periods} for name in students}
reasons = {name: {period: "" for period in periods} for name in students}

for name in students:
    cols = st.columns([1, 1, 1, 3, 3])  # 이름, 1차시 체크, 2차시 체크, 1차시 사유, 2차시 사유
    with cols[0]:
        st.write(f"**{name}**")
    for i, period in enumerate(periods):
        auto_absent = False
        auto_reason = ""
        if name in regular_absents:
            info = regular_absents[name]
            if info["pattern"] == "once" and weekday in info["days"]:
                auto_absent = True
                auto_reason = "정기 결석 (1,2차시 모두 결석)"
            elif info["pattern"] == "twice" and weekday in info["days"] and period == "2차시":
                auto_absent = True
                auto_reason = "정기 결석 (2차시 결석)"

        key_checkbox = f"{name}_absent_{period}"
        key_reason = f"{name}_reason_{period}"

        if auto_absent:
            st.checkbox(f"{period} 결석", key=key_checkbox, value=True, disabled=True)
            absent_students[name][period] = True
            with cols[3+i]:
                st.text(auto_reason)
                reasons[name][period] = auto_reason
        else:
            with cols[1+i]:
                absent = st.checkbox(f"{period} 결석", key=key_checkbox)
                absent_students[name][period] = absent
            with cols[3+i]:
                if absent_students[name][period]:
                    reason = st.text_input(f"{name} {period} 결석 사유", key=key_reason)
                    reasons[name][period] = reason
                else:
                    reasons[name][period] = ""

if st.button("💾 임시 출석 기록 저장"):
    if "temp_attendance" not in st.session_state:
        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

    # 기존 데이터 삭제 (해당 날짜)
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        st.session_state.temp_attendance["날짜"] != date_str
    ]

    # 새 데이터 추가
    for name in students:
        for period in periods:
            status = "결석" if absent_students[name][period] else "출석"
            reason = reasons[name][period] if absent_students[name][period] else ""
            st.session_state.temp_attendance.loc[len(st.session_state.temp_attendance)] = [date_str, period, name, status, reason]

    st.success("임시 출석 기록이 저장되었습니다.")

def pivot_attendance(df):
    if df.empty:
        return df
    pivoted = df.pivot_table(
        index=["날짜", "이름"],
        columns="차시",
        values=["상태", "사유"],
        aggfunc='first',
        fill_value=""
    )
    pivoted.columns = [f"{col2} {col1}" for col1, col2 in pivoted.columns]
    pivoted = pivoted.reset_index()
    pivoted = pivoted.sort_values(by=["날짜", "이름"]).reset_index(drop=True)
    return pivoted

st.subheader("📝 임시 출석 기록 수정 (학생별 1줄, 1,2차시 분리)")

if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
    st.info("임시 저장된 출석 기록이 없습니다.")
else:
    pivot_temp = pivot_attendance(st.session_state.temp_attendance)
    edited_pivot = st.data_editor(pivot_temp, num_rows="dynamic", key="temp_pivot_editor")

    rows = []
    for _, row in edited_pivot.iterrows():
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

if st.button("✅ 최종 출석 기록 저장"):
    if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
        st.warning("임시 출석 기록이 없습니다. 저장할 데이터가 없어요.")
    else:
        if "final_attendance" not in st.session_state:
            st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

        st.session_state.final_attendance = st.session_state.final_attendance[
            st.session_state.final_attendance["날짜"] != date_str
        ]

        st.session_state.final_attendance = pd.concat(
            [st.session_state.final_attendance, st.session_state.temp_attendance], ignore_index=True
        )

        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
        st.success("최종 출석 기록이 저장되었습니다.")

st.subheader("📊 최종 출석 기록 (학생별 1줄, 1,2차시 분리)")

if "final_attendance" not in st.session_state or st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    pivot_final = pivot_attendance(st.session_state.final_attendance)
    edited_final_pivot = st.data_editor(pivot_final, num_rows="dynamic", key="final_pivot_editor")

    rows = []
    for _, row in edited_final_pivot.iterrows():
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
