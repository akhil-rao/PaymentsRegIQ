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

# --- ECB Scraper ---
def scrape_ecb():
    try:
        url = "https://www.ecb.europa.eu/press/pr/date/html/index.en.html"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select(".ecb-publishable-item")
        results = []
        for item in items[:5]:
            a_tag = item.select_one("a")
            date_tag = item.select_one(".date")
            if not a_tag or not date_tag:
                continue
            title = a_tag.text.strip()
            link = "https://www.ecb.europa.eu" + a_tag["href"]
            date_text = date_tag.text.strip()
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
    except Exception as e:
        print(f"[ECB SCRAPER ERROR]: {e}")
        return []

# --- Fed Scraper ---
def scrape_fed():
    try:
        url = "https://www.federalreserve.gov/newsevents/pressreleases.htm"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        items = soup.select(".item")
        results = []
        for item in items[:5]:
            a_tag = item.select_one("a")
            date_tag = item.select_one(".article__time")
            if not a_tag or not date_tag:
                continue
            title = a_tag.text.strip()
            link = "https://www.federalreserve.gov" + a_tag["href"]
            date_text = date_tag.text.strip()
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
    except Exception as e:
        print(f"[FED SCRAPER ERROR]: {e}")
        return []

# --- Combine all data ---
def get_all_data():
    return pd.DataFrame(scrape_ecb() + scrape_fed())

# --- Streamlit UI ---
st.set_page_config(page_title="PaymentsRegIQ", layout="wide")
st.title("🌐 PaymentsRegIQ - Regulatory Feed for Payments Industry")
st.markdown("Auto-collated updates across CBDC, ISO 20022, cards, and instant payments.")

# --- Load data ---
df = get_all_data()

# --- Validate structure ---
required_columns = {"Title", "Jurisdiction", "Publication Date", "Regulatory Type", "Summary", "Deadline", "Source URL"}
if df.empty:
    st.warning("⚠️ No data found from ECB or Fed. Try again later.")
    st.stop()
elif not required_columns.issubset(df.columns):
    st.error("⚠️ Data loaded but is missing expected columns. Check scraper logic.")
    st.write("Columns present:", df.columns.tolist())
    st.stop()

# --- Debug preview ---
st.write("🔍 Debug Preview:", df.head())

# --- Filters and display ---
jurisdictions = st.sidebar.multiselect("Filter by Jurisdiction", df["Jurisdiction"].unique(), default=list(df["Jurisdiction"].unique()))
reg_types = st.sidebar.multiselect("Filter by Regulatory Type", df["Regulatory Type"].unique(), default=list(df["Regulatory Type"].unique()))
filtered_df = df[df["Jurisdiction"].isin(jurisdictions) & df["Regulatory Type"].isin(reg_types)]

st.write(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.dataframe(filtered_df.sort_values(by="Publication Date", ascending=False), use_container_width=True)
