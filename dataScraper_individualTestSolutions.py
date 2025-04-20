import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging
import time
import re
import concurrent.futures

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BASE_URL = "https://www.shl.com"

def extract_duration(text):
    """Extract duration from text description"""
    duration_match = re.search(r'(\d+)\s*(?:minutes|mins|min)', text, re.IGNORECASE)
    if duration_match:
        return f"{duration_match.group(1)} minutes"
    else:
        return "Unknown"

def get_product_details(url):
    """Get additional details from product page"""
    try:
        full_url = url if url.startswith('http') else f"{BASE_URL}{url}"
        logger.info(f"Fetching details from {full_url}")
        
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(full_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')

        # Description
        desc_div = soup.find('h4', string='Description')
        description = desc_div.find_next_sibling('p').text.strip() if desc_div else "No description available"

        # Duration (from approximate completion time)
        duration_text = soup.find('h4', string='Assessment length')
        duration = "Varies"
        if duration_text:
            p_tag = duration_text.find_next_sibling('p')
            if p_tag:
                match = re.search(r'(\d+)', p_tag.text)
                if match:
                    duration = f"{match.group(1)}"

        # Test Type (e.g., C, P, A, B)
        type_elems = soup.select('span.product-catalogue__key')
        test_type_mapping = {
            'A': 'Ability & Aptitude',
            'B': 'Biodata and Situational Judgement',
            'C': 'Competencies',
            'D' : 'Development & 360',
            'E' : 'Assessment Exercises', 
            'K' : 'Knowledge & Skills',
            'P': 'Personality & Behaviour',
            'S' : 'Simulations'
        }
        test_types = [test_type_mapping.get(elem.text.strip(), elem.text.strip()) for elem in type_elems]
        test_type = ', '.join(test_types) if test_types else "Unknown"
        
        # Remote Testing Support
        remote_td = soup.find_all('td', class_='custom__table-heading__general')
        remote_support = "No"
        if len(remote_td) >= 1:
            span = remote_td[0].find('span', class_='catalogue__circle -yes')
            if span:
                remote_support = "Yes"

        # Adaptive Support
        adaptive_support = "No"
        if len(remote_td) >= 2:
            span = remote_td[1].find('span', class_='catalogue__circle -yes')
            if span:
                adaptive_support = "Yes"

        return {
            "description": description,
            "duration": duration,
            "test_type": test_type,
            "remote_support": remote_support,
            "adaptive_support": adaptive_support
        }

    except Exception as e:
        logger.error(f"Error getting product details from {url}: {str(e)}")
        return {
            "description": "Error retrieving details",
            "duration": "Unknown",
            "test_type": "Unknown",
            "remote_support": "Unknown",
            "adaptive_support": "Unknown"
        }


def scrape_shl_catalog():
    """Scrape assessment information from SHL product catalog across multiple type pages"""
    BASE_CATALOG_URL = "https://www.shl.com/solutions/products/product-catalog/?start={}&type=1&type=1"
    assessments = []

    headers = {"User-Agent": "Mozilla/5.0"}
    for type_id in range(32):  # Loop for all pages
        count = 12*type_id
        url = BASE_CATALOG_URL.format(count)
        logger.info(f"Fetching data from {url}")
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            product_rows = soup.select('tr[data-entity-id]')
            if not product_rows:
                logger.warning(f"No product rows found for page={type_id+1}.")
                continue

            logger.info(f"Found {len(product_rows)} product rows for page={type_id+1}")

            for row in product_rows:
                try:
                    name_elem = row.select_one('td.custom__table-heading__title a')
                    if not name_elem:
                        continue

                    name = name_elem.text.strip()
                    product_url = name_elem['href']
                    
                    assessment = {
                        "name": name,
                        "url": f"{BASE_URL}{product_url}" if not product_url.startswith('http') else product_url
                    }
                    assessments.append(assessment)

                except Exception as e:
                    logger.error(f"Error processing row for page={type_id+1}: {str(e)}")
                    continue

        except Exception as e:
            logger.error(f"Error scraping SHL catalog for page={type_id+1}: {str(e)}")
            continue

    return assessments


def get_all_details(assessments, max_workers=5):
    """Get additional details for all assessments"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_index = {executor.submit(get_product_details, assessment['url']): i 
                          for i, assessment in enumerate(assessments)}
        
        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                details = future.result()
                assessments[index].update(details)
                logger.info(f"Details fetched for: {assessments[index]['name']}")
            except Exception as e:
                logger.error(f"Error getting details for assessment {index}: {str(e)}")
    
    return assessments

def main():
    assessments = scrape_shl_catalog()
    
    if assessments:
        logger.info(f"Scraped {len(assessments)} assessments. Fetching additional details...")
        detailed_assessments = get_all_details(assessments)
        
        df = pd.DataFrame(detailed_assessments)
        df.to_csv('assessments_final.csv', index=False)
        logger.info("Saved data to assessments.csv")
        
        print("\nSample:")
        print(df.head(3).to_string())
    else:
        logger.warning("No assessments found.")

if __name__ == "__main__":
    main()