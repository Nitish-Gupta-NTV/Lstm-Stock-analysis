# streamlit_stock_analysis_with_chart.py

import streamlit as st
import yfinance as yf
import pandas as pd
import warnings
import plotly.graph_objects as go
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore", category=FutureWarning)
st.set_page_config(
    page_title="Let model to decied stock name",
    page_icon="😎",
    layout="wide",
)

# --- Disclaimer ---
st.warning(
    "⚠️ This app is formini project purposes only and is NOT financial advice. "
    "Stock market investments carry risk. Always do your own research or consult a licensed professional."
)

# --- User Inputs ---
st.title("📊 Stock Analysis Dashboard")
ticker = st.text_input("Enter a stock ticker (e.g., AAPL, RELIANCE.NS, TCS.NS):", value="AAPL")
risk_profile = st.selectbox(
    "Select your risk profile:",
    options=["conservative", "moderate", "aggressive"]
)

# --- Functions ---
def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    try:
        info = stock.info
        hist = stock.history(period="1y")
        if info.get('regularMarketPrice') is None or hist.empty:
            return None, None
        return info, hist
    except:
        return None, None

def analyze_fundamentals(info):
    score = 0
    reasons = {}
    pe_ratio = info.get('trailingPE')
    if pe_ratio and 0 < pe_ratio < 25:
        score += 1
    reasons['P/E Ratio'] = f"{pe_ratio:.2f}" if pe_ratio else "N/A"
    pb_ratio = info.get('priceToBook')
    if pb_ratio and 0 < pb_ratio < 3:
        score += 1
    reasons['P/B Ratio'] = f"{pb_ratio:.2f}" if pb_ratio else "N/A"
    de_ratio = info.get('debtToEquity')
    if de_ratio and de_ratio < 100:
        score += 1
    reasons['Debt/Equity'] = f"{de_ratio/100:.2f}" if de_ratio else "N/A"
    roe = info.get('returnOnEquity')
    if roe and roe > 0.15:
        score += 1
    reasons['Return on Equity'] = f"{roe:.2%}" if roe else "N/A"
    eps = info.get('trailingEps')
    if eps and eps > 0:
        score += 1
    reasons['EPS'] = f"{eps:.2f}" if eps else "N/A"
    return score, reasons

def analyze_technicals(hist):
    score = 0
    reasons = {}
    delta = hist['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    last_rsi = rsi.iloc[-1]
    if last_rsi < 30: score += 1
    elif last_rsi > 70: score -= 1
    reasons['RSI'] = f"{last_rsi:.2f}" + (" (Oversold)" if last_rsi < 30 else " (Overbought)" if last_rsi > 70 else " (Neutral)")
    hist['MA20'] = hist['Close'].rolling(window=20).mean()
    hist['MA50'] = hist['Close'].rolling(window=50).mean()
    hist['MA100'] = hist['Close'].rolling(window=100).mean()
    hist['MA200'] = hist['Close'].rolling(window=200).mean()
    if hist['MA20'].iloc[-1] > hist['MA50'].iloc[-1]:
        score += 1
        reasons['MA Crossover'] = "Bullish (20-day > 50-day)"
    else:
        score -= 1
        reasons['MA Crossover'] = "Bearish (20-day < 50-day)"
    return score, reasons, rsi, hist

# --- Analysis ---
if st.button("Analyze Stock"):
    info, hist = get_stock_data(ticker)
    if not info:
        st.error("Could not fetch data for this ticker. Please check the symbol and try again.")
    else:
        f_score, f_reasons = analyze_fundamentals(info)
        t_score, t_reasons, rsi, hist = analyze_technicals(hist)
        total_score = f_score + t_score

        st.subheader(f"✨ Analysis for {info.get('shortName', ticker)} ({ticker})")
        st.write(f"**Current Price:** ₹{info.get('regularMarketPrice', 0):.2f}")
        st.write(f"**Total Score:** {total_score}/7")

        with st.expander("📊 Fundamental Analysis"):
            for k, v in f_reasons.items():
                st.write(f"{k}: {v}")

        with st.expander("📈 Technical Analysis"):
            for k, v in t_reasons.items():
                st.write(f"{k}: {v}")

        # Recommendation
        st.subheader("Recommendation Based on Risk Profile")
        recommended = "Hold / Monitor"
        if risk_profile == 'conservative' and f_score >= 4:
            recommended = "Buy (Strong Fundamentals)"
        elif risk_profile == 'moderate' and total_score >= 4:
            recommended = "Buy (Balanced)"
        elif risk_profile == 'aggressive' and t_score >= 1:
            recommended = "Buy (Technical Momentum)"
        st.write(f"**Suggested Action:** {recommended}")

        # --- Plot Chart ---
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                            vertical_spacing=0.1, row_heights=[0.7, 0.3])

        # Top Panel: Candlestick + MA100 + MA200
        fig.add_trace(go.Candlestick(x=hist.index, open=hist['Open'], high=hist['High'],
                                     low=hist['Low'], close=hist['Close'], name='Candlestick'), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA100'], line=dict(color='blue', width=1), name='MA100'), row=1, col=1)
        fig.add_trace(go.Scatter(x=hist.index, y=hist['MA200'], line=dict(color='orange', width=1), name='MA200'), row=1, col=1)

        # Bottom Panel: RSI
        fig.add_trace(go.Scatter(x=hist.index, y=rsi, line=dict(color='red', width=1), name='RSI'), row=2, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="grey", row=2, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="grey", row=2, col=1)

        fig.update_layout(title=f'{ticker} Price Chart with MA100, MA200 & RSI',
                          yaxis_title='Price',
                          xaxis_title='Date',
                          height=800)

        st.plotly_chart(fig, use_container_width=True)
