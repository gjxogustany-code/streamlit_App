import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(
    page_title="공영주차장 안내",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 공영주차장 정보 안내")

st.write("CSV 파일을 업로드하면 주소 검색과 지도를 제공합니다.")

# -------------------------------
# CSV 업로드
# -------------------------------
uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded_file is None:
    st.info("sample_parking.csv 형식의 파일을 업로드하세요.")
    st.stop()

# -------------------------------
# CSV 읽기
# -------------------------------
try:
    df = pd.read_csv(uploaded_file)
except Exception as e:
    st.error(f"CSV를 읽을 수 없습니다.\n{e}")
    st.stop()

required_columns = [
    "주차장명",
    "주소",
    "위도",
    "경도",
    "기본요금",
    "추가요금"
]

missing = [c for c in required_columns if c not in df.columns]

if missing:
    st.error(f"다음 컬럼이 없습니다 : {missing}")
    st.stop()

st.success("CSV 업로드 완료")

st.subheader("데이터")

st.dataframe(df)

# -------------------------------
# 주소 검색
# -------------------------------

keyword = st.text_input("주소 검색")

search_df = df.copy()

if keyword:

    search_df = df[
        df["주소"].astype(str).str.contains(keyword, case=False)
    ]

    st.subheader("검색 결과")

    if len(search_df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:
        st.dataframe(
            search_df[
                [
                    "주차장명",
                    "주소",
                    "기본요금",
                    "추가요금"
                ]
            ]
        )

# -------------------------------
# 지도 생성
# -------------------------------

center = [
    df["위도"].mean(),
    df["경도"].mean()
]

m = folium.Map(
    location=center,
    zoom_start=12
)

for _, row in df.iterrows():

    color = "blue"

    if keyword:
        if keyword in str(row["주소"]):
            color = "red"

    tooltip = (
        f"{row['주차장명']}<br>"
        f"기본요금 : {row['기본요금']}"
    )

    popup = (
        f"<b>{row['주차장명']}</b><br>"
        f"주소 : {row['주소']}<br>"
        f"기본요금 : {row['기본요금']}<br>"
        f"추가요금 : {row['추가요금']}"
    )

    folium.CircleMarker(
        location=[row["위도"], row["경도"]],
        radius=7,
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.8,
        tooltip=tooltip,
        popup=popup
    ).add_to(m)

st.subheader("공영주차장 지도")

st_folium(
    m,
    width=1200,
    height=650
)
