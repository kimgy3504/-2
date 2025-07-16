import streamlit as st
import pandas as pd
import datetime

# 설정
students = ["강정원", "고민서", "권지연", "김가령", "김나형", "김예르미", "박수빈", "송가은", "이려흔", "이수아", "임보배", "정지윤", "지혜원", "최수민", "하다빈", "한유진"]
periods = ["1차시", "2차시"]

# 정기 결석 패턴
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
    "한유진": {"pattern": "once", "days": [0, 3, 5]}     # 매주 화,목 2차시만 결석
}

# 날짜 설정
today = datetime.date.today()
if st.session_state.get("last_date") != today:
    st.session_state.temp_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.final_attendance = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    st.session_state.last_date = today

st.title("📝 출석 체크 (결석자만 선택)")

date = st.date_input("출석 날짜", today)
date_str = date.strftime("%Y-%m-%d")
weekday = date.weekday()

# 입력 폼
st.subheader("📋 출석 체크")

absent_students = {name: {period: False for period in periods} for name in students}
reasons = {name: {period: "" for period in periods} for name in students}

for name in students:
    cols = st.columns([1, 1, 1, 2, 2])
    cols[0].write(f"**{name}**")
    for i, period in enumerate(periods):
        auto = False
        auto_reason = ""
        if name in regular_absents:
            rule = regular_absents[name]
            if "once" in rule and weekday in rule["once"]:
                auto = True
                auto_reason = "정기 결석 (1,2차시)"
            elif "twice" in rule and weekday in rule["twice"] and period == "2차시":
                auto = True
                auto_reason = "정기 결석 (2차시)"

        key_cb = f"{name}_{period}_cb"
        key_reason = f"{name}_{period}_rs"

        if auto:
            absent_students[name][period] = True
            cols[1 + i].checkbox(f"{period} 결석", value=True, disabled=True, key=key_cb)
            cols[3 + i].text(auto_reason)
            reasons[name][period] = auto_reason
        else:
            checked = cols[1 + i].checkbox(f"{period} 결석", key=key_cb)
            absent_students[name][period] = checked
            if checked:
                reason = cols[3 + i].text_input(f"{name} {period} 사유", key=key_reason)
                reasons[name][period] = reason

# 임시 저장
if st.button("💾 임시 출석 기록 저장"):
    df = pd.DataFrame(columns=["날짜", "차시", "이름", "상태", "사유"])
    for name in students:
        for period in periods:
            상태 = "결석" if absent_students[name][period] else "출석"
            사유 = reasons[name][period] if 상태 == "결석" else ""
            df.loc[len(df)] = [date_str, period, name, 상태, 사유]

    # 같은 날짜 데이터 삭제
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        st.session_state.temp_attendance["날짜"] != date_str
    ]
    st.session_state.temp_attendance = pd.concat([st.session_state.temp_attendance, df], ignore_index=True)
    st.success("✅ 임시 출석 기록 저장 완료")

# 피벗 함수
def pivot(df):
    if df.empty:
        return df
    pivoted = df.pivot_table(
        index="이름",
        columns="차시",
        values=["상태", "사유"],
        aggfunc='first',
        fill_value=""
    )
    pivoted.columns = [f"{col2} {col1}" for col1, col2 in pivoted.columns]
    pivoted.reset_index(inplace=True)
    return pivoted

# 임시 수정
st.subheader("✏️ 임시 출석 기록 수정")

if st.session_state.temp_attendance.empty:
    st.info("임시 저장된 출석 기록이 없습니다.")
else:
    pivot_temp = pivot(st.session_state.temp_attendance[st.session_state.temp_attendance["날짜"] == date_str])
    edited_temp = st.data_editor(pivot_temp, num_rows="dynamic", key="edit_temp")

    # 역변환
    rows = []
    for _, row in edited_temp.iterrows():
        for period in periods:
            상태 = row.get(f"{period} 상태", "")
            사유 = row.get(f"{period} 사유", "")
            rows.append({
                "날짜": date_str,
                "이름": row["이름"],
                "차시": period,
                "상태": 상태,
                "사유": 사유,
            })
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        st.session_state.temp_attendance["날짜"] != date_str
    ]
    st.session_state.temp_attendance = pd.concat(
        [st.session_state.temp_attendance, pd.DataFrame(rows)],
        ignore_index=True
    )

# 최종 저장
if st.button("✅ 최종 출석 기록 저장"):
    st.session_state.final_attendance = st.session_state.final_attendance[
        st.session_state.final_attendance["날짜"] != date_str
    ]
    st.session_state.final_attendance = pd.concat(
        [st.session_state.final_attendance, st.session_state.temp_attendance[
            st.session_state.temp_attendance["날짜"] == date_str
        ]],
        ignore_index=True
    )
    st.session_state.temp_attendance = st.session_state.temp_attendance[
        st.session_state.temp_attendance["날짜"] != date_str
    ]
    st.success("🎉 최종 출석 기록 저장 완료")

# 최종 기록 보기
st.subheader("📊 최종 출석 기록")

if st.session_state.final_attendance.empty:
    st.info("최종 저장된 출석 기록이 없습니다.")
else:
    pivot_final = pivot(st.session_state.final_attendance[st.session_state.final_attendance["날짜"] == date_str])
    st.dataframe(pivot_final)

# 출석 요약 정보
if not st.session_state.final_attendance.empty:
    filtered = st.session_state.final_attendance[st.session_state.final_attendance["날짜"] == date_str]
    summary = filtered.groupby(["차시", "상태"]).size().unstack(fill_value=0)
    st.subheader("📈 출석 요약 정보")
    st.dataframe(summary)


