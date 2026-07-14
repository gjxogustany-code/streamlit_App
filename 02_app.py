import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="Global Top10 Stocks Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 Global Market Cap Top10 Dashboard")
st.markdown("### 최근 1년간 글로벌 시가총액 Top10 기업의 주가를 비교합니다.")

# -----------------------------
# 글로벌 시가총액 Top10
# -----------------------------
stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "TSMC": "TSM",
    "Berkshire Hathaway": "BRK-B"
}

# -----------------------------
# 사이드바
# -----------------------------
st.sidebar.header("설정")

selected = st.sidebar.multiselect(
    "기업 선택",
    options=list(stocks.keys()),
    default=list(stocks.keys())[:5]
)

mode = st.sidebar.radio(
    "그래프 종류",
    ["수익률(%)", "주가(USD)"]
)

# -----------------------------
# 데이터 다운로드
# -----------------------------
@st.cache_data(show_spinner=False)
def load_data(ticker):

    try:
        df = yf.download(
            ticker,
            period="1y",
            interval="1d",
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        df = df.reset_index()

        # MultiIndex 제거
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Date", "Close"]].copy()

        # Close가 DataFrame인 경우 대응
        if isinstance(df["Close"], pd.DataFrame):
            df["Close"] = df["Close"].iloc[:, 0]

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna()

        return df

    except Exception:
        return None


# -----------------------------
# 데이터 수집
# -----------------------------
chart_data = []
stock_data = {}

for company in selected:

    ticker = stocks[company]

    data = load_data(ticker)

    if data is None or data.empty:
        st.warning(f"{company} 데이터를 가져오지 못했습니다.")
        continue

    stock_data[company] = data.copy()

    data["Company"] = company

    if mode == "수익률(%)":

        base = float(data["Close"].iloc[0])

        data["Value"] = (
            data["Close"] / base - 1
        ) * 100

        ylabel = "Return (%)"

    else:

        data["Value"] = data["Close"]

        ylabel = "Price (USD)"

    chart_data.append(data)

# -----------------------------
# 차트
# -----------------------------
if len(chart_data) > 0:

    chart = pd.concat(chart_data)

    fig = px.line(
        chart,
        x="Date",
        y="Value",
        color="Company",
        template="plotly_dark"
    )

    fig.update_layout(
        height=700,
        hovermode="x unified",
        xaxis_title="Date",
        yaxis_title=ylabel,
        legend_title="Company"
    )

    fig.update_traces(line=dict(width=3))

    st.plotly_chart(fig, use_container_width=True)

    # -------------------------
    # Summary Table
    # -------------------------
    summary = []

    for company, data in stock_data.items():

        first_price = float(data["Close"].iloc[0])
        last_price = float(data["Close"].iloc[-1])

        summary.append({

            "Company": company,

            "Latest Price (USD)": round(last_price, 2),

            "1Y Return (%)": round(
                (last_price / first_price - 1) * 100,
                2
            )
        })

    summary_df = pd.DataFrame(summary)

    summary_df = summary_df.sort_values(
        "1Y Return (%)",
        ascending=False
    )

    st.subheader("📊 Summary")

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("선택한 기업의 데이터를 불러올 수 없습니다.")
