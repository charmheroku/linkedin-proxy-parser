# LinkedIn Profile Parser 🔍

[Demo Video](https://drive.google.com/file/d/1prPlvoq23gRaj2hiHwWTrQ3H9Pp7XNIz/view?usp=drive_link)

Tool for automatic collection of data from public LinkedIn profiles with support for proxy rotation and bypassing restrictions.

## 🌟 Features
- Parsing key data: profile URL, name, location, IP status
- Support for multiple search engines (Google, Bing, DuckDuckGo)
- Proxy rotation when authwall is detected
- Export results to CSV
- Graphical interface based on Streamlit

## 🛠 Technologies
![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Selenium](https://img.shields.io/badge/Selenium-4.10%2B-orange)
![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-brightgreen)

**Main stack:**
- **Web Scraping**: Selenium WebDriver + Chrome Headless
- **GUI**: Streamlit with dynamic data updates
- **Proxy management**: Webshare.io and ProxyScrape API
- **Data**: Pandas for processing and exporting

## 🚀 Main approaches
1. **Modular architecture**
   - Separate components for parsing, working with proxies and UI
   - Clear separation of business logic and presentation

2. **Robustness against blocks**
   - Automatic proxy rotation when authwall is detected
   - Exponential delay between requests
   - Browser session management

3. **Security**
   - Storing sensitive data in .env
   - Input parameter validation

## 📦 Installation

1. Clone the repository

```bash
git clone https://github.com/charmheroku/linkedin-proxy-parser.git
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Create a .env file

```bash
cp .env.example .env
```

4. Run the app

```bash
streamlit run app.py
```
## 🖥 Usage
1. Upload a CSV file with the `prooflink` column
2. Configure the parsing parameters in the sidebar
3. Start the data collection process
4. Export the results to CSV
