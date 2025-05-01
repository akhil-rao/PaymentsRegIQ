import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import openai

# ✅ Load OpenAI API key securely
openai.api_key = st.secrets["OPENAI_API_KEY"]

# ✅ Trusted regulatory RSS feeds
RSS_FEEDS = {
    "BIS": "https://www.bis.org/doclist/all_pressrels.rss",
    "MAS": "https://www.mas.gov.sg/rss/NewsReleases.xml",
    "Fed": "https://www.federalreserve.gov/feeds/press_all.xml"
}

# ✅ Payment-related keywords
KEYWORDS = ["CBDC", "ISO 20022", "Sanctions", "Stablecoin", "Payments", "AML", "KYC"]

# ✅ Regulatory classifier
def classify_topic(text):
    t = text.lower()
    if "iso 20022" in t: return "ISO 20022"
    if "cbdc" in t or "central bank digital currency" in t: return "CBDC"
    if "stablecoin" in t: return "Stablecoin"
    if "aml" in t or "kyc" in t: return "AML/KYC"
    if "sanction" in t: return "Sanctions"
    if "payment" in t: return "Payments"
    return "Other"

# ✅ Article body fetcher
def fetch_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(html.content, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p"))
        return text if len(text) > 200 else ""
    except:
        return ""

# ✅ GPT structuring
def gpt_extract(entry_text):
    prompt = f"""
You're a regulatory analyst. Extract the following structured information:

Text:
{entry_text[:4000]}

Return in this format:
Title:
Jurisdiction:
Published Date:
Deadline (if any):
Regulatory Type:
Summary (2–3 lines):
"""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        return "GPT parse failed."

# ✅ Streamlit UI
st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("📡 PaymentsRegIQ – Structured Regulatory Feed")

all_entries = []
with st.spinner("Fetching and analyzing authoritative sources..."):
    for jurisdiction, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", "")
            text = fetch_article_content(link) or summary
            if not any(k.lower() in (title + summary + text).lower() for k in KEYWORDS):
                continue
            topic = classify_topic(title + " " + text)
            structured = gpt_extract(title + "\n" + text)
            all_entries.append({
                "Jurisdiction": jurisdiction,
                "Title": title,
                "Regulatory Type": topic,
                "Published Date": published,
                "Structured Summary": structured,
                "Link": link
            })

df = pd.DataFrame(all_entries).drop_duplicates(subset=["Title", "Link"])

# ✅ Filters
st.sidebar.header("🔎 Filters")
types = st.sidebar.multiselect("Regulatory Type", df["Regulatory Type"].unique(), default=list(df["Regulatory Type"].unique()))
juris = st.sidebar.multiselect("Jurisdiction", df["Jurisdiction"].unique(), default=list(df["Jurisdiction"].unique()))
filtered = df[df["Regulatory Type"].isin(types) & df["Jurisdiction"].isin(juris)]

st.markdown(f"### {len(filtered)} regulatory updates found")
st.dataframe(filtered, use_container_width=True)
