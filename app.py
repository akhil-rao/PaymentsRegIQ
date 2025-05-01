import streamlit as st
import feedparser
import pandas as pd
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# ✅ Load OpenAI key from Streamlit secrets
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ✅ Authoritative regulatory RSS feeds
RSS_FEEDS = {
    "BIS": "https://www.bis.org/doclist/all_pressrels.rss",
    "MAS": "https://www.mas.gov.sg/rss/NewsReleases.xml",
    "Fed": "https://www.federalreserve.gov/feeds/press_all.xml"
}

# ✅ Keywords to match relevant news
KEYWORDS = ["CBDC", "ISO 20022", "Sanctions", "Stablecoin", "Payments", "AML", "KYC"]

# ✅ Classify regulatory topic
def classify_topic(text):
    t = text.lower()
    if "iso 20022" in t:
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
    return "Other"

# ✅ Try to fetch full body of article
def fetch_article_content(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        html = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(html.content, "html.parser")
        text = " ".join(p.get_text() for p in soup.find_all("p"))
        return text if len(text) > 200 else ""
    except:
        return ""

# ✅ Use GPT (v1 SDK) to extract structure
def gpt_extract(entry_text):
    prompt = f"""
You're a regulatory analyst. Extract the following structured information from the text below:

Text:
{entry_text[:4000]}

Return this format:
Title:
Jurisdiction:
Published Date:
Deadline (if any):
Regulatory Type:
Summary (2–3 lines):
"""
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"GPT parse failed: {e}"

# ✅ Streamlit page config
st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("📡 PaymentsRegIQ – Structured Regulatory Intelligence")

# ✅ GPT Test
st.markdown("#### 🧠 Testing OpenAI connection...")
try:
    _ = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Summarize CBDC in one sentence."}]
    )
    st.success("✅ OpenAI GPT is working.")
except Exception as e:
    st.error(f"❌ GPT connection failed: {e}")
    st.stop()

# ✅ Process Feeds
with st.spinner("⏳ Fetching regulatory content from BIS, MAS, Fed..."):
    records = []
    for jurisdiction, url in RSS_FEEDS.items():
        feed = feedparser.parse(url)
        for entry in feed.entries:
            title = entry.get("title", "")
            summary = entry.get("summary", "")
            link = entry.get("link", "")
            published = entry.get("published", "")

            content = fetch_article_content(link) or summary
            if not any(k.lower() in (title + content).lower() for k in KEYWORDS):
                continue

            classification = classify_topic(title + " " + content)
            structured = gpt_extract(title + "\n" + content)

            records.append({
                "Jurisdiction": jurisdiction,
                "Title": title,
                "Regulatory Type": classification,
                "Published Date": published,
                "Structured Summary": structured,
                "Link": link
            })

# ✅ Display
df = pd.DataFrame(records).drop_duplicates(subset=["Title", "Link"])

# ✅ Sidebar filters
st.sidebar.header("🔍 Filter Feed")
types = st.sidebar.multiselect("Regulatory Type", sorted(df["Regulatory Type"].unique()), default=list(df["Regulatory Type"].unique()))
juris = st.sidebar.multiselect("Jurisdiction", sorted(df["Jurisdiction"].unique()), default=list(df["Jurisdiction"].unique()))

filtered_df = df[df["Regulatory Type"].isin(types) & df["Jurisdiction"].isin(juris)]

# ✅ Final Output
st.markdown(f"### {len(filtered_df)} results")
st.dataframe(filtered_df, use_container_width=True)
