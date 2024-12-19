import streamlit as st
import pandas as pd
import requests
import plotly.express as px
from io import BytesIO

# Set up the app
st.set_page_config(page_title="Crypto Trader Dashboard", layout="wide")
st.title("📊 Crypto Trader Dashboard")


# Fetch the list of cryptocurrencies (example using CoinGecko API)
@st.cache_data
def get_crypto_list():
    url = "https://api.coingecko.com/api/v3/coins/list"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return pd.DataFrame(data)
    else:
        st.error("Failed to fetch cryptocurrencies. Try again later.")
        return pd.DataFrame()


crypto_list = get_crypto_list()

# User input for cryptocurrency selection
st.sidebar.header("Filter Options")
cryptos = st.sidebar.selectbox(
    "Select Cryptocurrency", crypto_list["id"] if not crypto_list.empty else []
)

# User input for data range
date_option = st.sidebar.radio("Select Data Range", ["Last N Days", "Custom Range"])
if date_option == "Last N Days":
    days = st.sidebar.slider("Number of Days", 1, 365, 30)
else:
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")


# Fetch historical data
@st.cache_data
def fetch_crypto_data(crypto_id, days=None, start_date=None, end_date=None):
    if days:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart?vs_currency=usd&days={days}"
    else:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart/range?vs_currency=usd&from={start_date}&to={end_date}"

    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        prices = pd.DataFrame(data["prices"], columns=["timestamp", "price"])
        prices["timestamp"] = pd.to_datetime(prices["timestamp"], unit="ms")
        return prices
    else:
        st.error("Failed to fetch data. Please try again later.")
        return pd.DataFrame()


# Fetch news data
@st.cache_data
def fetch_crypto_news(crypto_name):
    api_key = "348a1315be2241d29aedb4ca2c1f2bcf"  # Replace with your NewsAPI key
    url = f"https://newsapi.org/v2/everything?q={crypto_name}&apiKey={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()["articles"]
    else:
        st.warning("Failed to fetch news articles. Try again later.")
        return []


# Function to generate download links
def generate_download_link(df, file_format):
    if file_format == 'CSV':
        return df.to_csv(index=False).encode('utf-8')
    elif file_format == 'Excel':
        output = BytesIO()
        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()
    elif file_format == 'JSON':
        return df.to_json(orient="records").encode("utf-8")


if cryptos:
    # Fetch historical data
    if date_option == "Last N Days":
        data = fetch_crypto_data(cryptos, days=days)
    else:
        data = fetch_crypto_data(
            cryptos,
            start_date=pd.Timestamp(start_date).timestamp(),
            end_date=pd.Timestamp(end_date).timestamp(),
        )

    # Display data and visualizations
    if not data.empty:
        # Add additional columns
        data["change"] = data["price"].pct_change() * 100
        data.rename(columns={"price": "Price (USD)"}, inplace=True)

        st.subheader("📈 Cryptocurrency Data")
        st.dataframe(data)

        # Download Button
        st.subheader("📥 Download Data")
        file_format = st.radio("Select Format", ["CSV", "Excel", "JSON"])
        if st.button(f"Download as {file_format}"):
            file_data = generate_download_link(data, file_format)
            if file_format == "CSV":
                st.download_button("Download CSV", data=file_data, file_name=f"{cryptos}_data.csv", mime="text/csv")
            elif file_format == "Excel":
                st.download_button("Download Excel", data=file_data, file_name=f"{cryptos}_data.xlsx",
                                   mime="application/vnd.ms-excel")
            elif file_format == "JSON":
                st.download_button("Download JSON", data=file_data, file_name=f"{cryptos}_data.json",
                                   mime="application/json")

        # Visualization
        st.subheader("📊 Visualizations")
        graph_option = st.radio("Select Visualization", ["Line Graph", "Current Price Graph"])

        if graph_option == "Line Graph":
            fig = px.line(data, x="timestamp", y="Price (USD)", title="Price Over Time")
            st.plotly_chart(fig)
        elif graph_option == "Current Price Graph":
            st.bar_chart(data.set_index("timestamp")["Price (USD)"])

    # Fetch and display news
    st.subheader("📰 Latest News")
    news_articles = fetch_crypto_news(cryptos)
    if news_articles:
        for article in news_articles[:5]:  # Display the top 5 articles
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.write(article['description'])
            st.write(f"Published At: {article['publishedAt']}")
            st.markdown("---")
    else:
        st.info("No news articles found for this cryptocurrency.")
else:
    st.warning("No cryptocurrency selected.")
