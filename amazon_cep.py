import os
import json
import uuid
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from telegram_cep import send_message

URL = "https://www.amazon.com.tr/s?i=electronics&rh=n%3A12466496031%2Cn%3A13709880031%2Cn%3A13709907031%2Cp_123%3A110955%257C32374&s=price-desc-rank"
COOKIE_PATH = "cookie_cep.json"
SENT_FILE = "send_products_elektronik.txt"

def load_cookies(driver):
    if not os.path.exists(COOKIE_PATH):
        print("❌ Cookie dosyası bulunamadı.")
        return

    with open(COOKIE_PATH, "r", encoding="utf-8") as f:
        cookies = json.load(f)

    for cookie in cookies:
        try:
            driver.add_cookie({
                "name": cookie["name"],
                "value": cookie["value"],
                "domain": cookie["domain"],
                "path": cookie.get("path", "/")
            })
        except Exception as e:
            print(f"⚠️ Cookie eklenemedi: {cookie.get('name')} → {e}")

def get_driver():
    profile_id = str(uuid.uuid4())
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f"--user-data-dir=/tmp/chrome-profile-{profile_id}")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/115 Safari/537.36")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def load_sent_titles():
    if not os.path.exists(SENT_FILE):
        return set()
    with open(SENT_FILE, "r", encoding="utf-8") as f:
        return set(line.strip() for line in f)

def save_sent_titles(products):
    with open(SENT_FILE, "a", encoding="utf-8") as f:
        for product in products:
            f.write(product["title"].strip() + "\n")

def run():
    driver = get_driver()
    driver.get("https://www.amazon.com.tr")
    time.sleep(2)
    load_cookies(driver)
    driver.get(URL)

    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-component-type='s-search-result']"))
        )
    except:
        print("⚠️ Sayfa yüklenemedi.")
        driver.quit()
        return

    items = driver.find_elements(By.CSS_SELECTOR, "div[data-component-type='s-search-result']")
    print(f"🔍 {len(items)} ürün bulundu.")

    products = []
    for item in items[:5]:  # İlk 5 ürünü kontrol et
        try:
            title = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("alt")
            price_whole = item.find_element(By.CSS_SELECTOR, ".a-price-whole").text.strip()
            price_fraction = item.find_element(By.CSS_SELECTOR, ".a-price-fraction").text.strip()
            price = f"{price_whole},{price_fraction} TL"
            image = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("src")
            link = item.find_element(By.CSS_SELECTOR, "a.a-link-normal").get_attribute("href")

            products.append({
                "title": title,
                "price": price,
                "image": image,
                "link": link
            })
        except Exception as e:
            print("⚠️ Ürün parse hatası:", e)
            continue

    driver.quit()

    sent_titles = load_sent_titles()
    new_products = [p for p in products if p["title"].strip() not in sent_titles]

    if new_products:
        for product in new_products:
            send_message(product)
        save_sent_titles(new_products)
    else:
        print("⚠️ Yeni ürün bulunamadı.")

if __name__ == "__main__":
    run()
