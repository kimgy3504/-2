import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["홍길동", "김철수", "이영희"]

# 출석 기록을 저장할 데이터프레임 초기화
if "attendance" not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

st.title("📝 출석부 프로그램")

# 날짜 선택
date = st.date_input("출석 날짜", datetime.date.today())

# 필터: 현재 날짜에 이미 기록된 학생 이름 리스트
def get_recorded_names(attendance_df, date):
    if attendance_df.empty:
        return []
    return attendance_df[attendance_df["날짜"] == pd.to_datetime(date).strftime("%Y-%m-%d")]["이름"].tolist()

recorded_names = get_recorded_names(st.session_state.attendance, date)

st.subheader("출석 체크 (결석자만 체크하세요)")

for name in students:
    # 이미 기록된 학생은 체크박스 비활성화 및 상태 표시
    if name in recorded_names:
        # 해당 학생의 상태 가져오기
        state = st.session_state.attendance[
            (st.session_state.attendance["날짜"] == pd.to_datetime(date).strftime("%Y-%m-%d")) & 
            (st.session_state.attendance["이름"] == name)
        ]["상태"].values[0]
        st.write(f"{name}: 이미 '{state}' 처리됨")
        continue

    absent = st.checkbox(f"{name} 결석", key=f"{date}_{name}")
    if absent:
        reason = st.text_input(f"{name}의 결석 사유:", key=f"{date}_{name}_reason")
        if st.button(f"{name} 기록 저장", key=f"{date}_{name}_btn"):
            st.session_state.attendance.loc[len(st.session_state.attendance)] = [date, name, "결석", reason]
            st.success(f"{name} 결석 기록이 저장되었습니다.")
            st.experimental_rerun()
    else:
        if st.button(f"{name} 출석 기록 저장", key=f"{date}_{name}_btn_att"):
            st.session_state.attendance.loc[len(st.session_state.attendance)] = [date, name, "출석", ""]
            st.success(f"{name} 출석 기록이 저장되었습니다.")
            st.experimental_rerun()

st.subheader("📊 출석 기록")
st.dataframe(st.session_state.attendance)
