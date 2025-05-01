import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import re
import openai
from urllib.parse import urlparse

# Load API key from secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]

# Keywords for monitoring
KEYWORDS = [
    "CBDC",
    "Central Bank Digital Currency",
    "Sanctions",
    "Stablecoin",
    "Payments",
    "ISO 20022",
    "AML",
    "KYC"
]

# Classify the regulatory type
def classify_topic(text):
    t = text.lower()
    if "iso 20022" in t or "structured" in t:
        return "ISO 20022"
    elif "cbdc" in t or "central bank digital currency" in t:
        return "CBDC"
    elif "stablecoin" in t:
        return "Stablecoin"
    elif "aml" in t or "kyc" in t:
        return "AML/KYC"
    elif "sanction" in t:
        return "Sanctions"
    elif "payment" in t:
        return "Payments"
    else:
        return "Other"

# Use GPT to summarize the content
def simplify_summary(summary):
    prompt = f"Summarize the following regulatory news content in one clear sentence for financial compliance professionals:\n\n{summary}\n\nSummary:"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception:
        return summary

# Extract domain name
def extract_domain(url):
    try:
        return urlparse(url).netloc.replace('www.', '')
    except:
        return "Unknown"

# Parse RSS feed from Google News
def get_alerts_from_google_news(keyword):
    feed_url = f"https://news.google.com/rss/search?q={keyword.replace(' ', '%20')}"
    feed = feedparser.parse(feed_url)
    entries = []
    for entry in feed.entries:
        title = entry.get("title", "")
        link = entry.get("link", "")
        summary = entry.get("summary", "")
        published = entry.get("published", "")
        pub_date = ""
        try:
            pub_date = datetime.strptime(published, "%a, %d %b %Y %H:%M:%S %Z").strftime("%Y-%m-%d")
        except:
            pub_date = published

        topic = classify_topic(title + " " + summary)
        clean_summary = simplify_summary(summary)
        domain = extract_domain(link)

        entries.append({
            "Keyword": keyword,
            "Title": title,
            "Regulatory Type": topic,
            "Published Date": pub_date,
            "Summary": clean_summary,
            "Link": link,
            "Source": domain,
            "Jurisdiction": "Unknown"
        })
    return entries

# Streamlit UI
st.set_page_config(page_title="PaymentsRegIQ - AI Regulatory Feed", layout="wide")
st.title("📡 PaymentsRegIQ – Real-Time AI-Powered Regulatory Feed")

# Fetch alerts
with st.spinner("Fetching and analyzing alerts..."):
    all_entries = []
    for kw in KEYWORDS:
        all_entries.extend(get_alerts_from_google_news(kw))

df = pd.DataFrame(all_entries).drop_duplicates(subset=["Title", "Link"])

# UI Filters
st.sidebar.header("Filters")
selected_types = st.sidebar.multiselect("Regulatory Type", sorted(df["Regulatory Type"].unique()), default=list(df["Regulatory Type"].unique()))
selected_sources = st.sidebar.multiselect("Source", sorted(df["Source"].unique()), default=list(df["Source"].unique()))

filtered_df = df[df["Regulatory Type"].isin(selected_types) & df["Source"].isin(selected_sources)]

st.markdown(f"#### Results: {len(filtered_df)} entries")
st.dataframe(filtered_df, use_container_width=True)
