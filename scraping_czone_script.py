from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import cloudinary
import cloudinary.uploader
from datetime import datetime, timedelta
import json
import os

cloudinary.config(
    cloud_name="dgrmklvez",
    api_key="754748752136626",
    api_secret="x_9rxfpbDGqwvkqmD_NjadtuqP0",
    secure=True
)

chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("window-size=1920,1080")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.82 Safari/537.36"
)


json_filename = 'czon_scrap_data.json'

def check_last_crawl(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as json_file:
            data = json.load(json_file)
            last_crawl_date = data[0].get("Last Crawl Date", None)
            if last_crawl_date:
                last_crawl = datetime.strptime(last_crawl_date, "%Y-%m-%d %H:%M:%S")
                if datetime.now() - last_crawl < timedelta(days=1):
                    print("Last crawl was within 24 hours. Skipping new crawl.")
                    return True
    return False

if not check_last_crawl(json_filename):
    driver = webdriver.Chrome(options=chrome_options)

    urls = [
        "https://www.czone.com.pk/projectors-pakistan-ppt.252.aspx?br=6",
        "https://www.czone.com.pk/softwares-pakistan-ppt.103.aspx?br=26"
    ]

    last_crawl_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_products_data = [{"Last Crawl Date": last_crawl_date}]

    def fetch_element_text(driver, by, locator):
        try:
            return WebDriverWait(driver, 1).until(EC.visibility_of_element_located((by, locator))).text
        except Exception as e:
            print(e)
            return None

    def upload_image_to_cloudinary(image_url):
        try:
            response = cloudinary.uploader.upload(image_url)
            return response["url"]
        except Exception as e:
            print(e)
            return None

    def scrape_product_data(product_link):
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(product_link)

        product_data = {
            "ID": ("ID", "spnProductCode"),
            "Name": ("ID", "spnProductName"),
            "Price": ("ID", "spnCurrentPrice"),
            "Description": ("CSS_SELECTOR", "#divProductDesc"),
            "Features": None,
            "Product": ("ID", "spnParentProductType"),
            "Product Type": ("ID", "spnProductType"),
            "Stock Status": ("ID", "spnStockStatus"),
            "Warranty": ("ID", "spnWarranty"),
            "Price Updated On": ("ID", "spnUpdateDate"),
        }

        for key, locator in product_data.items():
            if locator is not None:
                by, loc = locator
                product_data[key] = fetch_element_text(driver, getattr(By, by), loc)

        try:
            highlights = WebDriverWait(driver, 1).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#ulHighlights li"))
            )
            highlight_texts = [highlight.text for highlight in highlights]
            product_data["Features"] = highlight_texts
        except Exception as e:
            print(e)
            product_data["Features"] = ["Not Available"]

        base_url = "https://www.czone.com.pk/"
        main_image = driver.find_element(By.ID, "imgProduct").get_attribute("data-zoom-image")
        main_image_url = base_url + main_image.lstrip("/")
        product_data["Main Image"] = upload_image_to_cloudinary(main_image_url)

        try:
            thumbnails = WebDriverWait(driver, 1).until(
                EC.visibility_of_all_elements_located((By.CSS_SELECTOR, "#divThumbs a[data-image]"))
            )
            if thumbnails:
                additional_images = [base_url + img.get_attribute("data-image").lstrip("/") for img in thumbnails]
                product_data["Images"] = [upload_image_to_cloudinary(img_url) for img_url in additional_images]
            else:
                product_data["Images"] = ["Not Available"]
        except Exception as e:
            print(e)
            product_data["Images"] = ["Not Available"]

        driver.quit()
        return product_data

    for url in urls:
        driver.get(url)
        detail_links = []
        try:
            products = driver.find_elements(By.CLASS_NAME, "item")
            for i, product in enumerate(products):
                index_str = f"{i:02}"
                try:
                    product_link = driver.find_element(By.ID, f"rptListView_ctl{index_str}_anProductImage").get_attribute("href")
                    detail_links.append(product_link)
                except Exception:
                    continue
        except Exception as e:
            print(e)

        for product_link in detail_links:
            product_data = scrape_product_data(product_link)
            all_products_data.append(product_data)
            print(f"Data Scraped: {product_data}")

    with open(json_filename, 'w') as json_file:
        json.dump(all_products_data, json_file, indent=4)

    driver.quit()
else:
    print("Crawl skipped: Data was recently refreshed within the last 24 hours.")
