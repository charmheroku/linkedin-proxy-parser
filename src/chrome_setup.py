# chrome_setup.py
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

try:
    from seleniumwire import webdriver as wire_webdriver
except ImportError:
    wire_webdriver = None


def setup_chrome_driver(proxy=None, headless: bool = False, verify_ssl: bool = False):
    """
    A function that sets up and returns a Chrome driver.

    """
    chrome_options = Options()

    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-software-rasterizer")
    chrome_options.add_argument("--disable-webgl")
    chrome_options.add_argument("--disable-webgl-image-chromium")
    chrome_options.add_argument("--disable-accelerated-2d-canvas")
    chrome_options.add_argument("--disable-accelerated-video-decode")

    # Stop WebRTC
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-features=WebRtcHideLocalIpsWithMdns")
    chrome_options.add_argument("--enable-features=WebRtcRemoteEventLog")

    # Other important settings
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-infobars")
    chrome_options.add_argument("--disable-breakpad")
    chrome_options.add_argument("--disable-component-update")
    chrome_options.add_argument("--disable-background-networking")

    # Disable logging
    chrome_options.add_argument("--log-level=3")
    chrome_options.add_argument("--silent")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--lang=en")

    if headless:
        chrome_options.add_argument("--headless=new")

    # Several user-agents
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        "AppleWebKit/537.36 (KHTML, like Gecko)"
        "Chrome/112.0.5615.49 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0)"
        "Gecko/20100101 Firefox/110.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
        "AppleWebKit/605.1.15 (KHTML, like Gecko)"
        "Version/15.1 Safari/605.1.15",
    ]
    chrome_options.add_argument(f"user-agent={random.choice(user_agents)}")

    service = Service(ChromeDriverManager().install())

    # If a proxy is needed
    if proxy and wire_webdriver is not None:
        ip = proxy["proxy_address"]
        port = proxy["port"]
        username = proxy.get("username")
        password = proxy.get("password")

        print(f"Using proxy: {ip}:{port} (Country: {proxy.get('country_code')})")

        if username and password:
            http_proxy = f"http://{username}:{password}@{ip}:{port}"
            https_proxy = f"https://{username}:{password}@{ip}:{port}"
        else:
            # Proxy without authentication
            http_proxy = f"http://{ip}:{port}"
            https_proxy = f"https://{ip}:{port}"

        seleniumwire_options = {
            "proxy": {
                "http": http_proxy,
                "https": https_proxy,
                "verify_ssl": verify_ssl,
            }
        }

        driver = wire_webdriver.Chrome(
            service=service,
            options=chrome_options,
            seleniumwire_options=seleniumwire_options,
        )
    else:
        # Without a proxy
        driver = webdriver.Chrome(service=service, options=chrome_options)

    # Selenium masking
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
        },
    )
    return driver
