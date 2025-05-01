import streamlit as st
import feedparser
from datetime import datetime
import pandas as pd

# Define RSS feeds
RSS_FEEDS = {
    "Federal Reserve - Press Releases": "https://www.federalreserve.gov/feeds/press_all.xml",
    "Bank of England - News": "https://www.bankofengland.co.uk/rss/news",
    "BIS - Press Releases": "https://www.bis.org/doclist/all_pressrels.rss",
    "MAS - News Releases": "https://www.mas.gov.sg/rss/NewsReleases.xml"
}

def parse_feed(feed_url):
    feed = feedparser.parse(feed_url)
    entries = []
    for entry in feed.entries:
        entries.append({
            "Title": entry.title,
            "Link": entry.link,
            "Published": entry.published if 'published' in entry else '',
            "Summary": entry.summary if 'summary' in entry else ''
        })
    return entries

st.title("PaymentsRegIQ - Regulatory Feed for Payments Industry")

# Sidebar for feed selection
selected_feed = st.sidebar.selectbox("Select a feed", list(RSS_FEEDS.keys()))

# Parse and display selected feed
feed_entries = parse_feed(RSS_FEEDS[selected_feed])
df = pd.DataFrame(feed_entries)

st.write(f"### {selected_feed}")
st.dataframe(df)
