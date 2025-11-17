import streamlit as st
import requests
import pandas as pd

# --------------------------- Page Config ---------------------------
st.set_page_config(
    page_title="Stock & Market News",
    page_icon="📰",
    layout="wide",
)
st.title("📰 Stock & Market News")
st.markdown(
    "Stay up-to-date with the latest stock and market news. "
    "Enter a stock ticker to get news for that company, or browse trending market news by default."
)

# --------------------------- User Input (Same Line) ---------------------------
col1, col2 = st.columns([3, 1])
with col1:
    ticker = st.text_input(
        "Enter Stock Ticker (e.g., AAPL, RELIANCE.NS, TCS.NS):",
        value=""
    )
with col2:
    get_news_clicked = st.button("Get News")

# --------------------------- API Token ---------------------------
API_TOKEN = "cmeIXBuOBJ2o0PQK9lCJTwewYfUPnbiqXoF8UNX4"

# --------------------------- Function to Fetch News ---------------------------
def get_marketaux_news(ticker=None, max_articles=20):
    """
    Fetch news from Marketaux API.
    If ticker is None, returns trending news.
    """
    base_url = "https://api.marketaux.com/v1/news/all"
    params = {
        "api_token": API_TOKEN,
        "language": "en",
        "limit": max_articles
    }
    if ticker:
        params["symbols"] = ticker.upper()

    try:
        response = requests.get(base_url, params=params, timeout=10)
        if response.status_code != 200:
            st.error(f"Error fetching news: {response.status_code} - {response.text}")
            return []
        data = response.json()
        return data.get("data", [])
    except requests.exceptions.RequestException as e:
        st.error(f"Network error: {e}")
        return []

# --------------------------- Display News ---------------------------
def display_news(news_items):
    """Display news in two-column professional layout."""
    for n in news_items:
        title = n.get("title", "No Title")
        source = n.get("source", "Unknown")
        url = n.get("url", "#")
        published_at = n.get("published_at", None)
        date = pd.to_datetime(published_at).strftime("%b %d, %Y %H:%M") if published_at else "Unknown"

        # Two-column layout for each news item
        left_col, right_col = st.columns([3, 1])
        with left_col:
            st.markdown(f"### {title}")
            st.write(f"**Source:** {source}  |  **Published:** {date}")
        with right_col:
            st.markdown(f"[Read Full Article]({url})")
        st.divider()

# --------------------------- Main Logic ---------------------------
# By default, show trending news when the user visits the page
if not ticker:
    st.subheader("🔥 Trending Market News")
    trending_news = get_marketaux_news(max_articles=20)
    if trending_news:
        display_news(trending_news)
    else:
        st.info("No trending news available at the moment.")

# Show news when button is clicked
if get_news_clicked:
    if ticker:
        st.subheader(f"📈 News for {ticker.upper()}")
        news_items = get_marketaux_news(ticker=ticker, max_articles=20)
        if news_items:
            display_news(news_items)
        else:
            st.info(f"No news found for ticker {ticker.upper()}.")
    else:
        st.warning("Please enter a stock ticker to fetch news.")
