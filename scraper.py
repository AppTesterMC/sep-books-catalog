import json
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
import math
import time
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import os
import glob


# Configuration
DELAY_BETWEEN_REQUESTS = (3.0, 6.0)  # Random delay between 3-6 seconds per request
DELAY_BETWEEN_PAGES = (5.0, 10.0)    # Random delay between 5-10 seconds per page
DELAY_BETWEEN_CATEGORIES = (10.0, 15.0)  # Random delay between 10-15 seconds per category
MAX_CONSECUTIVE_FAILURES = 5  # Stop category if 5 failures in a row
CHECKPOINT_FREQUENCY = 50  # Save progress every 50 books


def export_json(data, file_name):
    """Export data to JSON file."""
    with open(file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def export_csv(data, file_name):
    """Export single data record to CSV file."""
    book_info = ['title', 'author', 'publisher', 'ISBN', 'category', 
                 'price', 'date', 'pages']
    with open(file_name, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=book_info)
        w.writeheader()
        w.writerow(data)


def dict_to_csv(data, file_name):
    """Export list of dictionaries to CSV file."""
    df = pd.DataFrame.from_dict(data)
    df.to_csv(file_name, index=False, header=True, encoding='utf-8')


def load_checkpoint():
    """Load checkpoint data if it exists."""
    checkpoint_file = 'data/checkpoint.json'
    if os.path.exists(checkpoint_file):
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  Could not load checkpoint: {e}")
    return {'extracted_data': [], 'completed_categories': [], 'last_category': None, 'last_page': 0}


def save_checkpoint(checkpoint_data):
    """Save checkpoint data."""
    checkpoint_file = 'data/checkpoint.json'
    try:
        with open(checkpoint_file, 'w', encoding='utf-8') as f:
            json.dump(checkpoint_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save checkpoint: {e}")


def create_session():
    """Create a requests session with retry logic and proper headers."""
    session = requests.Session()
    
    # Add retry logic with exponential backoff
    retry_strategy = Retry(
        total=3,  # Reduced from 5 to fail faster
        backoff_factor=3,  # Increased from 2 for longer waits: 3, 9, 27 seconds
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    # Set headers to mimic a real browser
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'el-GR,el;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0'
    })
    
    return session


def make_request(url, session, timeout=20, max_retries=3):
    """Make HTTP GET request with error handling and retry logic."""
    for attempt in range(max_retries):
        try:
            # More aggressive random delay
            delay = random.uniform(*DELAY_BETWEEN_REQUESTS)
            time.sleep(delay)
            
            response = session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
            
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10  # Wait 10, 20, 30 seconds
                print(f"\n⚠️  Connection error. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Connection failed after {max_retries} attempts: {e}")
                return None
                
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 10
                print(f"\n⚠️  Timeout. Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
            else:
                print(f"\n❌ Timeout after {max_retries} attempts")
                return None
                
        except requests.RequestException as e:
            print(f"\n❌ Error: {e}")
            return None
    
    return None


def get_total_books_and_pages(start_url, session):
    """Calculate total number of books and required pages."""
    response = make_request(start_url, session)
    if not response:
        return 0, 0
    
    parser = BeautifulSoup(response.text, 'lxml')
    count_elements = parser.select('.woof_checkbox_count')
    
    total_books = 0
    for elem in count_elements:
        text = elem.text.strip()
        if text.startswith('(') and text.endswith(')'):
            try:
                count = int(text[1:-1])
                total_books += count / 2
            except ValueError:
                continue
    
    books_per_page = 20.0
    pages_safeguard = 4.0
    total_pages = math.ceil(total_books / books_per_page) + pages_safeguard
    total_books = int(total_books)
    
    return total_books, total_pages


def extract_urls(start_url, session):
    """Extract product URLs from a listing page."""
    response = make_request(start_url, session)
    if not response:
        return []
    
    parser = BeautifulSoup(response.text, 'lxml')
    product_links = parser.select('li.product > div > a')
    
    urls = []
    for link in product_links:
        relative_url = link.attrs.get('href')
        if relative_url:
            urls.append(relative_url)
    
    return urls

def extract_author(parser):
    """
    Extract author with multiple fallback methods.
    The website structure may vary, so we try several approaches.
    """
    # Method 1: Try the original selector
    author_elem = parser.select_one('.brxe-code > div > a')
    if author_elem and author_elem.text.strip():
        return author_elem.text.strip().replace(',', '$')
        
    # Method 3: Look for text containing "Συγγραφέας:" (Author:)
    all_text = parser.get_text()
    if 'Συγγραφέας:' in all_text:
        # Find the line with author
        lines = all_text.split('\n')
        for line in lines:
            if 'Συγγραφέας:' in line:
                # Extract author name after the colon
                author_part = line.split('Συγγραφέας:')[-1].strip()
                # Remove any extra text or links
                author_name = author_part.split('[')[0].strip()
                if author_name:
                    return author_name.replace(',', '$')
    
    # Method 2: Look for link with /contributor/ in href
    contributor_links = parser.find_all('a', href=lambda href: href and '/contributor/' in href)
    if contributor_links:
        for link in contributor_links:
            if link.text.strip():
                return link.text.strip().replace(',', '$')

    
    # Method 4: Try finding by class that might contain author
    potential_classes = [
        '.brxe-text-basic',
        '.product-author',
        '[class*="author"]',
        '[data-author]'
    ]
    
    for selector in potential_classes:
        try:
            elem = parser.select_one(selector)
            if elem:
                # Check if it contains a link
                link = elem.find('a')
                if link and link.text.strip():
                    return link.text.strip().replace(',', '$')
                # Otherwise use text directly
                if elem.text.strip():
                    return elem.text.strip().replace(',', '$')
        except:
            continue
    
    # If all methods fail, return empty string
    return ''

def extract_product(url, session):
    """Extract product information from a product page."""
    response = make_request(url, session)
    if not response:
        return None
    
    parser = BeautifulSoup(response.content, 'lxml', from_encoding='text/html; charset=utf-8')
    
    # Extract category
    category = parser.select_one('span.navigation > a:nth-child(5)')
    category_text = category.text if category else 'Βιβλία'
    
    # Extract title
    book_title_elem = parser.select_one('h3.brxe-product-title')
    book_title = book_title_elem.text.replace(',', '$') if book_title_elem else ''
    
    # Extract author
    #author_info = parser.select_one('.brxe-code > div > a')
    #author_info = author_info.text.replace(',', '$') if author_info else ''
    # Extract author using robust method
    author_info = extract_author(parser)
    
    # Extract price
    price_elem = parser.find('p', {'class': 'price'})
    if price_elem:
        price_text = price_elem.text.replace(' με ΦΠΑ', '').replace(
            'Original price was:', ',').replace('Η τρέχουσα τιμή είναι:', ',').split(',')
    else:
        price_text = ['', '', '']
    
    discount_price_text = price_text[2].replace('€.', '€') if len(price_text) > 2 else ''
    
    # Extract publication info
    year_elem = parser.find('div', {'data-script-id': 'hyxtvx'})
    year = year_elem.text.replace('Έτος Έκδοσης:', '').replace(',', '$') if year_elem else ''
    
    month_elem = parser.find('div', {'id': 'brxe-fuowkl'})
    month = month_elem.text.replace('Μήνας Έκδοσης:', '').replace(',', '$') if month_elem else ''
    
    repub_month_elem = parser.find('div', {'id': 'brxe-abckyu'})
    repub_month = repub_month_elem.text.replace('Μήνας Επανέκδοσης:', '').replace(',', '$') if month_elem else ''
    
    repub_year_elem = parser.find('div', {'id': 'brxe-htsaka'})
    repub_year = repub_year_elem.text.replace('Έτος Επανέκδοσης:', '').replace(',', '$') if repub_year_elem else ''
    
    ISBN_elem = parser.find('div', {'id': 'brxe-unzojw'})
    ISBN = ISBN_elem.text.replace('ISBN:', '').replace(',', '$') if ISBN_elem else ''
    
    pub_info_elem = parser.find('div', {'id': 'brxe-ysyhzh'})
    pub_info = pub_info_elem.text.replace('Εκδότης:', '').replace(',', '$') if pub_info_elem else ''
    
    repub_info_elem = parser.find('div', {'id': 'brxe-udljnu'})
    repub_info = repub_info_elem.text.replace('Έκδοση:', '').replace(',', '$') if repub_info_elem else ''
    
    # Construct issue info
    if year:
        issue_info = f"{month} {year}".strip()
    elif repub_year:
        if repub_info:
            issue_info = f"{repub_month} {repub_year}({repub_info} έκδοση)".strip()
        else:
            issue_info = f"{repub_month} {repub_year}".strip()
    else:
        issue_info = ''
        
    num_pages_elem = parser.find('div', {'data-script-id': 'ytsgdu'})
    num_pages = num_pages_elem.text.replace('Σελίδες:', '').replace(',', '$') if num_pages_elem else ''
    
    product_data = {
        'title': book_title,
        'author': author_info,
        'publisher': pub_info,
        'ISBN': ISBN,
        'category': category_text,
        'date': issue_info,
        'pages': num_pages,
        'price': price_text[0] if price_text else '',
        'discount_price': discount_price_text
    }
    
    return product_data


def scrape_category(category_name, start_url, session, checkpoint_data):
    """Scrape a single category with failure detection."""
    
    # Check if already completed
    if category_name in checkpoint_data['completed_categories']:
        print(f"✓ Category '{category_name}' already completed, skipping...")
        return True
    
    print(f"\n📚 {category_name}: Calculating total books and pages...")
    total_books, total_pages = get_total_books_and_pages(start_url, session)
    
    if total_books == 0:
        print(f"⚠️  Could not determine total books count for '{category_name}'. Skipping...")
        checkpoint_data['completed_categories'].append(category_name)
        return False
    
    print(f"✓ Found {total_books} total books")
    print(f"✓ Will scrape {total_pages} pages")
    
    # Determine starting page
    start_page = 1
    if checkpoint_data['last_category'] == category_name:
        start_page = checkpoint_data['last_page'] + 1
        if start_page > total_pages:
            print(f"✓ Category '{category_name}' already completed")
            checkpoint_data['completed_categories'].append(category_name)
            return True
        print(f"↻ Resuming from page {start_page}")
    
    consecutive_failures = 0
    books_in_category = 0
    
    # Scrape pages
    for page in tqdm(range(start_page, total_pages + 1), desc=f"Processing {category_name}", initial=start_page-1, total=total_pages):
        page_url = f"{start_url}&product-page={page}"
        
        product_urls = extract_urls(page_url, session)
        
        if not product_urls:
            consecutive_failures += 1
            print(f"\n⚠️  No products found on page {page} (failure {consecutive_failures}/{MAX_CONSECUTIVE_FAILURES})")
            
            if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                print(f"\n🛑 Too many consecutive failures. Stopping category '{category_name}'.")
                print(f"   Scraped {books_in_category} books from this category before stopping.")
                checkpoint_data['last_category'] = category_name
                checkpoint_data['last_page'] = page - 1
                save_checkpoint(checkpoint_data)
                return False
            
            # Wait longer before retry
            time.sleep(random.uniform(30.0, 60.0))
            continue
        
        # Reset failure counter on success
        consecutive_failures = 0
        
        for url in product_urls:
            product_data = extract_product(url, session)
            
            if product_data:
                checkpoint_data['extracted_data'].append(product_data)
                books_in_category += 1
                
                # Save checkpoint periodically
                if len(checkpoint_data['extracted_data']) % CHECKPOINT_FREQUENCY == 0:
                    checkpoint_data['last_category'] = category_name
                    checkpoint_data['last_page'] = page
                    save_checkpoint(checkpoint_data)
                    print(f"\n💾 Checkpoint saved ({len(checkpoint_data['extracted_data'])} books total)")
            else:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_FAILURES:
                    print(f"\n🛑 Too many failures. Stopping category '{category_name}'.")
                    checkpoint_data['last_category'] = category_name
                    checkpoint_data['last_page'] = page
                    save_checkpoint(checkpoint_data)
                    return False
        
        # Update checkpoint after each page
        checkpoint_data['last_category'] = category_name
        checkpoint_data['last_page'] = page
        
        # Longer delay between pages
        if page < total_pages:
            delay = random.uniform(*DELAY_BETWEEN_PAGES)
            time.sleep(delay)
    
    # Category completed successfully
    print(f"\n✓ Completed category '{category_name}' ({books_in_category} books)")
    checkpoint_data['completed_categories'].append(category_name)
    checkpoint_data['last_category'] = None
    checkpoint_data['last_page'] = 0
    save_checkpoint(checkpoint_data)
    
    return True


def main():
    """Main scraping function."""
    print("🔧 Initializing scraper with checkpoint support...")
    session = create_session()
    
    # Create data directory
    os.makedirs('data', exist_ok=True)
    
    # Load checkpoint
    checkpoint_data = load_checkpoint()
    if checkpoint_data['extracted_data']:
        print(f"↻ Resuming from checkpoint ({len(checkpoint_data['extracted_data'])} books already scraped)")
        print(f"   Completed categories: {', '.join(checkpoint_data['completed_categories']) if checkpoint_data['completed_categories'] else 'None'}")
    
    categories = [
        ("", "General Books"),
        ("omilos-ekpaideytikoy-provlimatismoy", "Educational Circle"),
        ("biblia-poy-diathetei-h-se", "SE Publications"),
        ("vivlia-allon-ekdoton", "Other Publishers"),
        ("politiki-kai-koinonia", "Politics & Society"),
        ("ellhnikh-logotexnia", "Greek Literature"),
        ("paidiki-logotechnia", "Children's Literature"),
        ("marx-engkels-lenin", "Marx-Engels-Lenin"),
        ("komix-geloiografies", "Comics"),
        ("xeni-logotechnia", "Foreign Literature"),
        ("vivlia-gnoseon-vivlia", "Knowledge Books")
    ]
    
    for category_slug, category_display in categories:
        start_url = f"https://sep.gr/product-category/vivlia/{category_slug}/?orderby=date"
        
        success = scrape_category(category_display, start_url, session, checkpoint_data)
        
        if not success:
            print(f"\n⚠️  Category '{category_display}' had issues. Progress saved.")
            print(f"   You can re-run the script to continue from where it stopped.")
        
        # Long delay between categories
        if category_display != categories[-1][1]:  # Not last category
            delay = random.uniform(*DELAY_BETWEEN_CATEGORIES)
            print(f"\n⏸️  Waiting {delay:.1f}s before next category...")
            time.sleep(delay)
    
    # Export final data
    extracted_data = checkpoint_data['extracted_data']
    
    if extracted_data:
        # Deduplicate
        seen = set()
        unique_data = []
        for item in extracted_data:
            key = (item.get('title', '').strip(), item.get('ISBN', '').strip())
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        
        dup_count = len(extracted_data) - len(unique_data)
        
        # Generate filename with current date
        current_date = datetime.now().strftime('%Y%m%d')
        output_filename = f'data/{current_date}_sep_data.csv'
        latest_filename = 'data/latest.csv'
        
        dict_to_csv(unique_data, output_filename)
        dict_to_csv(unique_data, latest_filename)
        
        # Generate manifest
        csv_files = glob.glob('data/*.csv')
        csv_files_data = []
        most_recent_date = None
        
        greek_months = [
            "Γενάρη", "Φλεβάρη", "Μάρτη", "Απρίλη", "Μάη", "Ιούνη",
            "Ιούλη", "Αύγουστο", "Σεπτέμβρη", "Οχτώβρη", "Νοέμβρη", "Δεκέμβρη"
        ]

        for csv_file in sorted(csv_files, reverse=True):
            filename = os.path.basename(csv_file)
            if filename == 'latest.csv':
                continue
            
            if filename.endswith('_sep_data.csv'):
                date_str = filename.split('_')[0]
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    day = date_obj.day
                    month_name = greek_months[date_obj.month - 1]
                    year = date_obj.year
                    formatted_date = date_obj.strftime('%d/%m/%Y')
                    display_date = f"{day} {month_name} {year}"
                    
                    if most_recent_date is None:
                        most_recent_date = formatted_date
                    
                    csv_files_data.append({
                        'filename': filename,
                        'date': formatted_date,
                        'display': display_date
                    })
                except ValueError:
                    pass
        
        # Add latest.csv
        if most_recent_date:
            current_date_obj = datetime.now()
            latest_date = f"{current_date_obj.day} {greek_months[current_date_obj.month - 1]} {current_date_obj.year}"
            csv_files_data.insert(0, {
                'filename': 'latest.csv',
                'date': most_recent_date,
                'display': latest_date
            })
        else:
            csv_files_data.insert(0, {
                'filename': 'latest.csv',
                'date': 'Latest',
                'display': 'Latest'
            })
        
        with open('data/manifest.json', 'w', encoding='utf-8') as f:
            json.dump(csv_files_data, f, ensure_ascii=False, indent=2)
        
        # Clean up checkpoint on success
        checkpoint_file = 'data/checkpoint.json'
        if os.path.exists(checkpoint_file):
            os.remove(checkpoint_file)
        
        # Print summary
        print("\n" + "="*70)
        print("📊 SCRAPING SUMMARY")
        print("="*70)
        print(f"✓ Successfully scraped {len(extracted_data)} books")
        if dup_count > 0:
            print(f"✓ Removed {dup_count} duplicates → {len(unique_data)} unique books")
        print(f"✓ Data saved to: {output_filename}")
        print(f"✓ Latest data saved to: {latest_filename}")
        print(f"✓ Manifest updated with {len(csv_files_data)} files")
        print("="*70)
    else:
        print("\n❌ No data was extracted")


if __name__ == '__main__':
    main()