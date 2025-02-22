# search_engines.py
import time
import random
from abc import ABC, abstractmethod
from typing import Optional
import urllib.parse

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

################################################
# Example simplified integration of 2captcha
################################################


def solve_recaptcha_2captcha(
    api_key: str, site_key: str, page_url: str, max_wait=120
) -> Optional[str]:
    pass


def inject_recaptcha_response(driver: WebDriver, recaptcha_response: str):
    pass


################################################
# Base class
################################################


class BaseSearchEngine(ABC):
    """
    Base class for all search engines.
    """

    @abstractmethod
    def open_homepage(self, driver: WebDriver) -> None:
        """Opens the main page of the search engine."""
        pass

    @abstractmethod
    def accept_cookies(self, driver: WebDriver) -> None:
        """Clicks "Accept cookies" if needed."""
        pass

    @abstractmethod
    def check_for_captcha(self, driver: WebDriver) -> bool:
        pass

    @abstractmethod
    def perform_search(self, driver: WebDriver, query: str) -> None:
        pass

    @abstractmethod
    def extract_linkedin_url(self, driver: WebDriver) -> Optional[str]:
        pass

    def search_linkedin_profile(self, driver: WebDriver, query: str) -> Optional[str]:
        """
        Universal method: opens the main page, if needed accepts cookies,
        checks/solves captcha, enters query, again captcha, extracts LinkedIn link.
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                # Step 1: open the main page
                self.open_homepage(driver)
                time.sleep(random.uniform(1.5, 3.0))

                # Step 2: click cookies
                self.accept_cookies(driver)

                # Step 3: check/solve captcha
                if self.check_for_captcha(driver):
                    print(
                        "It seems there is a captcha."
                        "Solve it manually or automatically."
                    )
                    input("Press Enter when ready to continue...")
                    retry_count += 1
                    continue

                # Step 4: enter query
                self.perform_search(driver, query)
                time.sleep(random.uniform(2, 4))

                # Step 5: again captcha?
                if self.check_for_captcha(driver):
                    print(
                        "Captcha after the request. Solve it manually or automatically."
                    )
                    input("Press Enter when you solved the captcha...")
                    retry_count += 1
                    continue

                # Step 6: extract the link
                found_url = self.extract_linkedin_url(driver)
                return found_url

            except Exception as e:
                print(f"Error during search: {e}")
                retry_count += 1
                time.sleep(random.uniform(2, 5))

        print("Maximum number of search attempts exceeded.")
        return None


################################################
# Google
################################################


class GoogleSearchEngine(BaseSearchEngine):
    """
    Implementation of BaseSearchEngine for Google.
    """

    def open_homepage(self, driver: WebDriver) -> None:
        driver.get("https://www.google.com")

    def accept_cookies(self, driver: WebDriver) -> None:
        try:
            accept_button = driver.find_element(By.ID, "L2AGLb")
            accept_button.click()
        except NoSuchElementException:
            pass

    def check_for_captcha(self, driver: WebDriver) -> bool:

        page_source = driver.page_source.lower()
        current_url = driver.current_url.lower()

        captcha_indicators = [
            "unusual traffic" in page_source,
            "captcha" in page_source,
            "verify you're a human" in page_source,
            current_url.startswith("https://www.google.com/sorry"),
        ]
        if any(captcha_indicators):
            print("Captcha detected")
            return True

        return False

    def perform_search(self, driver: WebDriver, query: str) -> None:
        search_box = driver.find_element(By.NAME, "q")
        search_box.clear()
        search_box.send_keys(query)
        time.sleep(random.uniform(0.5, 1.5))
        search_box.send_keys(Keys.ENTER)

    def extract_linkedin_url(self, driver: WebDriver) -> Optional[str]:
        results = driver.find_elements(By.CSS_SELECTOR, "div.g a")
        for r in results:
            href = r.get_attribute("href")
            if href and "linkedin.com/in/" in href:
                return href
        return None


################################################
# Bing
################################################


class BingSearchEngine(BaseSearchEngine):
    def open_homepage(self, driver: WebDriver) -> None:
        driver.get("https://www.bing.com")

    def accept_cookies(self, driver: WebDriver) -> None:
        try:
            accept_btn = driver.find_element(By.ID, "bnp_btn_accept")
            accept_btn.click()
        except NoSuchElementException:
            pass

    def check_for_captcha(self, driver: WebDriver) -> bool:
        page_source = driver.page_source.lower()
        if (
            "please verify you're not a robot" in page_source
            or "captcha" in page_source
        ):
            return True
        return False

    def perform_search(self, driver: WebDriver, query: str) -> None:
        query = query.strip()
        linkedin_query = f'"{query}" site:linkedin.com/in/'
        encoded_query = urllib.parse.quote_plus(linkedin_query)
        search_url = f"https://www.bing.com/search?q={encoded_query}&first=1"
        driver.get(search_url)
        time.sleep(3)

    def extract_linkedin_url(self, driver: WebDriver) -> Optional[str]:
        links = driver.find_elements(By.CSS_SELECTOR, "li.b_algo h2 a")
        for link in links:
            href = link.get_attribute("href")
            if href and "linkedin.com/in/" in href:
                return href
        return None


################################################
# DuckDuckGo
################################################


class DuckDuckGoSearchEngine(BaseSearchEngine):
    def open_homepage(self, driver: WebDriver) -> None:
        driver.get("https://duckduckgo.com/")
        time.sleep(2)

    def accept_cookies(self, driver: WebDriver) -> None:
        try:
            consent_button = driver.find_element(
                By.CSS_SELECTOR, "button[data-testid='cookie-consent-button']"
            )
            consent_button.click()
        except NoSuchElementException:
            pass

    def check_for_captcha(self, driver: WebDriver) -> bool:
        return False

    def perform_search(self, driver: WebDriver, query: str) -> None:
        try:
            search_box = driver.find_element(
                By.CSS_SELECTOR,
                "input[name='q'], #search_form_input_homepage, #searchbox_input",
            )
        except NoSuchElementException:
            search_box = driver.find_element(By.CSS_SELECTOR, "#search_form_input")

        search_box.clear()
        search_box.send_keys(query)
        time.sleep(random.uniform(0.5, 1.5))
        search_box.send_keys(Keys.ENTER)

    def extract_linkedin_url(self, driver: WebDriver) -> Optional[str]:
        selectors = [
            "article a[data-testid='result-title-a']",
            "a.result__a",
            ".results a",
        ]

        for selector in selectors:
            results = driver.find_elements(By.CSS_SELECTOR, selector)
            for link in results:
                href = link.get_attribute("href")
                if href and "linkedin.com/in/" in href:
                    return href
        return None


################################################
# Factory
################################################


def get_search_engine(engine_name: str) -> BaseSearchEngine:
    engine_name = engine_name.lower()
    if engine_name == "google":
        return GoogleSearchEngine()
    elif engine_name == "bing":
        return BingSearchEngine()
    elif engine_name == "duckduckgo":
        return DuckDuckGoSearchEngine()
    else:
        print(f"[WARNING] Unknown engine '{engine_name}', defaulting to Google.")
        return GoogleSearchEngine()
