from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from tldextract import extract as tld_extract
import time
from bs4 import BeautifulSoup
import requests

def extract_website_info_with_selenium(url):
    # Setup Chrome options for headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")  # Recommended for running in a server environment
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    
    # Setup WebDriver (assuming ChromeDriver is installed and in PATH)
    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    driver.get(url)

    # Wait for JavaScript to render (adjust the waiting time as necessary)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    time.sleep(0.01)  # Waiting a bit longer for JS to finish

    # Now you can parse the rendered HTML
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # Extract title
    title = soup.title.text if soup.title else 'No title found'

    # Extract domain name
    domain_info = tld_extract(url)
    domain_name = f"{domain_info.domain}.{domain_info.suffix}"
    
    images = soup.find_all('img')
    main_image = None
    for image in images:
        if 'profile' in str(image).lower():
            main_image = image.get('src')
    
    if main_image is None:
        icon_links = soup.find_all('link', rel=lambda value: value and 'icon' in value.lower())
        for link in icon_links:
            href = link.get('href')
            if href:
                if href.startswith('http'):
                    main_image = href
                elif href.startswith('//'):
                    request_schema = 'https:' if url.startswith('https') else 'http:'
                    main_image = request_schema + href
                else:
                    main_image = requests.compat.urljoin(url, href)
            
    

    driver.quit()

    return {
        'title': title,
        'domain_name': domain_name,
        'main_image': main_image
    }

# Test the function
url = 'https://www.linkedin.com/in/tianxiang-ren-7b1637239/'
info = extract_website_info_with_selenium(url)
print(info)
