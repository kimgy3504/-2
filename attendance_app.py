import streamlit as st
import pandas as pd
import datetime

# 기본 설정
students = ["홍길동", "김철수", "이영희"]
periods = ["1차시", "2차시"]

# 정기 결석 설정 예시 (패턴을 리스트로 지정)
regular_absents = {
    "이영희": [("both", [2])],         # 매주 수요일 1,2차시 모두 결석
    "김철수": [("2nd_only", [1, 3])],   # 매주 화,목 2차시만 결석
}

# 자동 초기화
today = datetime.date.today()
last_date = st.session_state.get("last_date", None)

# 날짜 변경 시: 상태 초기화 + 키 초기화
if last_date != today:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.last_date = today

    for name in students:
        for period in periods:
            cb_key = f"{name}_absent_{period}"
            reason_key = f"{name}_reason_{period}"
            st.session_state.pop(cb_key, None)
            st.session_state.pop(reason_key, None)

# 날짜 선택
date = st.date_input("출석 날짜", today)
date_str = date.strftime("%Y-%m-%d")
weekday = date.weekday()

st.title("📝 출석부 (1,2차시 + 정기 결석 + 요약 정보)")

st.subheader("📋 출석 체크 (결석자만 체크)")

# 결석자 기록용 딕셔너리
absent_students = {name: {period: False for period in periods} for name in students}
reasons = {name: {period: "" for period in periods} for name in students}

# 출석 체크 UI
for name in students:
    cols = st.columns([1, 1, 1, 3, 3])
    with cols[0]:
        st.write(f"**{name}**")
    for i, period in enumerate(periods):
        auto_absent = False
        auto_reason = ""

        # 정기 결석 자동 처리
        if name in regular_absents:
            for pattern, days in regular_absents[name]:
                if weekday in days:
                    if pattern == "both":
                        auto_absent = True
                        auto_reason = "정기 결석 (1,2차시)"
                    elif pattern == "2nd_only" and period == "2차시":
                        auto_absent = True
                        auto_reason = "정기 결석 (2차시)"

        cb_key = f"{name}_absent_{period}"
        reason_key = f"{name}_reason_{period}"

        if auto_absent:
            with cols[1 + i]:
                st.checkbox(f"{period} 결석", value=True, disabled=True, key=cb_key)
            with cols[3 + i]:
                st.text(auto_reason)
            absent_students[name][period] = True
            reasons[name][period] = auto_reason
        else:
            with cols[1 + i]:
                absent = st.checkbox(f"{period} 결석", key=cb_key)
                absent_students[name][period] = absent
            with cols[3 + i]:
                if absent_students[name][period]:
                    reason = st.text_input(f"{name} {period} 결석 사유", key=reason_key)
                    reasons[name][period] = reason

# 임시 저장
if st.button("💾 임시 출석 기록 저장"):
    if "temp_attendance" not in st.session_state:
        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

    # 기존 해당 날짜 삭제
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        st.session_state.temp_attendance["날짜"] != date_str
    ]

    # 새로 추가
    for name in students:
        for period in periods:
            status = "결석" if absent_students[name][period] else "출석"
            reason = reasons[name][period] if absent_students[name][period] else ""
            st.session_state.temp_attendance.loc[len(st.session_state.temp_attendance)] = [
                date_str, period, name, status, reason
            ]
    st.success("✅ 임시 출석 기록이 저장되었습니다.")

# -------------------------------
# ✅ 출석 요약 정보
# -------------------------------
def show_summary(df):
    if df.empty:
        return
    st.subheader("📈 출석 요약 정보")
    grouped = df.groupby(["날짜", "차시", "상태"]).size().unstack(fill_value=0)
    for (날짜, 차시), row in grouped.iterrows():
        출석 = row.get("출석", 0)
        결석 = row.get("결석", 0)
        st.markdown(f"- **{날짜} {차시}** → ✅ 출석: {출석}명 / ❌ 결석: {결석}명")

# -------------------------------
# ✅ 임시 출석 기록 표시 및 수정
# -------------------------------
st.subheader("📝 임시 출석 기록 수정")

if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
    st.info("임시 저장된 출석 기록이 없습니다.")
else:
    show_summary(st.session_state.temp_attendance)

    # 학생별 1줄 피벗
    def pivot_attendance(df):
        if df.empty:
            return df
        pivoted = df.pivot_table(
            index=["날짜", "이름"],
            columns="차시",
            values=["상태", "사유"],
            aggfunc="first",
            fill_value=""
        )
        pivoted.columns = [f"{col2} {col1}" for col1, col2 in pivoted.columns]
        return pivoted.reset_index().sort_values(by=["날짜", "이름"])

    pivot_temp = pivot_attendance(st.session_state.temp_attendance)
    edited_temp = st.data_editor(pivot_temp, num_rows="dynamic", key="temp_editor")

    # 다시 풀어서 저장
    rows = []
    for _, row in edited_temp.iterrows():
        for period in periods:
            상태 = row.get(f"{period} 상태", "")
            사유 = row.get(f"{period} 사유", "")
            rows.append({
                "날짜": row["날짜"],
                "이름": row["이름"],
                "차시": period,
                "상태": 상태,
                "사유": 사유
            })
    st.session_state.temp_attendance = pd.DataFrame(rows)

# -------------------------------
# ✅ 최종 출석 기록 저장
# -------------------------------
if st.button("✅ 최종 출석 기록 저장"):
    if "final_attendance" not in st.session_state:
        st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

    # 현재 날짜 삭제 후 병합
    st.session_state.final_attendance = st.session_state.final_attendance[
        st.session_state.final_attendance["날짜"] != date_str
    ]

    st.session_state.final_attendance = pd.concat([
        st.session_state.final_attendance,
        st.session_state.temp_attendance
    ], ignore_index=True)

    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.success("🎉 최종 출석 기록이 저장되었습니다.")

# -------------------------------
# ✅ 최종 출석 기록 보기
# -------------------------------
st.subheader("📊 최종 출석 기록")

if "final_attendance" not in st.session_state or st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    pivot_final = pivot_attendance(st.session_state.final_attendance)
    edited_final = st.data_editor(pivot_final, num_rows="dynamic", key="final_editor")

    # 반영
    rows = []
    for _, row in edited_final.iterrows():
        for period in periods:
            상태 = row.get(f"{period} 상태", "")
            사유 = row.get(f"{period} 사유", "")
            rows.append({
                "날짜": row["날짜"],
                "이름": row["이름"],
                "차시": period,
                "상태": 상태,
                "사유": 사유
            })
    st.session_state.final_attendance = pd.DataFrame(rows)
