# parser_logic.py
import time
import random
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


def extract_linkedin_info(driver, url: str) -> dict:
    """
    Extracts LinkedIn profile information.
    """
    info = {}

    driver.get(url)
    time.sleep(random.uniform(1, 2))  # waiting for page loading

    current_url = driver.current_url.lower()
    is_authwall = "authwall" in current_url

    if is_authwall:
        info = {
            "url": url,
            "name": None,
            "location": None,
            "current_position": None,
            "is_authwall": True,
        }
        print("The page is under the authwall.")
        return info

    name = None
    location = None
    current_position = None

    name_selectors = [
        "h1.text-heading-xlarge",
        "h1.top-card-layout__title",
        ".pv-text-details__left-panel h1",
        "h1",
    ]
    for sel in name_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text:
                name = text
                break
        except NoSuchElementException:
            continue

    location_selectors = [
        ".top-card-layout__card span.top-card__subline-item",
        "span.location",
        ".pv-text-details__left-panel div.text-body-small",
        ".profile-info-subheader .not-first-middot span:first-child",
    ]
    for sel in location_selectors:
        try:
            el = driver.find_element(By.CSS_SELECTOR, sel)
            text = el.text.strip()
            if text:
                location = text
                break
        except NoSuchElementException:
            continue

    if not is_authwall:
        position_selectors = [
            ".experience-item__title",
            ".top-card-layout__headline",
            ".pv-text-details__left-panel div.text-body-medium.break-words",
        ]
        for sel in position_selectors:
            try:
                el = driver.find_element(By.CSS_SELECTOR, sel)
                text = el.text.strip()
                if text:
                    current_position = text
                    break
            except NoSuchElementException:
                continue

    info = {
        "url": url,
        "name": name,
        "location": location,
        "current_position": current_position,
        "is_authwall": is_authwall,
    }
    print("Profile information:", info)
    return info
