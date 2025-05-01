import streamlit as st
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import pandas as pd

# --- Classifier ---
def classify_topic(text):
    text = text.lower()
    if "iso 20022" in text or "structured" in text:
        return "ISO 20022"
    elif "cbdc" in text or "digital currency" in text:
        return "CBDC"
    elif "instant" in text or "real-time" in text or "fednow" in text:
        return "Instant Payments"
    elif "card" in text:
        return "Card Payments"
    elif "aml" in text or "compliance" in text or "sanctions" in text:
        return "AML/Compliance"
    elif "cross-border" in text or "remittance" in text:
        return "Cross-border"
    else:
        return "Other"

# --- Scrapers ---
def scrape_ecb():
    url = "https://www.ecb.europa.eu/press/pr/date/html/index.en.html"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.select(".ecb-publishable-item")
    results = []
    for item in items[:5]:
        title = item.select_one("a").text.strip()
        link = "https://www.ecb.europa.eu" + item.select_one("a")["href"]
        date_text = item.select_one(".date").text.strip()
        pub_date = datetime.strptime(date_text, "%d %B %Y").date()
        tag = classify_topic(title)
        results.append({
            "Title": title,
            "Jurisdiction": "ECB",
            "Publication Date": pub_date,
            "Regulatory Type": tag,
            "Summary": "See source.",
            "Deadline": "N/A",
            "Source URL": link
        })
    return results

def scrape_fed():
    url = "https://www.federalreserve.gov/newsevents/pressreleases.htm"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.select(".item")
    results = []
    for item in items[:5]:
        title = item.select_one("a").text.strip()
        link = "https://www.federalreserve.gov" + item.select_one("a")["href"]
        date_text = item.select_one(".article__time").text.strip()
        pub_date = datetime.strptime(date_text, "%B %d, %Y").date()
        tag = classify_topic(title)
        results.append({
            "Title": title,
            "Jurisdiction": "Federal Reserve",
            "Publication Date": pub_date,
            "Regulatory Type": tag,
            "Summary": "See source.",
            "Deadline": "N/A",
            "Source URL": link
        })
    return results

def scrape_swift():
    url = "https://www.swift.com/news-events/news"
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    items = soup.select(".view-news .views-row")
    results = []
    for item in items[:5]:
        title = item.select_one(".field-content").text.strip()
        link = "https://www.swift.com" + item.select_one("a")["href"]
        pub_date = datetime.today().date()
        tag = classify_topic(title)
        results.append({
            "Title": title,
            "Jurisdiction": "SWIFT",
            "Publication Date": pub_date,
            "Regulatory Type": tag,
            "Summary": "See source.",
            "Deadline": "N/A",
            "Source URL": link
        })
    return results

def get_all_data():
    return pd.DataFrame(scrape_ecb() + scrape_fed() + scrape_swift())

# --- UI ---
st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("🌐 PaymentsRegIQ - Regulatory Feed for Payments Industry")
st.markdown("Auto-collated updates across CBDC, ISO 20022, cards, and instant payments.")

df = get_all_data()
jurisdictions = st.sidebar.multiselect("Filter by Jurisdiction", df["Jurisdiction"].unique(), default=list(df["Jurisdiction"].unique()))
reg_types = st.sidebar.multiselect("Filter by Regulatory Type", df["Regulatory Type"].unique(), default=list(df["Regulatory Type"].unique()))
filtered_df = df[df["Jurisdiction"].isin(jurisdictions) & df["Regulatory Type"].isin(reg_types)]

st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.dataframe(filtered_df.sort_values(by="Publication Date", ascending=False), use_container_width=True)
