import streamlit as st
import pandas as pd
import datetime

# 학생 목록
students = ["강정원", "고민서", "권지연", "김가령", "김나형", "김예르미", "박수빈", "송가은", "이려흔", "이수아", "임보배", "정지윤", "지혜원", "최수민", "하다빈", "한유진"]
periods = ["1차시", "2차시"]

# 정기 결석 설정
regular_absents = {
    "고민서": {"pattern": "once", "days": [1]},   # 매주 화, 목 2차시만 결석
    "권지연": {"pattern": "twice", "days": [0, 3, 5]},
    "김가령": {"pattern": "once", "days": [4]},
    "김나형": {"pattern": "twice", "days": [0, 2, 5]},
    "김예르미": {"pattern": "once", "days": [4]},
    "이려흔": {"pattern": "twice", "days": [2,5]},
    "이수아": {"pattern": "twice", "days": [4, 5]},
    "정지윤": {"pattern": "twice", "days": [5]},
    "최수민": {"pattern": "twice", "days": [0]}, "최수민": {"pattern": "once", "days": [5]},
    "하다빈": {"pattern": "twice", "days": [0]},
    "한유진": {"pattern": "once", "days": [0, 3, 5]},
}

st.title("📝 출석부 (1,2차시 분리 + 정기 결석 반영 + 학생별 기록)")

# 자동 초기화
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

# 출석 체크 입력
absent_students_period = {period: [] for period in periods}
reasons_period = {period: {} for period in periods}

for period in periods:
    st.markdown(f"### ▶ {period} 출석 체크")
    for name in students:
        absent_auto = False
        reason = ""
        if name in regular_absents:
            info = regular_absents[name]
            if info["pattern"] == "once" and weekday in info["days"]:
                absent_auto = True
                reason = "정기 결석일 (1,2차시 모두 결석)"
            elif info["pattern"] == "twice" and weekday in info["days"] and period == "2차시":
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
                reasons_period[period][name] = st.text_input(
                    f"{name} 결석 사유 ({period})", key=f"{name}_reason_{period}"
                )

# 임시 저장 버튼
if st.button("💾 임시 출석 기록 저장"):
    if "temp_attendance" not in st.session_state:
        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])

    # 현재 임시 저장된 기록 불러오기
    df = st.session_state.temp_attendance.copy()

    # 기존 해당 날짜+차시+이름 제거
    for period in periods:
        for name in students:
            df = df[~((df["날짜"] == date_str) & (df["차시"] == period) & (df["이름"] == name))]

    # 새 데이터 반영
    new_rows = []
    for period in periods:
        for name in students:
            if name in absent_students_period[period]:
                status = "결석"
                reason = reasons_period[period].get(name, "")
            else:
                status = "출석"
                reason = ""
            new_rows.append({
                "날짜": date_str,
                "차시": period,
                "이름": name,
                "상태": status,
                "사유": reason,
            })

    # 병합 및 저장
    st.session_state.temp_attendance = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    st.success("✅ 임시 출석 기록이 저장되었습니다.")

# 최종 저장 버튼
if st.button("✅ 최종 출석 기록 저장"):
    if "temp_attendance" not in st.session_state or st.session_state.temp_attendance.empty:
        st.warning("임시 출석 기록이 없습니다.")
    else:
        if "final_attendance" not in st.session_state:
            st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
        
        # 기존 해당 날짜 제거
        st.session_state.final_attendance = st.session_state.final_attendance[
            st.session_state.final_attendance["날짜"] != date_str
        ]
        
        # 추가
        st.session_state.final_attendance = pd.concat(
            [st.session_state.final_attendance, st.session_state.temp_attendance],
            ignore_index=True
        )
        st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
        st.success("🎉 최종 출석 기록이 저장되었습니다.")

# 최종 기록 보기
st.subheader("📊 최종 출석 기록 (학생별 1줄 보기)")

if "final_attendance" not in st.session_state or st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    pivot_final = pivot_attendance(st.session_state.final_attendance)
    edited_final = st.data_editor(pivot_final, num_rows="dynamic", key="final_editor")

    # 수정 반영
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
                "사유": 사유,
            })
    st.session_state.final_attendance = pd.DataFrame(rows)
if not st.session_state.final_attendance.empty:
    st.subheader("📈 출석 요약 정보")
    summary = (
        st.session_state.final_attendance
        .groupby(["날짜", "차시", "상태"])
        .size()
        .unstack(fill_value=0)
        .reset_index()
    )
    summary = summary.rename(columns={"출석": "출석자 수", "결석": "결석자 수"}).fillna(0)
    st.dataframe(summary)
