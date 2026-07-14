import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# 페이지 설정
# -----------------------------
st.set_page_config(
    page_title="Global Top10 Stocks Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 Global Market Cap Top10 Dashboard")
st.markdown("최근 1년간 글로벌 시가총액 Top10 기업의 주가를 비교합니다.")

# -----------------------------
# 기업 목록
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
# Sidebar
# -----------------------------
st.sidebar.header("설정")

selected = st.sidebar.multiselect(
    "기업 선택",
    list(stocks.keys()),
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
            auto_adjust=True,
            progress=False
        )

        if df.empty:
            return None

        df = df.reset_index()

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Date", "Close"]].copy()

        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna()

        return df

    except Exception:
        return None


# -----------------------------
# 데이터 저장
# -----------------------------
stock_data = {}

for company in selected:

    ticker = stocks[company]

    data = load_data(ticker)

    if data is None or data.empty:
        st.warning(f"{company} 데이터를 불러오지 못했습니다.")
        continue

    stock_data[company] = data

# -----------------------------
# Plotly Figure (SVG 렌더링)
# -----------------------------
fig = go.Figure()

for company, data in stock_data.items():

    if mode == "수익률(%)":
        y = (data["Close"] / data["Close"].iloc[0] - 1) * 100
        ylabel = "Return (%)"
        hover = "%{y:.2f}%"

    else:
        y = data["Close"]
        ylabel = "Price (USD)"
        hover = "$%{y:.2f}"

    fig.add_trace(
        go.Scatter(
            x=data["Date"],
            y=y,
            mode="lines",
            name=company,
            line=dict(width=2),
            hovertemplate=(
                "<b>%{fullData.name}</b><br>"
                "%{x|%Y-%m-%d}<br>"
                + hover +
                "<extra></extra>"
            )
        )
    )

fig.update_layout(
    template="plotly_white",
    height=700,
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title=ylabel,
    legend_title="Company"
)

st.plotly_chart(fig, use_container_width=True)

# -----------------------------
# Summary
# -----------------------------
if stock_data:

    summary = []

    for company, data in stock_data.items():

        first = float(data["Close"].iloc[0])
        last = float(data["Close"].iloc[-1])

        summary.append({
            "Company": company,
            "Latest Price (USD)": round(last, 2),
            "1Y Return (%)": round((last / first - 1) * 100, 2)
        })

    summary_df = (
        pd.DataFrame(summary)
        .sort_values("1Y Return (%)", ascending=False)
    )

    st.subheader("📊 Summary")

    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True
    )

else:
    st.error("표시할 데이터가 없습니다.")
