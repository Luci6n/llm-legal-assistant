from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import os
import re
import requests

__all__ = [
    'setup_driver',
    'download_single_case',
    'parallel_download',
    'By',          
    'EC',           
    'time',         
    're'            
]

def setup_driver(dir):
    # --- Configuration ---
    # Get project root directory reliably
    current_file = os.path.abspath(__file__)  # Current file location
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))  # Go up 3 levels
    
    # Build path from project root
    DOWNLOAD_DIR = os.path.join(project_root, "data", "raw", dir)    
    
    chromedriver_path = os.path.join(project_root, "back-end", "data_collection", "chromedriver-win64", "chromedriver.exe")

    service = Service(chromedriver_path)
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("prefs", {
        "download.default_directory": DOWNLOAD_DIR,
        "plugins.always_open_pdf_externally": True,
    })
    
    driver = webdriver.Chrome(service=service, options=options)
    wait = WebDriverWait(driver, 20)
    
    return driver, wait, DOWNLOAD_DIR

def download_single_case(row_data, download_dir, download_url):
    """Download a single case file using requests (faster than Selenium)"""
    try:
        doc_id, nombor_kes = row_data
        
        download_url = download_url.format(doc_id=doc_id)
        
        # Use requests for faster download
        response = requests.get(download_url, timeout=30, stream=True)
        if response.status_code == 200:
            file_path = os.path.join(download_dir, f"{nombor_kes}.pdf")
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"📥 Downloaded: {nombor_kes}.pdf")
            return True
        else:
            print(f"⚠️ Failed to download: {nombor_kes} (Status: {response.status_code})")
            return False
            
    except Exception as e:
        print(f"⚠️ Error downloading {nombor_kes}: {e}")
        return False

def parallel_download(download_tasks, download_dir, download_url, max_workers=4):
    """Execute downloads in parallel"""
    successful_downloads = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all download tasks
        future_to_task = {
            executor.submit(download_single_case, task, download_dir, download_url): task 
            for task in download_tasks
        }
        
        # Wait for downloads to complete
        for future in as_completed(future_to_task):
            task = future_to_task[future]
            try:
                if future.result():
                    successful_downloads += 1
            except Exception as e:
                print(f"⚠️ Download task failed: {e}")
    
    return successful_downloads

    
    