import streamlit as st
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd
import re

# RSS feeds from regulatory bodies
RSS_FEEDS = {
    "Federal Reserve": "https://www.federalreserve.gov/feeds/press_all.xml",
    "Bank of England": "https://www.bankofengland.co.uk/rss/news",
    "BIS": "https://www.bis.org/doclist/all_pressrels.rss",
    "MAS": "https://www.mas.gov.sg/rss/NewsReleases.xml"
}

def classify_regulation(title, summary):
    text = (title + " " + summary).lower()
    if "iso 20022" in text or "structured" in text:
        return "ISO 20022"
    elif "cbdc" in text or "digital currency" in text:
        return "CBDC"
    elif "instant" in text or "real-time" in text or "fednow" in text:
        return "Instant Payments"
    elif "card" in text or "visa" in text or "mastercard" in text:
        return "Card Payments"
    elif "aml" in text or "sanction" in text or "compliance" in text:
        return "AML/Compliance"
    elif "cross-border" in text or "remittance" in text:
        return "Cross-Border"
    else:
        return "Other"

def extract_deadline(text):
    matches = re.findall(r"\b(?:by|before|until)?\s*(\d{4}-\d{2}-\d{2})\b", text)
    return matches[0] if matches else "N/A"

def parse_all_feeds():
    records = []
    for jurisdiction, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "No title")
            link = entry.get("link", "#")
            published = entry.get("published", "")
            raw_summary = entry.get("summary", "")

            clean_summary = BeautifulSoup(raw_summary, "html.parser").get_text()
            short_summary = clean_summary[:300] + "..." if len(clean_summary) > 300 else clean_summary
            deadline = extract_deadline(clean_summary)

            try:
                pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z")
                pub_date_str = pub_date.strftime("%Y-%m-%d")
            except:
                pub_date_str = "N/A"

            topic = classify_regulation(title, clean_summary)

            records.append({
                "Jurisdiction": jurisdiction,
                "Title": title,
                "Regulatory Type": topic,
                "Published Date": pub_date_str,
                "Deadline": deadline,
                "Summary": short_summary,
                "Link": link
            })
    return pd.DataFrame(records)

# UI
st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("📡 PaymentsRegIQ – Structured Regulatory Feed")

df = parse_all_feeds()
if df.empty:
    st.warning("⚠️ No data found.")
    st.stop()

# Filters
jurisdictions = st.sidebar.multiselect("Jurisdiction", df["Jurisdiction"].unique(), default=list(df["Jurisdiction"].unique()))
types = st.sidebar.multiselect("Regulatory Type", df["Regulatory Type"].unique(), default=list(df["Regulatory Type"].unique()))
filtered = df[df["Jurisdiction"].isin(jurisdictions) & df["Regulatory Type"].isin(types)]

st.dataframe(filtered, use_container_width=True)
