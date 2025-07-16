import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["홍길동", "김철수", "이영희"]

# 출석 기록을 저장할 데이터프레임
if "attendance" not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

st.title("📝 출석부 프로그램")

# 날짜 선택
date = st.date_input("출석 날짜", datetime.date.today())
date_str = pd.to_datetime(date).strftime("%Y-%m-%d")

# 이미 기록된 이름 리스트
def get_recorded_names(attendance_df, date_str):
    return attendance_df[attendance_df["날짜"] == date_str]["이름"].tolist()

recorded_names = get_recorded_names(st.session_state.attendance, date_str)

st.subheader("✅ 출석 체크")

# 이름 선택
name = st.selectbox("이름을 선택하세요", [""] + students)

if name:
    if name in recorded_names:
        # 이미 기록된 경우
        state = st.session_state.attendance[
            (st.session_state.attendance["날짜"] == date_str) &
            (st.session_state.attendance["이름"] == name)
        ]["상태"].values[0]
        st.info(f"{name}님은 이미 '{state}'으로 처리되었습니다.")
    else:
        # 결석 여부 체크
        is_absent = st.radio("상태 선택", ["출석", "결석"], key=f"radio_{name}")
        reason = ""
        if is_absent == "결석":
            reason = st.text_input("결석 사유를 입력해주세요", key=f"reason_{name}")

        if st.button("기록 저장"):
            st.session_state.attendance.loc[len(st.session_state.attendance)] = [date_str, name, is_absent, reason]
            st.success(f"{name}님의 '{is_absent}' 기록이 저장되었습니다.")
            st.experimental_rerun()

# 출석 기록 보기
st.subheader("📊 출석 기록")
st.dataframe(st.session_state.attendance)

# CSV 다운로드
if st.download_button("출석부 CSV 다운로드", st.session_state.attendance.to_csv(index=False).encode("utf-8"), "attendance.csv"):
    st.success("다운로드 완료!")
