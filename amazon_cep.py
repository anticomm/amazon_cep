# ... [önceki import ve sabit tanımlar aynı kalıyor]

def normalize(text):
    return text.replace("\xa0", " ").replace("\u202f", " ").replace("\u200b", "").strip()

# ... [cookie ve driver fonksiyonları aynı kalıyor]

def extract_price(item):
    selectors = [
        ".a-price .a-offscreen",
        ".a-price-whole",
        "span.a-color-base",
        "div.a-section.a-spacing-small.puis-padding-left-small.puis-padding-right-small span.a-color-base"
    ]
    for selector in selectors:
        try:
            elements = item.find_elements(By.CSS_SELECTOR, selector)
            for el in elements:
                text = el.get_attribute("innerText").replace("\xa0", "").replace("\u202f", "").strip()
                if "TL" in text and any(char.isdigit() for char in text):
                    return text
        except:
            continue
    return "Fiyat alınamadı"

def load_sent_data():
    data = {}
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            for line in f:
                parts = line.strip().split("|", 1)
                if len(parts) == 2:
                    title, price = parts
                    data[normalize(title)] = price.strip()
    return data

def save_sent_data(products_to_send):
    existing = load_sent_data()
    for product in products_to_send:
        title = product['title']  # zaten normalize edilmiş geliyor
        price = product['price'].strip()
        existing[title] = price
    with open(SENT_FILE, "w", encoding="utf-8") as f:
        for title, price in existing.items():
            f.write(f"{title} | {price}\n")

def run():
    if not decode_cookie_from_env():
        return

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
    for item in items:
        try:
            title_raw = item.find_element(By.CSS_SELECTOR, "img.s-image").get_attribute("alt")
            title = normalize(title_raw)
            price = extract_price(item)
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

    sent_data = load_sent_data()
    products_to_send = []

    for product in products:
        title = product["title"]
        price = product["price"].strip()

        if title in sent_data:
            old_price = sent_data[title]
            if price != old_price:
                print(f"📉 Fiyat düştü: {title} → {old_price} → {price}")
                products_to_send.append(product)
        else:
            print(f"🆕 Yeni ürün: {title}")
            products_to_send.append(product)

    if products_to_send:
        for p in products_to_send:
            send_message(p)
        save_sent_data(products_to_send)
        print(f"📁 Dosya güncellendi: {len(products_to_send)} ürün eklendi/güncellendi.")
    else:
        print("⚠️ Yeni veya indirimli ürün bulunamadı.")

if __name__ == "__main__":
    run()
