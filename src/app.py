import streamlit as st
import pandas as pd
import time
from typing import Optional, Dict

from main import process_profile
from chrome_setup import setup_chrome_driver
from proxy_helper import WebshareProxyManager, ProxyscrapeJSONManager
from search_engines import get_search_engine


class LinkedInParserApp:
    def __init__(self) -> None:
        st.set_page_config(page_title="LinkedIn Parser", page_icon="🔍", layout="wide")
        if "proxy_info" not in st.session_state:
            st.session_state.proxy_info = {
                "current_proxy": None,
                "rotations": 0,
                "last_change": "No changes",
            }
        if "results" not in st.session_state:
            st.session_state.results = []
        if "driver" not in st.session_state:
            st.session_state.driver = None
        if "metrics_container" not in st.session_state:
            st.session_state.metrics_container = None

    def create_sidebar(self) -> Dict:
        """Create sidebar with settings."""
        with st.sidebar:
            st.header("Settings")
            search_engine = st.selectbox(
                "Search engine",
                ["google", "bing", "duckduckgo"],
                help="Select search engine for profile search",
            )
            proxy_type = st.selectbox(
                "Proxy type",
                ["none", "webshare", "proxyscrape"],
                help="Select proxy type",
            )
            proxy_api_key = None
            if proxy_type != "none":
                proxy_api_key = st.text_input(
                    "API key for proxy",
                    type="password",
                    help="Enter your API key for proxy service",
                )
            headless = st.checkbox(
                "Headless mode",
                value=False,
                help="Run browser without graphical interface",
            )
            delay = st.slider(
                "Delay between requests (sec)",
                min_value=1,
                max_value=30,
                value=5,
                help="Set delay between requests",
            )
            return {
                "search_engine": search_engine,
                "proxy_type": proxy_type,
                "proxy_api_key": proxy_api_key,
                "headless": headless,
                "delay": delay,
            }

    def update_proxy_info(self) -> None:
        """Update proxy information with full cleanup and rewrite"""
        proxy_info = st.session_state.proxy_info

        # Clean the container before updating
        st.session_state.metrics_container.empty()

        # Create new metrics in the cleaned container
        with st.session_state.metrics_container:
            col1, col2, col3 = st.columns(3)
            with col1:
                if proxy_info["current_proxy"]:
                    proxy_str = (
                        f"{proxy_info['current_proxy'].get('proxy_address', 'N/A')}"
                        f"({proxy_info['current_proxy'].get('country_code', 'N/A')})"
                    )
                else:
                    proxy_str = "Not used"
                st.metric("Current proxy", proxy_str)
            with col2:
                st.metric("Number of rotations", proxy_info["rotations"])
            with col3:
                st.metric("Last change", proxy_info["last_change"])

    def setup_proxy(self, proxy_type: str, api_key: str) -> Optional[Dict]:
        """Setup proxy manager with immediate state update"""
        proxy = None
        if proxy_type == "webshare" and api_key:
            proxy_manager = WebshareProxyManager(api_key=api_key)
            proxy = proxy_manager.get_current_proxy()
        elif proxy_type == "proxyscrape" and api_key:
            proxy_manager = ProxyscrapeJSONManager(api_url=api_key)
            proxy = proxy_manager.get_current_proxy()

        if proxy:
            st.session_state.proxy_info.update(
                {
                    "current_proxy": proxy,
                    "rotations": st.session_state.proxy_info["rotations"] + 1,
                    "last_change": time.strftime("%H:%M:%S"),
                }
            )
            self.update_proxy_info()

        return proxy

    def process_file(self, file, settings) -> None:
        """Process uploaded file."""
        if file is None:
            return

        df = pd.read_csv(file)
        if "prooflink" not in df.columns:
            st.error("CSV file must contain 'prooflink' column!")
            return

        profiles = df["prooflink"].dropna().tolist()
        total_profiles = len(profiles)

        if total_profiles == 0:
            st.warning("No profiles found for processing!")
            return

        progress_bar = st.progress(0)
        status_text = st.empty()
        results_container = st.empty()

        proxy = self.setup_proxy(settings["proxy_type"], settings["proxy_api_key"])
        search_engine = get_search_engine(settings["search_engine"])
        authwall_count = 0

        try:
            if st.session_state.driver is None:
                st.session_state.driver = setup_chrome_driver(
                    proxy=proxy, headless=settings["headless"]
                )

            for i, profile_url in enumerate(profiles, 1):
                status_text.text(
                    f"Processing profile {i}/{total_profiles}: {profile_url}"
                )

                result = process_profile(
                    st.session_state.driver, profile_url, search_engine
                )

                if result.get("IPChange") == "authwall":
                    authwall_count += 1
                    if authwall_count >= 5:
                        proxy = self.setup_proxy(
                            settings["proxy_type"], settings["proxy_api_key"]
                        )
                        if proxy:
                            st.session_state.driver.quit()
                            st.session_state.driver = setup_chrome_driver(
                                proxy=proxy, headless=settings["headless"]
                            )
                            result["IPChange"] = "rotation"
                            authwall_count = 0
                else:
                    authwall_count = 0

                st.session_state.results.append(result)

                results_df = pd.DataFrame(st.session_state.results)
                results_container.dataframe(results_df)

                progress_bar.progress(i / total_profiles)
                self.update_proxy_info()
                time.sleep(settings["delay"])

            st.success("Parsing completed!")

        except Exception as e:
            st.error(f"Error during parsing: {str(e)}")

        finally:
            if st.session_state.driver:
                st.session_state.driver.quit()
                st.session_state.driver = None

    def run(self) -> None:
        """Main method to run the application"""
        st.title("LinkedIn Parser")

        # Create an empty container for metrics
        st.session_state.metrics_container = st.empty()

        # Initialize metrics with initial values
        self.update_proxy_info()
        st.markdown("---")

        settings = self.create_sidebar()

        uploaded_file = st.file_uploader(
            "Upload CSV file with profiles",
            type=["csv"],
            help="File must contain 'prooflink' column with profile URLs",
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Start parsing", disabled=uploaded_file is None):
                self.process_file(uploaded_file, settings)

        with col2:
            if st.button("Clear results"):
                st.session_state.results = []
                st.session_state.proxy_info = {
                    "current_proxy": None,
                    "rotations": 0,
                    "last_change": "No changes",
                }
                self.update_proxy_info()
                st.experimental_rerun()

        if st.session_state.results:
            st.header("Results")
            results_df = pd.DataFrame(st.session_state.results)
            st.dataframe(results_df, use_container_width=True)

            csv = results_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download results",
                csv,
                "linkedin_results.csv",
                "text/csv",
                key="download-csv",
            )


if __name__ == "__main__":
    app = LinkedInParserApp()
    app.run()
