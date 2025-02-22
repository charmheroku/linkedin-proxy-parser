# main.py
import os
import time
import random
import csv
from typing import Dict, Any, List

from sheets_helper import read_profiles_csv, read_profiles_gsheet
from chrome_setup import setup_chrome_driver
from proxy_helper import WebshareProxyManager
from search_engines import get_search_engine
from parser_logic import extract_linkedin_info

OUTPUT_FILE = "linkedin_results.csv"
FIELDNAMES = ["Original", "LinkedInURL", "FullName", "Location", "IPChange"]


def write_result(row: Dict[str, Any]) -> None:
    """Writes one line to CSV in append mode."""
    file_exists = os.path.exists(OUTPUT_FILE)
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
        csvfile.flush()


def process_profile(driver, profile_url: str, search_engine) -> Dict[str, Any]:
    """
    Processes one profile using the provided driver.
    Function:
      - searches for a LinkedIn link through the search engine,
      - goes to the profile page and extracts data.
    IMPORTANT: driver is not closed inside this function.
    """
    found_url = search_engine.search_linkedin_profile(driver, profile_url)
    if not found_url:
        return {
            "Original": profile_url,
            "LinkedInURL": "",
            "FullName": "",
            "Location": "",
            "IPChange": "not_found_or_captcha",
        }

    info = extract_linkedin_info(driver, found_url)
    if info["is_authwall"]:
        return {
            "Original": profile_url,
            "LinkedInURL": found_url,
            "FullName": "",
            "Location": "",
            "IPChange": "authwall",
        }

    return {
        "Original": profile_url,
        "LinkedInURL": found_url,
        "FullName": info["name"] or "",
        "Location": info["location"] or "",
        "IPChange": "",
    }


def main():
    """
    Main script:
      - Reads the list of profiles (CSV or Google Sheets),
      - Creates a driver with the current proxy (once),
      - Processes each profile, immediately appending the result to CSV,
      - When 5 consecutive authwalls (redirect to the authorization page) occur,
        the proxy rotation occurs:
        close the driver, write a line with IPChange = "rotation"
        and create a new driver.
    """
    # 1. Data source
    source_type = os.environ.get("SOURCE_TYPE", "csv").lower()
    profiles: List[str] = []
    if source_type == "csv":
        csv_path = os.environ.get("CSV_PATH", "ProfilesListExample.csv")
        print(f"Reading profiles from CSV: {csv_path}")
        profiles = read_profiles_csv(csv_path)
    elif source_type == "gsheet":
        sheet_url = os.environ.get("GSHEET_URL", "<YOUR_SHEET_URL>")
        creds_file = os.environ.get("GSHEET_CREDS", "service_account.json")
        print(f"Reading profiles from Google Sheet: {sheet_url}")
        profiles = read_profiles_gsheet(sheet_url, creds_file)
    else:
        raise ValueError(
            f"Unknown SOURCE_TYPE={source_type}. Must be 'csv' or 'gsheet'."
        )

    print(f"Loaded {len(profiles)} profile(s).")

    # 2. Initialize the proxy manager
    proxy_api_key = os.environ.get("PROXY_API_KEY", "REPLACE_WITH_YOUR_KEY")
    proxy_manager = WebshareProxyManager(api_key=proxy_api_key)

    # 3. Select the search engine
    search_engine_name = os.environ.get("SEARCH_ENGINE", "google")
    print(f"Using search engine: {search_engine_name}")
    search_engine = get_search_engine(search_engine_name)

    # 4. Create a driver once with the current proxy
    driver = setup_chrome_driver(proxy=None, headless=False)

    authwall_count = 0
    input("Press Enter when ready to continue...")

    for profile_url in profiles:
        profile_url = profile_url.strip()
        if not profile_url:
            continue
        print(f"Processing profile: {profile_url}")
        result = process_profile(driver, profile_url, search_engine)

        if result["IPChange"] == "authwall":
            authwall_count += 1
            print(f"Encountered authwall. Count: {authwall_count}")
            if authwall_count >= 5:
                print("Reached 5 consecutive authwalls. Rotating proxy...")
                result["IPChange"] = "rotation"
                write_result(result)
                try:
                    driver.quit()
                except Exception as e:
                    print("Error quitting driver:", e)
                new_proxy = proxy_manager.rotate_proxy()
                driver = setup_chrome_driver(proxy=new_proxy, headless=False)
                authwall_count = 0
                time.sleep(random.uniform(2, 5))
                continue
        else:
            authwall_count = 0

        write_result(result)
        time.sleep(random.uniform(2, 5))

    try:
        driver.quit()
    except Exception as e:
        print("Error quitting driver:", e)

    print("Done. Results appended to", OUTPUT_FILE)


if __name__ == "__main__":
    main()
