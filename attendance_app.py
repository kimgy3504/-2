import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["홍길동", "김철수", "이영희"]

# 🔁 정기 결석 요일 설정: {"이름": [요일 번호 리스트]} (0=월, 1=화, ..., 6=일)
regular_absents = {
    "이영희": [2],  # 매주 수요일 결석
    "김철수": [4],  # 매주 금요일 결석
}

# 출석 기록 초기화 및 저장용 데이터프레임 준비
if "attendance" not in st.session_state:
    st.session_state.attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])

st.title("📝 출석부 (결석자만 체크 + 정기 결석 자동 반영)")

# 날짜 선택
date = st.date_input("출석 날짜", datetime.date.today())
date_str = pd.to_datetime(date).strftime("%Y-%m-%d")
weekday = date.weekday()

# 이미 기록된 학생들
recorded_names = st.session_state.attendance[
    st.session_state.attendance["날짜"] == date_str]["이름"].tolist()

st.subheader("🙋‍♂️ 결석자 체크 (정기 결석자는 자동 표시됨)")

absent_students = []
reasons = {}

for name in students:
    if name in recorded_names:
        state = st.session_state.attendance[
            (st.session_state.attendance["날짜"] == date_str) &
            (st.session_state.attendance["이름"] == name)
        ]["상태"].values[0]
        st.markdown(f"✅ **{name}**: 이미 '{state}' 처리됨")
        continue

    # 정기 결석일 자동 처리
    if name in regular_absents and weekday in regular_absents[name]:
        st.markdown(f"❗ **{name}**: 정기 결석일이라 자동 결석 처리됨")
        absent_students.append(name)
        reasons[name] = "정기 결석일"
        continue

    # 수동 결석 체크 및 사유 입력
    is_absent = st.checkbox(f"{name} 결석", key=f"{name}_absent")
    if is_absent:
        absent_students.append(name)
        reasons[name] = st.text_input(f"{name} 결석 사유", key=f"{name}_reason")

# 출석 기록 저장 버튼
if st.button("📌 출석 기록 저장"):
    for name in students:
        if name in recorded_names:
            continue  # 중복 저장 방지

        if name in absent_students:
            reason = reasons.get(name, "")
            st.session_state.attendance.loc[len(st.session_state.attendance)] = [date_str, name, "결석", reason]
        else:
            st.session_state.attendance.loc[len(st.session_state.attendance)] = [date_str, name, "출석", ""]

    st.success("출석 기록이 저장되었습니다.")
    st.rerun()

# 출석 기록 초기화 버튼
if st.button("🧹 출석 기록 초기화 (오늘부터 새로 시작)"):
    st.session_state.attendance = pd.DataFrame(columns=["날짜", "이름", "상태", "사유"])
    st.success("출석 기록이 초기화되었습니다.")
    st.rerun()

# 출석 기록 테이블 표시
st.subheader("📊 출석 기록")
st.dataframe(st.session_state.attendance)

# CSV 다운로드 버튼
if st.download_button("출석부 CSV 다운로드", st.session_state.attendance.to_csv(index=False).encode("utf-8"), "attendance.csv"):
    st.success("다운로드 완료!")
