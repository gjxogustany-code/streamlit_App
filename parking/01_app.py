import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

# -------------------------------
# 페이지 설정
# -------------------------------
st.set_page_config(
    page_title="공영주차장 정보",
    page_icon="🅿️",
    layout="wide"
)

st.title("🅿️ 공영주차장 안내 시스템")

st.write("CSV 파일을 업로드하면 주소 검색과 지도를 제공합니다.")

# -------------------------------
# CSV 업로드
# -------------------------------

uploaded_file = st.file_uploader(
    "공영주차장 CSV 업로드",
    type="csv"
)

if uploaded_file is None:
    st.info("CSV 파일을 업로드하세요.")
    st.stop()

# -------------------------------
# CSV 읽기 (인코딩 자동 처리)
# -------------------------------

encodings = [
    "utf-8",
    "utf-8-sig",
    "cp949",
    "euc-kr"
]

df = None

for enc in encodings:

    try:
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, encoding=enc)
        break

    except Exception:
        pass

if df is None:
    st.error("CSV 파일을 읽을 수 없습니다.\nUTF-8 또는 CP949 형식인지 확인하세요.")
    st.stop()

# -------------------------------
# 필수 컬럼 검사
# -------------------------------

required_columns = [
    "주차장명",
    "주소",
    "위도",
    "경도",
    "기본요금",
    "추가요금"
]

missing = [c for c in required_columns if c not in df.columns]

if len(missing) > 0:

    st.error("다음 컬럼이 없습니다.")

    st.write(missing)

    st.stop()

# -------------------------------
# 위도 경도 숫자로 변환
# -------------------------------

df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

df = df.dropna(subset=["위도", "경도"])

st.success("CSV 업로드 완료!")

# -------------------------------
# 데이터 보기
# -------------------------------

with st.expander("데이터 보기"):

    st.dataframe(df)

# -------------------------------
# 주소 검색
# -------------------------------

keyword = st.text_input("주소 검색")

search_df = df.copy()

if keyword:

    search_df = df[
        df["주소"].astype(str).str.contains(
            keyword,
            case=False,
            na=False
        )
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
    zoom_start=12,
    control_scale=True
)

for _, row in df.iterrows():

    color = "blue"

    if keyword:

        if keyword.lower() in str(row["주소"]).lower():

            color = "red"

    tooltip = (
        f"""
        <b>{row['주차장명']}</b><br>
        기본요금 : {row['기본요금']}
        """
    )

    popup = (
        f"""
        <b>{row['주차장명']}</b><br><br>

        주소 : {row['주소']}<br>

        기본요금 : {row['기본요금']}<br>

        추가요금 : {row['추가요금']}
        """
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

st.subheader("🗺️ 공영주차장 지도")

st_folium(
    m,
    width=None,
    height=650
)

st.caption("🔵 전체 주차장   🔴 검색된 주차장")
