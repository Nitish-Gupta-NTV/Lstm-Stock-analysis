# streamlit_stock_recommender.py

import streamlit as st
import yfinance as yf
import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings("ignore", category=FutureWarning)
st.set_page_config(
    page_title="Let model to decied stock name",
    page_icon="😎",
    layout="wide",
)

# --- Disclaimer ---
st.warning(
    "⚠️ This app is for College mini project purposes only and is NOT financial advice. "
    "Stock market investments carry risk. Always do your own research or consult a licensed professional."
)

# --- List of stocks to scan ---
STOCKS_TO_SCAN = [
    'RELIANCE.NS', 'TCS.NS', 'HDFCBANK.NS', 'INFY.NS',
    'ICICIBANK.NS', 'HINDUNILVR.NS', 'BHARTIARTL.NS', 'ITC.NS',
    'SBIN.NS', 'LT.NS'
]

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
    reasons['RSI'] = f"{last_rsi:.2f} " + ("(Oversold)" if last_rsi < 30 else "(Overbought)" if last_rsi > 70 else "(Neutral)")

    hist['MA20'] = hist['Close'].rolling(window=20).mean()
    hist['MA50'] = hist['Close'].rolling(window=50).mean()

    if hist['MA20'].iloc[-1] > hist['MA50'].iloc[-1]:
        score += 1
        reasons['MA Crossover'] = "Bullish (20-day > 50-day)"
    else:
        score -= 1
        reasons['MA Crossover'] = "Bearish (20-day < 50-day)"

    return score, reasons

def find_best_stock(risk_profile):
    analyzed_stocks = []

    progress_text = st.empty()
    progress_bar = st.progress(0)

    for i, ticker in enumerate(STOCKS_TO_SCAN):
        info, hist = get_stock_data(ticker)
        if not info:
            continue

        f_score, f_reasons = analyze_fundamentals(info)
        t_score, t_reasons = analyze_technicals(hist)

        analyzed_stocks.append({
            'Ticker': ticker,
            'Company': info.get('shortName', ticker),
            'Price': info.get('regularMarketPrice', 0),
            'Fundamental Score': f_score,
            'Technical Score': t_score,
            'Total Score': f_score + t_score,
            'Fundamental Details': f_reasons,
            'Technical Details': t_reasons
        })

        progress_text.text(f"Scanning {i+1}/{len(STOCKS_TO_SCAN)}: {ticker}")
        progress_bar.progress((i+1)/len(STOCKS_TO_SCAN))

    progress_text.text("✅ Analysis complete!")
    progress_bar.empty()

    df = pd.DataFrame(analyzed_stocks).sort_values(by='Total Score', ascending=False)

    # Filter based on risk profile
    if risk_profile == 'conservative':
        df_filtered = df[df['Fundamental Score'] >= 4]
    elif risk_profile == 'moderate':
        df_filtered = df[df['Total Score'] >= 3]
    elif risk_profile == 'aggressive':
        df_filtered = df[df['Technical Score'] >= 1]
    else:
        df_filtered = df

    if df_filtered.empty:
        st.warning("No suitable stock found for your risk profile.")
        return

    best_stock = df_filtered.iloc[0]

    st.subheader("✨ Recommended Stock ✨")
    st.write(f"**Company:** {best_stock['Company']} ({best_stock['Ticker']})")
    st.write(f"**Current Price:** ₹{best_stock['Price']:.2f}")
    st.write(f"**Overall Score:** {best_stock['Total Score']}/7")

    with st.expander("📊 Fundamental Details"):
        for key, val in best_stock['Fundamental Details'].items():
            st.write(f"{key}: {val}")

    with st.expander("📈 Technical Details"):
        for key, val in best_stock['Technical Details'].items():
            st.write(f"{key}: {val}")

    st.subheader("📑 All Analyzed Stocks")
    st.dataframe(df[['Ticker', 'Company', 'Price', 'Fundamental Score', 'Technical Score', 'Total Score']])

# --- Streamlit UI ---
st.sidebar.title("Investor Risk Profile")
risk_profile = st.sidebar.selectbox(
    "Select your risk profile:",
    options=["conservative", "moderate", "aggressive"]
)

if st.sidebar.button("Analyze Stocks"):
    find_best_stock(risk_profile)
