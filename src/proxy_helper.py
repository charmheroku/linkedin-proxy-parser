# proxy_helper.py
import random
import requests
from typing import Dict, List, Optional

BASE_URL = "https://proxy.webshare.io/api/v2"


class WebshareProxyManager:
    """
    Simple proxy manager for Webshare.io:
    - Gets a list of proxies through the API.
    - Allows returning a random/next proxy.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {"Authorization": f"Token {self.api_key}"}
        self.proxies = []
        self.current_proxy_index = -1
        self._fetch_proxies()

    def _fetch_proxies(self):
        url = (
            f"{BASE_URL}/proxy/list/"
            f"?mode=direct&page=1&page_size=25"
        )
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            data = response.json()
            self.proxies = data["results"]
            print(f"Fetched {len(self.proxies)} proxies from Webshare.io")
        else:
            raise Exception(f"Failed to fetch proxies: {response.text}")

    def get_current_proxy(self) -> Dict:

        if not self.proxies:
            self._fetch_proxies()

        proxy_data = random.choice(self.proxies)
        return {
            "proxy_address": proxy_data["proxy_address"],
            "port": proxy_data["port"],
            "username": proxy_data["username"],
            "password": proxy_data["password"],
            "country_code": proxy_data.get("country_code", "unknown"),
            "verify_ssl": False,
        }

    def rotate_proxy(self) -> Dict:

        return self.get_current_proxy()


class ProxyscrapeJSONManager:
    """
    A proxy manager for JSON responses from proxyscrape.com:
    """

    def __init__(
        self,
        api_url: str,
        allowed_countries: Optional[List[str]] = None,
        required_status: str = "Online",
        required_protocol: str = "HTTP",
    ):
        self.api_url = api_url
        self.allowed_countries = allowed_countries
        self.required_status = required_status
        self.required_protocol = required_protocol
        self.proxies = self._fetch_proxies()

    def _fetch_proxies(self) -> List[Dict]:
        print(f"Fetching proxy list from: {self.api_url}")
        resp = requests.get(self.api_url, timeout=30)
        if resp.status_code != 200:
            raise Exception(
                f"Failed to fetch proxies. Status={resp.status_code}, Body={resp.text}"
            )

        data_json = resp.json()
        if "data" not in data_json:
            raise Exception("JSON response doesn't contain 'data' field.")

        raw_list = data_json["data"]

        parsed_proxies = []
        for entry in raw_list:
            if not isinstance(entry, list) or len(entry) < 4:
                continue

            ip_port = entry[0]
            protocol = entry[1]
            status = entry[2]
            country = entry[3]

            if ":" not in ip_port:
                continue
            ip, port = ip_port.split(":", 1)

            if self.required_status and status.lower() != self.required_status.lower():
                continue

            if (
                self.required_protocol
                and protocol.lower() != self.required_protocol.lower()
            ):
                continue

            if self.allowed_countries and country.lower() not in [
                c.lower() for c in self.allowed_countries
            ]:
                continue

            parsed_proxies.append(
                {
                    "proxy_address": ip,
                    "port": port,
                    "username": None,
                    "password": None,
                    "country_code": country.lower(),
                }
            )

        print(f"Fetched {len(parsed_proxies)} proxies (after filtering).")
        return parsed_proxies

    def get_current_proxy(self) -> Dict:
        if not self.proxies:
            self.proxies = self._fetch_proxies()
        return random.choice(self.proxies)

    def rotate_proxy(self) -> Dict:
        return self.get_current_proxy()
