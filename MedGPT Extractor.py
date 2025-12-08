##############################################################################################################################
#---------------------------------------------------- MedGPT Extractor  -----------------------------------------------------#
#------------------ It scrolls, clicks see more, and extracts metadata of all MedGPTs until no more "see more"  -------------#
##############################################################################################################################

import json
import time
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from seleniumbase import Driver

keyword_file_path = "C:/Users/XXXXXX/Healthcare GPT Assessment/healthcare_gpt_search_keywords_2.txt"
output_file_path = "C:/Users/XXXXXX/Healthcare GPT Assessment/gpt_metadata_output.json"
gpt_store_url = "https://chatgpt.com/gpts"
login_url = "https://auth0.openai.com/u/login/password?state=hKFo2SBtbFFXQmhscnZVcWxtcnV6VFVWazhGanhUTHJFWi1NOaFur3VuaXZlcnNhbC1sb2dpbqN0aWTZIFZ5XzZROEVMYlZKbWdmbE1POU5PZzYyakVMaGZZenV0o2NpZNkgVGRKSWNiZTE2V29USHROOTVueXl3aDVFNHlPbzZJdEc"

def load_keywords(path):
    with open(path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def extract_metadata(driver):
    data = {}

    try:
        data['name'] = driver.find_element(By.CSS_SELECTOR, "div.text-center.text-2xl.font-semibold").text.strip()
    except:
        data['name'] = "N/A"

    try:
        author_divs = driver.find_elements(By.CSS_SELECTOR, "div.text-sm.text-token-text-tertiary")
        author = next((el.text.strip() for el in author_divs if el.text.strip().lower().startswith("by ")), "N/A")
        data['author'] = author.replace("By ", "")
    except:
        data['author'] = "N/A"

    try:
        sections = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-col.justify-center.items-center")
        for section in sections:
            try:
                label = section.find_element(By.CSS_SELECTOR, "div.text-xs.text-token-text-tertiary").text.strip().lower()
                value = section.find_element(By.CSS_SELECTOR, "div.text-xl.font-semibold").text.strip()
                if "ratings" in label:
                    match = re.search(r"\((.*?)\)", label)
                    reviews_value = match.group(1) if match else "N/A"
                    data['rating'] = value
                    data['reviews'] = reviews_value
                elif "category" in label:
                    data['category'] = value
                elif "conversations" in label:
                    data['conversations'] = value
            except:
                continue
    except:
        data.setdefault('rating', "N/A")
        data.setdefault('reviews', "N/A")
        data.setdefault('category', "N/A")
        data.setdefault('conversations', "N/A")

    try:
        starters = driver.find_elements(By.CSS_SELECTOR, "div.line-clamp-2.text-sm.break-all")
        data['conversation_starters'] = [s.text.strip() for s in starters if s.text.strip()]
    except:
        data['conversation_starters'] = []

    try:
        capabilities = driver.find_elements(By.CSS_SELECTOR, "div.flex.flex-row.items-start.gap-2.py-1.text-sm")
        data['capabilities'] = [c.text.strip() for c in capabilities if c.text.strip()]
    except:
        data['capabilities'] = []

    try:
        description_elem = driver.find_element(By.CSS_SELECTOR, "div.text-token-text-primary.text-sm.font-normal")
        data['description'] = description_elem.text.strip()
    except:
        data['description'] = "N/A"


    try:
        link_elem = driver.find_element(By.CSS_SELECTOR, "a.btn.relative.btn-primary.h-12.w-full")
        relative_url = link_elem.get_attribute("href")
        if relative_url:
            data['url'] = relative_url if relative_url.startswith("http") else f"https://chatgpt.com{relative_url}"
        else:
            data['url'] = driver.current_url
    except:
        data['url'] = driver.current_url

    return data

def click_see_more_until_done(driver):
    while True:
        try:
            see_more = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'See more')]"))
            )
            driver.execute_script("arguments[0].scrollIntoView(true);", see_more)
            time.sleep(4)
            see_more.click()
            time.sleep(5)
        except:
            break

def run_scraper():
    keywords = load_keywords(keyword_file_path)
    all_results = []
    seen_pairs = set()

    driver = Driver(uc=True, headless=False)

    try:
        driver.uc_open_with_reconnect(login_url, reconnect_time=30)
        print("\U0001f512 Please log in manually and solve any CAPTCHA. Press ENTER when GPT store is ready.")
        driver.uc_gui_click_captcha()
        input()

        for keyword in keywords:
            driver.get(gpt_store_url)
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[aria-label="Search GPTs"]'))
            )
            time.sleep(4)
            search_box = driver.find_element(By.CSS_SELECTOR, 'input[aria-label="Search GPTs"]')
            search_box.clear()
            time.sleep(4)
            search_box.send_keys(keyword)
            time.sleep(5)

            click_see_more_until_done(driver)
            idx = 0

            while True:
                cards = driver.find_elements(By.CSS_SELECTOR, "li[role='option']")
                if idx >= len(cards):
                    break

                try:
                    card = cards[idx]
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", card)
                    WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, f"(//li[@role='option'])[{idx + 1}]"))
                    )
                    driver.execute_script("arguments[0].click();", card)

                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "div.text-center.text-2xl.font-semibold"))
                    )
                    time.sleep(5)

                    gpt_data = extract_metadata(driver)
                    key_pair = (gpt_data.get("name", ""), gpt_data.get("description", ""))
                    if key_pair in seen_pairs:
                        print("  - Skipped duplicate by name & description")
                    else:
                        all_results.append(gpt_data)
                        seen_pairs.add(key_pair)

                    driver.back()
                    WebDriverWait(driver, 15).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li[role='option']"))
                    )
                    time.sleep(5)
                    click_see_more_until_done(driver)
                    idx += 1

                except Exception as gpt_err:
                    print(f"\u26a0\ufe0f Error handling GPT card #{idx}: {gpt_err}")
                    idx += 1

    finally:
        driver.quit()
        with open(output_file_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"\n\U0001f4be Saved {len(all_results)} GPTs to {output_file_path}")

if __name__ == "__main__":
    run_scraper()