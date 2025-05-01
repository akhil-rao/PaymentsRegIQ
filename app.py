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
    try:
        feed = feedparser.parse(feed_url)
        entries = []
        for entry in feed.entries:
            published = entry.get("published", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "#")
            title = entry.get("title", "No title")

            # Format publish date
            try:
                pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z")
                published = pub_date.strftime("%Y-%m-%d %H:%M")
            except:
                pass  # keep original

            entries.append({
                "Title": title,
                "Published": published,
                "Summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "Link": link
            })
        return entries
    except Exception as e:
        st.error(f"Failed to load feed: {e}")
        return []

st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("📡 PaymentsRegIQ - Regulatory Feed for Payments Industry")

# Sidebar for feed selection
selected_feed = st.sidebar.selectbox("Select a source", list(RSS_FEEDS.keys()))

# Parse and display selected feed
feed_entries = parse_feed(RSS_FEEDS[selected_feed])
if not feed_entries:
    st.warning("No data found for the selected feed.")
else:
    df = pd.DataFrame(feed_entries)
    st.write(f"### {selected_feed}")
    st.dataframe(df, use_container_width=True)
