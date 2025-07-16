import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["홍길동", "김철수", "이영희"]

# 정기 결석 요일 설정 (0=월, ..., 6=일)
regular_absents = {
    "이영희": [2],  # 매주 수요일 결석
    "김철수": [4],  # 매주 금요일 결석
}

st.title("📝 출석부 (임시 저장 + 수정 기능 포함)")

# 날짜 선택
date = st.date_input("출석 날짜", datetime.date.today())
date_str = date.strftime("%Y-%m-%d")
weekday = date.weekday()

# 초기화: 메모리용 임시 저장 공간
if "temp_attendance" not in st.session_state:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

if "final_attendance" not in st.session_state:
    st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

st.subheader("📋 출석 체크 (결석자만 체크)")

absent_students = []
reasons = {}

for name in students:
    # 정기 결석 자동 처리
    if name in regular_absents and weekday in regular_absents[name]:
        st.markdown(f"❗ **{name}**: 정기 결석일 (자동 결석 처리)")
        absent_students.append(name)
        reasons[name] = "정기 결석일"
        continue

    # 수동 체크
    absent = st.checkbox(f"{name} 결석", key=f"{name}_absent")
    if absent:
        absent_students.append(name)
        reasons[name] = st.text_input(f"{name} 결석 사유", key=f"{name}_reason")

# 임시 저장 버튼
if st.button("💾 임시 출석 기록 저장"):
    # 기존 임시 데이터에서 해당 날짜 이름 제거
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        ~((st.session_state.temp_attendance["날짜"] == date_str) & 
          (st.session_state.temp_attendance["이름"].isin(students)))
    ]
    # 새 데이터 추가
    for name in students:
        if name in absent_students:
            reason = reasons.get(name, "")
            status = "결석"
        else:
            reason = ""
            status = "출석"
        st.session_state.temp_attendance.loc[len(st.session_state.temp_attendance)] = [date_str, name, status, reason]
    st.success("임시 출석 기록이 저장되었습니다.")

# 임시 저장된 기록 보기 및 수정
st.subheader("📝 임시 출석 기록 수정")

if st.session_state.temp_attendance.empty:
    st.info("임시 저장된 출석 기록이 없습니다.")
else:
    edited_df = st.data_editor(st.session_state.temp_attendance, num_rows="dynamic")
    st.session_state.temp_attendance = edited_df

# 최종 저장 버튼
if st.button("✅ 최종 출석 기록 저장"):
    # 기존 최종 데이터에서 해당 날짜 기록 제거
    st.session_state.final_attendance = st.session_state.final_attendance[
        st.session_state.final_attendance["날짜"] != date_str
    ]
    # 임시 기록을 최종 기록에 추가
    st.session_state.final_attendance = pd.concat([st.session_state.final_attendance, st.session_state.temp_attendance])
    # 임시 기록 초기화
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])
    st.success("최종 출석 기록이 저장되었습니다.")

# 최종 출석 기록 보기 및 수정
st.subheader("📊 최종 출석 기록")

if st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    edited_final = st.data_editor(st.session_state.final_attendance, num_rows="dynamic")
    st.session_state.final_attendance = edited_final
