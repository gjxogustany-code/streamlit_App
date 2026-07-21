import streamlit as st
import requests
import pandas as pd
import random
from datetime import datetime


# ==========================
# 기본 설정
# ==========================

st.set_page_config(
    page_title="FESTA KOREA",
    page_icon="🎉",
    layout="wide"
)


API_KEY = st.secrets["TOUR_API_KEY"]


# ==========================
# 축제 API 호출
# ==========================

@st.cache_data(ttl=3600)
def get_festivals():

    url = (
        "https://apis.data.go.kr/B551011/KorService1/searchFestival1"
    )

    today = datetime.now().strftime("%Y%m%d")

    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalApp",
        "eventStartDate": today,
        "numOfRows": 100,
        "pageNo": 1,
        "_type": "json"
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10
        )

        data = response.json()

        items = (
            data["response"]
            ["body"]
            ["items"]
            ["item"]
        )

        return pd.DataFrame(items)

    except Exception as e:

        st.error(
            f"API 호출 오류: {e}"
        )

        return pd.DataFrame()



# ==========================
# 날짜 계산
# ==========================

def calculate_dday(date):

    try:

        start = datetime.strptime(
            str(date),
            "%Y%m%d"
        )

        today = datetime.now()

        diff = (
            start - today
        ).days


        if diff > 0:
            return f"D-{diff}"

        elif diff == 0:
            return "🔥 오늘 시작"

        else:
            return "🎉 진행중"


    except:

        return "-"



# ==========================
# 화면
# ==========================


st.title("🎉 FESTA KOREA")

st.write(
    "한국관광공사 API 기반 전국 축제 정보 서비스"
)


df = get_festivals()



if df.empty:

    st.warning(
        "축제 데이터를 가져오지 못했습니다."
    )

    st.stop()



# ==========================
# 데이터 정리
# ==========================

columns = {
    "title": "축제명",
    "addr1": "주소",
    "eventstartdate": "시작일",
    "eventenddate": "종료일",
    "firstimage": "이미지",
    "mapx": "경도",
    "mapy": "위도"
}


for col in columns:

    if col not in df:

        df[col] = ""



df["상태"] = df["eventstartdate"].apply(
    calculate_dday
)



# ==========================
# 사이드바
# ==========================


st.sidebar.header(
    "🔎 검색"
)


keyword = st.sidebar.text_input(
    "축제 검색"
)


regions = [
    "전체"
]


if "addr1" in df:

    regions += sorted(
        list(
            set(
                df["addr1"]
                .dropna()
                .astype(str)
                .str[:2]
            )
        )
    )


region = st.sidebar.selectbox(
    "지역 선택",
    regions
)



# ==========================
# 필터
# ==========================


result = df.copy()


if keyword:

    result = result[
        result["title"]
        .str.contains(
            keyword,
            na=False
        )
    ]


if region != "전체":

    result = result[
        result["addr1"]
        .str.contains(
            region,
            na=False
        )
    ]



# ==========================
# 랜덤 추천
# ==========================


st.subheader(
    "🎲 오늘의 추천 축제"
)


if st.button(
    "랜덤 축제 뽑기"
):

    festival = random.choice(
        df.to_dict("records")
    )


    st.success(
        festival["title"]
    )

    st.write(
        festival.get(
            "addr1",
            ""
        )
    )

    st.write(
        "상태:",
        calculate_dday(
            festival["eventstartdate"]
        )
    )



st.divider()



# ==========================
# 축제 카드 출력
# ==========================


st.subheader(
    f"🎪 축제 목록 ({len(result)}개)"
)



for _, row in result.iterrows():


    with st.container():

        col1, col2 = st.columns(
            [1,3]
        )


        with col1:

            if row["firstimage"]:

                st.image(
                    row["firstimage"],
                    width=180
                )


        with col2:

            st.markdown(
                f"""
                ### {row['title']}

                📍 {row['addr1']}

                📅 {row['eventstartdate']} ~ 
                {row['eventenddate']}

                ⭐ {row['상태']}
                """
            )


        st.divider()



# ==========================
# 지도 표시
# ==========================

st.subheader(
    "🗺 축제 위치"
)


map_df = result[
    ["mapy","mapx"]
].copy()


map_df.columns = [
    "lat",
    "lon"
]


map_df = map_df[
    (map_df["lat"]!="")
    &
    (map_df["lon"]!="")
]


if len(map_df)>0:

    map_df["lat"] = map_df["lat"].astype(float)

    map_df["lon"] = map_df["lon"].astype(float)


    st.map(
        map_df
    )



