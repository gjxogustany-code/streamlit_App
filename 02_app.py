import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Global Top10 Stocks Dashboard",
    page_icon="📈",
    layout="wide"
)

st.title("🌍 Global Market Cap Top10 Dashboard")
st.markdown("최근 1년간 글로벌 시가총액 Top10 기업의 주가를 비교합니다.")

# 글로벌 시가총액 Top10 (2025 기준)
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

selected = st.multiselect(
    "기업 선택",
    options=list(stocks.keys()),
    default=list(stocks.keys())[:5]
)

mode = st.radio(
    "그래프 종류",
    ["수익률(%)", "주가(USD)"],
    horizontal=True
)

@st.cache_data
def load_data(ticker):
    df = yf.download(
        ticker,
        period="1y",
        interval="1d",
        progress=False,
        auto_adjust=True
    )

    df = df.reset_index()

    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df[["Date", "Close"]]
    df["Ticker"] = ticker
    return df

dfs = []

for company in selected:
    ticker = stocks[company]

    try:
        data = load_data(ticker)
        data["Company"] = company

        if mode == "수익률(%)":
            base = data["Close"].iloc[0]
            data["Value"] = (data["Close"] / base - 1) * 100
            ylabel = "Return (%)"
        else:
            data["Value"] = data["Close"]
            ylabel = "Price"

        dfs.append(data)

    except:
        st.warning(f"{company} 데이터를 가져오지 못했습니다.")

if dfs:

    chart = pd.concat(dfs)

    fig = px.line(
        chart,
        x="Date",
        y="Value",
        color="Company",
        template="plotly_dark"
    )

    fig.update_layout(
        height=700,
        xaxis_title="Date",
        yaxis_title=ylabel,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)

    latest = []

    for company in selected:

        ticker = stocks[company]
        data = load_data(ticker)

        latest.append({
            "Company": company,
            "Latest Price": round(data["Close"].iloc[-1], 2),
            "1Y Return (%)": round(
                (data["Close"].iloc[-1]/data["Close"].iloc[0]-1)*100,
                2
            )
        })

    st.subheader("📊 Summary")

    summary = pd.DataFrame(latest)

    st.dataframe(
        summary.sort_values(
            "1Y Return (%)",
            ascending=False
        ),
        use_container_width=True
    )

else:
    st.info("기업을 선택해주세요.")
