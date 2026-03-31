import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import feedparser
import requests
import html

# Configuration de la page
st.set_page_config(
    page_title="Market Monitor - Bloomberg Style",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour style Bloomberg
st.markdown("""
<style>
    .main {
        background-color: #000000;
        color: #00ff00;
    }
    .stMetric {
        background-color: #1a1a1a;
        color: #00ff00;
    }
    div[data-testid="stMetricValue"] {
        color: #00ff00;
    }
    h1, h2, h3 {
        color: #ff9900;
    }
</style>
""", unsafe_allow_html=True)

# Titre
st.title("◆ GLOBAL MARKET WATCH ◆")

# Configuration des actifs
ASSETS = {
    "S&P 500": "^GSPC",
    "BTC/USD": "BTC-USD",
    "GOLD": "GC=F",
    "SILVER": "SI=F",
    "MICROSTRAT": "MSTR",
    "TESLA": "TSLA",
    "GOLD PROD": "GDX"
}

# Sidebar pour les paramètres
st.sidebar.header("⚙️ Paramètres")
selected_period = st.sidebar.selectbox(
    "Période",
    ["6 Mois", "1 An", "5 Ans", "10 Ans"],
    index=0
)

selected_assets = st.sidebar.multiselect(
    "Actifs à afficher",
    list(ASSETS.keys()),
    default=["S&P 500", "BTC/USD"]
)

# Mapping période -> jours
period_days = {
    "6 Mois": 180,
    "1 An": 365,
    "5 Ans": 1825,
    "10 Ans": 3650
}

# Récupération des données
@st.cache_data(ttl=300)
def get_historical_data(ticker, days):
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    data = yf.download(ticker, start=start_date, end=end_date, progress=False)
    return data['Close'] if not data.empty else None

@st.cache_data(ttl=60)
def get_current_price(ticker):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1d")
    return data['Close'].iloc[-1] if not data.empty else None

# Affichage des prix en temps réel
st.subheader("📊 Prix en Temps Réel")
cols = st.columns(len(selected_assets) if selected_assets else 1)

prices = {}
for i, asset_name in enumerate(selected_assets):
    ticker = ASSETS[asset_name]
    price = get_current_price(ticker)

    if price is not None:
        prices[asset_name] = price

        # Calcul de la variation
        days = period_days[selected_period]
        hist_data = get_historical_data(ticker, days)

        if hist_data is not None and len(hist_data) > 1:
            start_price = hist_data.iloc[0]
            change = price - start_price
            pct_change = (change / start_price) * 100

            with cols[i % len(cols)]:
                st.metric(
                    label=asset_name,
                    value=f"${price:,.2f}",
                    delta=f"{change:+,.2f} ({pct_change:+.2f}%)"
                )

# Graphique
if selected_assets:
    st.subheader("📈 Performance Relative (Base 100)")

    fig = go.Figure()

    for asset_name in selected_assets:
        ticker = ASSETS[asset_name]
        hist_data = get_historical_data(ticker, period_days[selected_period])

        if hist_data is not None and len(hist_data) > 1:
            # Normalisation base 100
            normalized = (hist_data / hist_data.iloc[0]) * 100

            fig.add_trace(go.Scatter(
                x=normalized.index,
                y=normalized.values,
                name=asset_name,
                mode='lines',
                line=dict(width=2)
            ))

    fig.update_layout(
        template='plotly_dark',
        height=500,
        xaxis_title="Date",
        yaxis_title="Performance (%)",
        hovermode='x unified'
    )

    st.plotly_chart(fig, use_container_width=True)

# News Feed
st.subheader("📰 News Feed")

NEWS_FEEDS = [
    "https://feeds.feedburner.com/zerohedge/feed",
    "https://feeds.reuters.com/reuters/businessNews",
    "https://www.cnbc.com/id/100003114/device/rss/rss.html",
]

all_news = []
for feed_url in NEWS_FEEDS:
    try:
        response = requests.get(feed_url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0'
        })
        response.raise_for_status()
        feed = feedparser.parse(response.content)

        for entry in feed.entries[:3]:
            all_news.append({
                'title': html.escape(entry.get('title', 'No title')),
                'source': html.escape(
                    feed.feed.get('title', 'Unknown') if hasattr(feed, 'feed') else 'Unknown'
                ),
                'published': entry.get('published', '')
            })
    except Exception:
        continue

if all_news:
    for news in all_news[:10]:
        st.markdown(f"""
        **▶ {news['title']}**
        *[{news['source']}]* - {news['published'][:50] if news['published'] else 'N/A'}
        ---
        """)
else:
    st.info("Aucune news disponible")

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "Market Monitor Professional • Données fournies par Yahoo Finance"
    "</div>",
    unsafe_allow_html=True
)
