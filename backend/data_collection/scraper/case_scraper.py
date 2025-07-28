from data_collection import *

def scrape_legal_cases():
    driver, wait, download_dir = setup_driver("legal_cases")
    
    # Set to track processed cases and avoid duplicates
    processed_cases = set()
    
    # Initialize counters
    total_downloaded = 0
    current_page = 1
    
    try:
        print("Starting Malaysian Court Case Scraper")
        driver.get("https://ejudgment.kehakiman.gov.my/ejudgmentweb/searchpage.aspx?JurisdictionType=ALL")

        # Wait for date controls to load
        print("Waiting for page elements to load...")
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-id='divEJudgmentPortalSearchPageControl']")))

        # Click "Jenis Kes" dropdown and select "Sivil"
        print("Setting case type to 'Sivil'...")
        jenis_kes = driver.find_element(By.XPATH, "//span[@data-type='ddlCaseType']")
        jenis_kes.click()
        time.sleep(2)
        driver.find_element(By.XPATH, "//li[contains(text(), 'Sivil')]").click()

        """
        Test Case: Uncomment to set specific date range
        # Set 'Tarikh Keputusan' from and to
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)

        # Open and fill 'from' date picker
        from_picker = driver.find_element(By.XPATH, "//span[@data-type='dpFromDateOfResult']//input")
        from_picker.clear()
        from_picker.send_keys("01 Dis 2024")
    
        # Open and fill 'to' date picker
        to_picker = driver.find_element(By.XPATH, "//span[@data-type='dpDateOfResult']//input")
        to_picker.clear()
        to_picker.send_keys("31 Dis 2024")
        """

        time.sleep(3)

        # Click the search button
        search_button = driver.find_element(By.XPATH, "//input[@data-type='btnSearch']")
        search_button.click()
        
        # Wait for search results to load with better error handling
        print("Waiting for search results...")
        time.sleep(random.uniform(50, 60))  # Initial wait for search to process

        # Get the total number of pages
        total_pages_element = driver.find_element(By.XPATH, "//span[@data-type='TotalPage']")
        total_pages = int(total_pages_element.get_attribute("data-totalpage"))
        print(f"Found {total_pages} total pages to process")

        while current_page <= total_pages:
            print(f"Processing page {current_page} of {total_pages}")
            time.sleep(random.uniform(20, 30))  # Wait for the page to load
            rows = driver.find_elements(By.CSS_SELECTOR, "table[data-id='tblAPList'] > tbody > tr")
        
            if len(rows) == 1 and "NoRecordFound" in rows[0].get_attribute("innerHTML"):
                print("<X> No results found for the selected criteria.")
                break
        
            print(f"Page {current_page}: Found {len(rows)} row(s)")
        
            # Collect all download tasks for this page
            download_tasks = []
            
            for i, row in enumerate(rows):
                try:
                    columns = row.find_elements(By.TAG_NAME, "td")

                    # Skip if row doesn't have enough columns
                    if len(columns) < 2:
                        print(f"<!> Skipping row {i+1}: insufficient columns ({len(columns)})")
                        continue

                    raw_text = columns[1].text.strip()
                    
                    # Check for duplicates based on raw_text
                    if raw_text in processed_cases:
                        print(f"<!> Skipping duplicate case: {raw_text}")
                        continue
                    
                    # Add to processed cases set
                    processed_cases.add(raw_text)
                    
                    nombor_kes = re.sub(r"[\\/:*?\"<>|\n\r]+", "_", raw_text).replace(" ", "_")

                    # Find download button
                    view_btn = None
                    if columns[-1].find_elements(By.TAG_NAME, "table"):
                        # Extract information from the nested table
                        rows_nested = columns[-1].find_elements(By.CSS_SELECTOR, "table.innerTable.gridView > tbody > tr")
                        for row_nested in rows_nested:
                            columns_nested = row_nested.find_elements(By.TAG_NAME, "td")

                            # Make sure there are at least two columns before accessing index 1
                            if (len(columns_nested) >= 2):
                                try:
                                    view_btn = columns_nested[1].find_element(By.CSS_SELECTOR, "[data-action='viewdoc']")
                                    break  # Stop if found
                                except:
                                    continue    
                    else:
                        try:
                            view_btn = row.find_element(By.CSS_SELECTOR, "[data-action='viewdoc']")
                        except:
                            view_btn = None
                    
                    # Check if the download button exists
                    if not view_btn:
                        print(f"<Notice> Skipping row {i+1} (Nombor Kes: {nombor_kes}): No download link found.")
                        continue # Skip to the next row if no download button

                    # Get document ID for download
                    doc_id = view_btn.get_attribute("data-documentid")
                    download_tasks.append((doc_id, nombor_kes))

                except Exception as e:
                    print(f"<!> Error processing row {i+1}: {e}")
            
            # Execute downloads in parallel (4 concurrent downloads)
            if download_tasks:
                print(f"Starting parallel download of {len(download_tasks)} files...")
                successful_downloads = parallel_download(
                    download_tasks, 
                    download_dir,
                    download_url="https://efs.kehakiman.gov.my/EFSWeb/DocDownloader.aspx?DocumentID={doc_id}&Inline=true", 
                    max_workers=2
                )
                print(f"Downloaded {successful_downloads}/{len(download_tasks)} files from page {current_page}")
                total_downloaded += successful_downloads
                
            # Move to next page only if more pages remain
            if current_page < total_pages:
                try:
                    next_btn = driver.find_element(By.XPATH, "//span[@class='fa fa-forward']")
                    next_btn.click()
                    current_page += 1
                except Exception as e:
                    print(f"<!> Could not click Next: {e}")
                    break
            else:
                print("<end> Reached last page.")
                break

    except Exception as e:
        print(f"<X> Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("All file downloaded successfully")
        print(f"Total files: {total_downloaded}")
        print(f"Total unique cases processed: {len(processed_cases)}")
        driver.quit()

if __name__ == "__main__":
    scrape_legal_cases()