import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["홍길동", "김철수", "이영희"]

# 정기 결석 패턴 설정
# pattern: "once" = 매주 1번, "twice" = 매주 2번
# days: 요일 리스트 (0=월요일, 6=일요일)
regular_absents = {
    "이영희": {"pattern": "once", "days": [2]},       # 매주 수요일 1,2차시 모두 결석
    "김철수": {"pattern": "twice", "days": [1, 3]},  # 매주 화,목 2차시만 결석
}

periods = ["1차시", "2차시"]

st.title("📝 출석부 (1,2차시 분리 + 정기 결석 패턴 반영)")

# 자동 초기화 (하루 한번 초기화)
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

absent_students_period = {period: [] for period in periods}
reasons_period = {period: {} for period in periods}

for period in periods:
    st.markdown(f"### ▶ {period} 출석 체크")
    for name in students:
        absent_auto = False
        reason = ""
        if name in regular_absents:
            info = regular_absents[name]
            if info["pattern"] == "once":
                # 매주 1번: 해당 요일이면 1,2차시 모두 결석
                if weekday in info["days"]:
                    absent_auto = True
                    reason = "정기 결석일 (1,2차시 모두 결석)"
            elif info["pattern"] == "twice":
                # 매주 2번: 해당 요일이고 2차시일 때만 결석
                if weekday in info["days"] and period == "2차시":
                    absent_auto = True
                    reason = "정기 결석일 (2차시 결석)"
        if absent_auto:
            st.markdown(f"❗ **{name}**: {reason} (자동 결석 처리)")
            absent_students_period[period].append(name)
            reasons_period[period][name] = reason
        else:
            absent = st.checkbox(f"{name} 결석 ({period})", key=f"{name}_absent_{period}")
            if absent:
                absent_students_period[period].append(name)
                reasons_period[period][name] = st.text_input(f"{name} 결석 사유 ({period})", key=f"{name}_reason_{period}")

if st.button("💾 임시 출석 기록 저장"):
    if "temp_attendance" not in st.session_state:
        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

    # 기존 데이터 삭제
    for period in periods:
        st.session_state.temp_attendance = st.session_state.temp_attendance[
            ~((st.session_state.temp_attendance["날짜"] == date_str) &
              (st.session_state.temp_attendance["차시"] == period) &
              (st.session_state.temp_attendance["이름"].isin(students)))
        ]

    # 새 데이터 추가
    for period in periods:
        for name in students:
            if name in absent_students_period[period]:
                status = "결석"
                reason = reasons_period[period].get(name, "")
            else:
                status = "출석"
                reason = ""
            st.session_state.temp_attendance.loc[len(st.session_state.temp_attendance)] = [date_str, period, name, status, reason]

    st.success("임시 출석 기록이 저장되었습니다.")

st.subheader("📝 임시 출석 기록 수정")
if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
    st.info("임시 저장된 출석 기록이 없습니다.")
else:
    sorted_temp = st.session_state.temp_attendance.sort_values(by=["날짜", "차시", "이름"]).reset_index(drop=True)
    edited_df = st.data_editor(sorted_temp, num_rows="dynamic", key="temp_editor")
    st.session_state.temp_attendance = edited_df.sort_values(by=["날짜", "차시", "이름"]).reset_index(drop=True)

if st.button("✅ 최종 출석 기록 저장"):
    if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
        st.warning("임시 출석 기록이 없습니다. 저장할 데이터가 없어요.")
    else:
        if "final_attendance" not in st.session_state:
            st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

        # 해당 날짜 데이터 삭제
        st.session_state.final_attendance = st.session_state.final_attendance[
            st.session_state.final_attendance["날짜"] != date_str
        ]

        # 임시 기록 추가
        st.session_state.final_attendance = pd.concat(
            [st.session_state.final_attendance, st.session_state.temp_attendance], ignore_index=True
        )

        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
        st.success("최종 출석 기록이 저장되었습니다.")

st.subheader("📊 최종 출석 기록")
if "final_attendance" not in st.session_state or st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    sorted_final = st.session_state.final_attendance.sort_values(by=["날짜", "차시", "이름"]).reset_index(drop=True)
    edited_final = st.data_editor(sorted_final, num_rows="dynamic", key="final_editor")
    st.session_state.final_attendance = edited_final.sort_values(by=["날짜", "차시", "이름"]).reset_index(drop=True)
