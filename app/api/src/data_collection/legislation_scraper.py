from data_collection import *
from bs4 import BeautifulSoup

ORDINANCE_URL = "https://lom.agc.gov.my/ordinance.php"
SUBSIDIARY_LEGISLATION_URL = "https://lom.agc.gov.my/subsid.php?type=pua"
PRINCIPAL_UPDATED_ACT_URL = "https://lom.agc.gov.my/principal.php?type=updated"
PRINCIPAL_REVISED_ACT_URL = "https://lom.agc.gov.my/principal.php?type=revised"
AMENDMENT_ACT_URL = "https://lom.agc.gov.my/principal.php?type=amendment"

CATEGORY_URLS = {
    "act/principal/updated": PRINCIPAL_UPDATED_ACT_URL,
    "act/principal/revised": PRINCIPAL_REVISED_ACT_URL,
    "act/amendment": AMENDMENT_ACT_URL,
    "ordinance": ORDINANCE_URL,
    "subsidiary_legislation": SUBSIDIARY_LEGISLATION_URL,
}

def parse_row(category, row):
    cols = row.find_all("td")
    metadata, pdf_url = {}, None

    if category in ["act/principal/updated", "act/principal/revised"]:
        metadata = {
            "act_no": cols[0].get_text(strip=True),
            "title": cols[1].get_text(" ", strip=True),
            "date": cols[2].get_text(strip=True) if len(cols) > 2 else ""
        }
        link_tag = cols[-1].find("a", href=True)
        pdf_url = link_tag["href"] if link_tag else None

    elif category == "act/amendment":
        metadata = {
            "act_no": cols[0].get_text(strip=True),
            "title": cols[1].get_text(" ", strip=True),
            "royal_assent": cols[2].get_text(strip=True),
            "publication_date": cols[3].get_text(strip=True),
            "commencement_date": cols[4].get_text(strip=True)
        }
        link_tag = cols[-1].find("a", href=True)
        pdf_url = link_tag["href"] if link_tag else None

    elif category == "ordinance":
        metadata = {
            "ordinance_no": cols[0].get_text(strip=True),
            "title": cols[1].get_text(" ", strip=True),
            "commencement_date": cols[2].get_text(strip=True) if len(cols) > 2 else ""
        }
        link_tag = cols[-1].find("a", href=True)
        pdf_url = link_tag["href"] if link_tag else None

    elif category == "subsidiary_legislation":
        metadata = {
            "publication_date": cols[0].get_text(strip=True),
            "pu_no": cols[1].get_text(strip=True),
            "title": cols[2].get_text(" ", strip=True),
            "status": cols[3].get_text(strip=True),
            "related_legislation": cols[4].get_text(strip=True),
            "commencement_date": cols[5].get_text(strip=True)
        }
        link_tag = cols[-1].find("a", href=True)
        pdf_url = link_tag["href"] if link_tag else None

    if pdf_url and not pdf_url.startswith("http"):
        pdf_url = "https://lom.agc.gov.my/" + pdf_url.lstrip("/")

    return metadata, pdf_url

CATEGORY_URLS = {
    "act/principal/updated": PRINCIPAL_UPDATED_ACT_URL,
    "act/principal/revised": PRINCIPAL_REVISED_ACT_URL,
    "act/amendment": AMENDMENT_ACT_URL,
    "ordinance": ORDINANCE_URL,
    "subsidiary_legislation": SUBSIDIARY_LEGISLATION_URL,
}

def set_page_length_to_100(driver, wait, category):
    """
    Set the page length dropdown to 100 entries per page
    """
    try:
        # Different categories might have different dropdown selectors
        dropdown_selectors = [
            'select[name="data-ordinance_length"]',  # For ordinance
            'select[name="data-updated_length"]',    # For updated acts
            'select[name="data-revised_length"]',    # For revised acts
            'select[name="data-amendment_length"]',  # For amendment acts
            'select[name="datatable1_length"]',        # For subsidiary legislation
            'select.form-select.form-select-sm',     # Generic selector
        ]
        
        dropdown = None
        for selector in dropdown_selectors:
            try:
                dropdown = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                print(f"✅ Found dropdown with selector: {selector}")
                break
            except:
                continue
        
        if dropdown:
            # Click the dropdown to open it
            dropdown.click()
            time.sleep(1)
            
            # Select the option with value "100"
            option_100 = dropdown.find_element(By.CSS_SELECTOR, 'option[value="100"]')
            option_100.click()
            
            print(f"✅ Set page length to 100 for {category}")
            time.sleep(3)  # Wait for the page to reload
            return True
        else:
            print(f"⚠️ Could not find page length dropdown for {category}")
            return False
            
    except Exception as e:
        print(f"❌ Error setting page length for {category}: {e}")
        return False
    
def check_next_page_available(driver, category):
    """
    Check if next page is available by looking for enabled next button
    """
    try:
        # Different pagination selectors for different categories
        pagination_selectors = {
            "ordinance": '//*[@id="data-ordinance_paginate"]//span[contains(@class, "paginate_button next")]',
            "act/principal/updated": '//*[@id="data-updated_paginate"]//span[contains(@class, "paginate_button next")]',
            "act/principal/revised": '//*[@id="data-revised_paginate"]//span[contains(@class, "paginate_button next")]',
            "act/amendment": '//*[@id="data-amendment_paginate"]//span[contains(@class, "paginate_button next")]',
            "subsidiary_legislation": '//*[@id="datatable1_paginate"]//span[contains(@class, "paginate_button next")]',
        }
        
        # Try category-specific selector first, then fallback to generic
        selectors_to_try = []
        if category in pagination_selectors:
            selectors_to_try.append(pagination_selectors[category])
        
        # Add generic selectors
        selectors_to_try.extend([
            '//span[contains(@class, "paginate_button next") and not(contains(@class, "disabled"))]',
            '//a[contains(@class, "paginate_button next") and not(contains(@class, "disabled"))]'
        ])
        
        for selector in selectors_to_try:
            try:
                next_elements = driver.find_elements(By.XPATH, selector)
                for element in next_elements:
                    # Check if element is not disabled and is displayed
                    if ("disabled" not in element.get_attribute("class") and 
                        element.is_displayed() and element.is_enabled()):
                        print(f"✅ Found enabled next button with selector: {selector}")
                        return element
            except Exception as e:
                continue
        
        print("⚠️ No enabled next button found - reached last page")
        return None
        
    except Exception as e:
        print(f"❌ Error checking pagination: {e}")
        return None

def scrape_legislation():
    driver, wait, base_download_dir, _ = setup_driver("legislation")
    total_downloaded = 0  # Initialize the variable

    try:
        for category, url in CATEGORY_URLS.items():
            print(f"\n🔄 Starting {category} scrape...")

            # Create category-specific directories
            download_dir = os.path.join(base_download_dir, category)
            metadata_dir = os.path.join(download_dir, "metadata")        
            
            # Create directories if they don't exist
            os.makedirs(download_dir, exist_ok=True)
            os.makedirs(metadata_dir, exist_ok=True)
            
            driver.get(url)
            time.sleep(5)

            # Set page length to 100 before starting scrape
            set_page_length_to_100(driver, wait, category)
            
            page = 1
            category_downloaded = 0
            
            try:
                while True:
                    print(f"Processing page {page}...")
                    soup = BeautifulSoup(driver.page_source, "html.parser")
                    rows = soup.select("table tbody tr")

                    download_tasks = []
                    for row in rows:
                        metadata, pdf_url = parse_row(category, row)
                        if not pdf_url:
                            continue
                        
                        # Build safe filename based on category
                        if category == "ordinance":
                            identifier = metadata.get("ordinance_no", "unknown")
                        elif category == "subsidiary_legislation":
                            identifier = metadata.get("pu_no", "unknown")
                        else:  # act categories
                            identifier = metadata.get("act_no", "unknown")

                        # Clean filename
                        base_filename = re.sub(r"[\\/:*?\"<>|\n\r]+", "_", str(identifier)).replace(" ", "_")
                        download_tasks.append((pdf_url, base_filename, metadata))

                    if download_tasks:
                        successful_downloads = parallel_download(
                            download_tasks,
                            download_dir,
                            metadata_dir,
                            download_url="{doc_id}",  # here pdf_url is passed as doc_id
                            max_workers=4
                        )
                        category_downloaded += successful_downloads
                        total_downloaded += successful_downloads
                        print(f"Downloaded {successful_downloads}/{len(download_tasks)} files from page {page}")

                    # Check if next page is available
                    next_btn = check_next_page_available(driver, category)
                    if next_btn:
                        next_btn.click()
                        page += 1
                        time.sleep(random.uniform(6, 8))
                    else:
                        print("<end> Reached last page.")
                        break
                    
            except Exception as e:
                print(f"❌ Error processing {category}: {e}")
                
            print(f"✅ {category} scrape finished. Downloaded: {category_downloaded} files")

    finally:
        print(f"\n🎉 All legislation scrape finished. Total files downloaded: {total_downloaded}")
        driver.quit()

if __name__ == "__main__":
    scrape_legislation()