
import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import re
from datetime import datetime
import matplotlib.pyplot as plt
from wordcloud import WordCloud
from konlpy.tag import Okt
from collections import Counter

# 페이지 설정
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")
st.title("📊 유튜브 댓글 분석기")
st.markdown("유튜브 링크와 API 키를 입력하여 댓글의 트렌드와 키워드를 분석해보세요.")

# 폰트 경로 설정 (Streamlit Cloud 리눅스 환경 기준 나눔폰트)
FONT_PATH = "/usr/share/fonts/truetype/nanum/NanumGothic.ttf"

# --- 사이드바: API 키 및 설정 ---
st.sidebar.header("⚙️ 설정")
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
max_comments = st.sidebar.slider("가져올 댓글 개수 설정", min_value=10, max_value=500, value=100, step=10)

# --- 메인 화면: 유튜브 링크 입력 ---
video_url = st.text_input("유튜브 영상 링크를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")

# 유튜브 URL에서 영상 ID 추출하는 함수
def extract_video_id(url):
    pattern = r'(?:v=|\/v\/|youtu\.be\/|\/embed\/)([^#\&\?]*Layout?)'
    # 일반적인 url 패턴 대응
    if "watch?v=" in url:
        return url.split("watch?v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("youtu.be/")[1].split("?")[0]
    return None

# 유튜브 댓글을 가져오는 함수
def get_youtube_comments(api_key, video_id, max_results):
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_results, 100), # 한 번에 최대 100개
            textFormat="plainText"
        )
        
        while request and len(comments) < max_results:
            response = request.execute()
            for item in response['items']:
                comment_data = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment_data['authorDisplayName'],
                    'comment': comment_data['textDisplay'],
                    'published_at': comment_data['publishedAt'],
                    'like_count': comment_data['likeCount']
                })
            
            # 다음 페이지가 있고, 원하는 개수보다 적게 가져왔다면 계속 진행
            if 'nextPageToken' in response and len(comments) < max_results:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    pageToken=response['nextPageToken'],
                    maxResults=min(max_results - len(comments), 100),
                    textFormat="plainText"
                )
            else:
                break
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {e}")
        return None

# --- 실행 로직 ---
if video_url:
    video_id = extract_video_id(video_url)
    
    if video_id:
        # 1. 영상 보여주기
        st.video(video_url)
        
        if not api_key:
            st.warning("👈 왼쪽 사이드바에 YouTube API Key를 입력해 주세요.")
        else:
            with st.spinner("댓글 데이터를 가져오고 분석하는 중입니다..."):
                df = get_youtube_comments(api_key, video_id, max_comments)
                
                if df is not None and not df.empty:
                    # 전처리: 날짜 데이터 변환
                    df['published_at'] = pd.to_datetime(df['published_at'])
                    df['date_hour'] = df['published_at'].dt.strftime('%Y-%m-%d %H시')
                    
                    st.success(f"총 {len(df)}개의 댓글을 성공적으로 가져왔습니다!")
                    
                    # 탭 분할로 깔끔하게 시각화
                    tab1, tab2, tab3 = st.tabs(["📈 시간대별 추이", "❤️ 댓글 반응도", "☁️ 한글 워드클라우드"])
                    
                    # --- Tab 1: 시간대별 댓글 작성 추이 ---
                    with tab1:
                        st.subheader("시간대별 댓글 작성 추이")
                        time_counts = df.groupby('date_hour').size().reset_index(name='count')
                        time_counts = time_counts.sort_values('date_hour')
                        
                        st.line_chart(data=time_counts, x='date_hour', y='count')
                    
                    # --- Tab 2: 댓글 반응도 (좋아요 수가 많은 상위 댓글) ---
                    with tab2:
                        st.subheader("가장 반응이 좋았던 댓글 (좋아요 기준)")
                        top_liked = df.sort_values(by='like_count', ascending=False).head(5)
                        
                        for idx, row in top_liked.iterrows():
                            st.markdown(f"**👤 {row['author']}** (👍 {row['like_count']}개)")
                            st.info(row['comment'])
                    
                    # --- Tab 3: 한글 워드클라우드 ---
                    with tab3:
                        st.subheader("댓글 주요 키워드 (워드클라우드)")
                        
                        # 한글 텍스트만 추출 및 정제
                        raw_text = " ".join(df['comment'].astype(str))
                        clean_text = re.sub(r'[^가-힣\s]', '', raw_text)
                        
                        # 명사 추출
                        okt = Okt()
                        nouns = okt.nouns(clean_text)
                        
                        # 2글자 이상만 필터링
                        nouns = [n for n in nouns if len(n) > 1]
                        
                        if nouns:
                            count = Counter(nouns)
                            
                            # 워드클라우드 생성
                            try:
                                wc = WordCloud(
                                    font_path=FONT_PATH,
                                    background_color="white",
                                    width=800,
                                    height=400
                                ).generate_from_frequencies(count)
                                
                                # Matplotlib 시각화
                                fig, ax = plt.subplots(figsize=(10, 5))
                                ax.imshow(wc, interpolation='interp)
                                ax.axis('off')
                                st.pyplot(fig)
                            except Exception as e:
                                st.error(f"워드클라우드를 생성하는 중 오류가 발생했습니다. (폰트 설정 확인 필요): {e}")
                        else:
                            st.write("분석할 만한 한글 명사 단어가 부족합니다.")
                else:
                    st.info("가져온 댓글이 없거나 영상의 댓글 기능이 꺼져있을 수 있습니다.")
    else:
        st.error("올바른 유튜브 URL 형식이 아닙니다. 확인 후 다시 입력해 주세요.")
