
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
import folium
from streamlit_folium import st_folium
import random

# 페이지 설정
st.set_page_config(
    page_title="🎉 전국 축제 탐험대",
    page_icon="🎈",
    layout="wide"
)

# API 키 불러오기 (Streamlit Secrets 활용)
API_KEY = st.secrets.get("TOUR_API_KEY", "")

# 한국관광공사 API 호출 함수
@st.cache_data(ttl=3600)  # 1시간 동안 캐시 유지
def get_festival_data(event_start_date):
    url = "http://apis.data.go.kr/B551011/KorService1/searchFestival1"
    params = {
        "serviceKey": API_KEY,
        "numOfRows": "100",
        "pageNo": "1",
        "MobileOS": "ETC",
        "MobileApp": "FestivalApp",
        "_type": "json",
        "listYN": "Y",
        "arrange": "A", # 정렬 (A=제목순, C=수정일순, D=생성일순)
        "eventStartDate": event_start_date
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        items = data['response']['body']['items']['item']
        return pd.DataFrame(items)
    except Exception as e:
        st.error(f"데이터를 불러오는데 실패했습니다: {e}")
        return pd.DataFrame()

# ---------------- 메인 화면 ----------------
st.title("🎈 전국 구석구석 축제 탐험")
st.caption("한국관광공사 TourAPI 기반 실시간 축제 정보")

if not API_KEY:
    st.warning("⚠️ API 키가 설정되지 않았습니다. .streamlit/secrets.toml 또는 Streamlit Cloud Secrets에 TOUR_API_KEY를 추가해 주세요.")
    st.stop()

# 오늘 날짜 기준 (YYYYMMDD)
today_str = datetime.now().strftime("%Y%m%d")
df = get_festival_data(today_str)

if df.empty:
    st.info("현재 조회 가능한 축제 데이터가 없습니다.")
    st.stop()

# 데이터 전처리 (위도/경도 숫자 변환)
df['mapx'] = pd.to_numeric(df['mapx'], errors='coerce')
df['mapy'] = pd.to_numeric(df['mapy'], errors='coerce')

# Sidebar 필터
st.sidebar.header("🔍 축제 검색 및 필터")
search_keyword = st.sidebar.text_input("축제 이름 검색")

if search_keyword:
    filtered_df = df[df['title'].str.contains(search_keyword, case=False, na=False)]
else:
    filtered_df = df.copy()

# ---------------- 재미있는 기능 1: 축제 룰렛 (랜덤 추천) ----------------
st.subheader("🎲 어디로 갈지 고민된다면? 랜덤 축제 뽑기!")
col_roulette, col_info = st.columns([1, 2])

with col_roulette:
    if st.button("✨ 오늘의 운명적인 축제 뽑기!", use_container_width=True):
        random_festival = filtered_df.sample(1).iloc[0]
        st.session_state['selected_festival'] = random_festival

if 'selected_festival' in st.session_state:
    pick = st.session_state['selected_festival']
    with col_info:
        st.success(f"🎉 추천 축제: **{pick['title']}**")
        st.write(f"📍 위치: {pick.get('addr1', '주소 정보 없음')}")
        st.write(f"📅 기간: {pick.get('eventstartdate', '')} ~ {pick.get('eventenddate', '')}")

st.divider()

# ---------------- 메인 탭 구성 ----------------
tab1, tab2 = st.tabs(["📋 축제 목록 & D-Day", "🗺️ 전국 축제 지도"])

with tab1:
    st.write(f"총 **{len(filtered_df)}**개의 축제가 진행 중이거나 예정되어 있습니다.")
    
    # ---------------- 재미있는 기능 2: D-Day 계산 카드 ----------------
    grid_cols = st.columns(3)
    
    for idx, row in filtered_df.iterrows():
        col = grid_cols[idx % 3]
        
        with col:
            with st.container(border=True):
                # 이미지 표시
                img_url = row.get('firstimage') or 'https://via.placeholder.com/300x200?text=No+Image'
                st.image(img_url, use_column_width=True)
                
                # 제목 및 기본 정보
                st.markdown(f"### {row['title']}")
                st.caption(f"📍 {row.get('addr1', '지역 정보 없음')}")
                
                # D-Day 계산
                start_date_str = str(row.get('eventstartdate', ''))
                if start_date_str:
                    start_date = datetime.strptime(start_date_str, "%Y%m%d")
                    days_left = (start_date - datetime.now()).days
                    
                    if days_left > 0:
                        st.chip(f"⏰ 개막 D-{days_left}", icon="🔥")
                    elif days_left == 0:
                        st.chip("🎉 오늘 개막!", icon="✨")
                    else:
                        st.chip("🥳 축제 진행 중", icon="🎈")
                
                st.text(f"기간: {row.get('eventstartdate')} ~ {row.get('eventenddate')}")

with tab2:
    st.subheader("📍 지도에서 축제 위치 확인하기")
    
    # 위도/경도가 존재하는 데이터만 필터링
    map_df = filtered_df.dropna(subset=['mapx', 'mapy'])
    map_df = map_df[(map_df['mapx'] != 0) & (map_df['mapy'] != 0)]
    
    if not map_df.empty:
        # 대한민국 중심 좌표로 지도 생성
        m = folium.Map(location=[36.5, 127.8], zoom_start=7)
        
        for _, row in map_df.iterrows():
            folium.Marker(
                location=[row['mapy'], row['mapx']],
                popup=folium.Popup(f"<b>{row['title']}</b><br>{row.get('addr1', '')}", max_width=200),
                tooltip=row['title'],
                icon=folium.Icon(color="red", icon="star")
            ).add_to(m)
            
        st_folium(m, width="100%", height=500)
    else:
        st.info("지도에 표시할 위치 정보가 없습니다.")
