import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["강정원", "고민서", "권지연", "김가령", "김나형", "김예르미", "박수빈", "송가은", "김가령", "이려흔", "이수아", "임보배", "정지윤", "지혜원", "최수민", "하다빈", "한유진"]

# 출석 기록을 저장할 데이터프레임
if "attendance" not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

st.title("📝 출석부 프로그램")

# 날짜 선택
date = st.date_input("출석 날짜", datetime.date.today())

# 출석 체크
st.subheader("출석 체크 (결석자만 체크하세요)")

for name in students:
    absent = st.checkbox(f"{name} 결석", key=name)
    if absent:
        reason = st.text_input(f"{name}의 결석 사유:", key=f"{name}_reason")
        st.session_state.attendance.loc[len(st.session_state.attendance)] = [date, name, "결석", reason]
    else:
        st.session_state.attendance.loc[len(st.session_state.attendance)] = [date, name, "출석", ""]

# 결과 보기
st.subheader("📊 출석 기록")
st.dataframe(st.session_state.attendance)

# 파일로 저장 (선택)
if st.download_button("출석부 CSV 다운로드", st.session_state.attendance.to_csv(index=False).encode("utf-8"), "attendance.csv"):
    st.success("다운로드 완료!")
