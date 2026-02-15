import json
import csv
import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from datetime import datetime
import math


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


def make_request(url, timeout=10):
    """Make HTTP GET request with error handling."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return response
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


def get_total_books_and_pages(start_url):
    """
    Calculate total number of books and required pages from woof_checkbox_count elements.
    Returns tuple: (total_books, total_pages)
    """
    response = make_request(start_url)
    if not response:
        return 0, 0
    
    parser = BeautifulSoup(response.text, 'lxml')
    
    # Find all elements with class 'woof_checkbox_count'
    count_elements = parser.select('.woof_checkbox_count')
    
    total_books = 0
    for elem in count_elements:
        # Extract text like "(1234)" and get the number
        text = elem.text.strip()
        if text.startswith('(') and text.endswith(')'):
            try:
                count = int(text[1:-1])  # Remove parentheses and convert to int
                # Dividing by 2 to account for duplicate counts in the DOM
                total_books += count / 2
            except ValueError:
                continue
    
    # Calculate number of pages needed (assuming 20 books per page)
    books_per_page = 20.0
    total_pages = math.ceil(total_books / books_per_page)
    total_books = int(total_books)
    
    return total_books, total_pages


def extract_urls(start_url):
    """Extract product URLs from a listing page."""
    response = make_request(start_url)
    if not response:
        return
    
    parser = BeautifulSoup(response.text, 'lxml')
    product_links = parser.select('li.product > div > a')
    
    for link in product_links:
        relative_url = link.attrs.get('href')
        if relative_url:
            yield relative_url


def extract_product(url):
    """Extract product information from a product page."""
    response = make_request(url)
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
    author_info = parser.select_one('.brxe-text-basic > a')
    author_info = author_info.text.replace(',', '$') if author_info else ''
    
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
    
    repub_year_elem = parser.find('div', {'id': 'brxe-htsaka'})
    repub_year = repub_year_elem.text.replace('Έτος Επανέκδοσης:', '').replace(',', '$') if repub_year_elem else ''
    
    ISBN_elem = parser.find('div', {'id': 'brxe-unzojw'})
    ISBN = ISBN_elem.text.replace('ISBN:', '').replace(',', '$') if ISBN_elem else ''
    
    pub_info_elem = parser.find('div', {'id': 'brxe-ysyhzh'})
    pub_info = pub_info_elem.text.replace('Εκδότης:', '').replace(',', '$') if pub_info_elem else ''
    
    repub_info_elem = parser.find('div', {'id': 'brxe-udljnu'})
    repub_info = repub_info_elem.text.replace('Έκδοση:', '').replace(',', '$') if repub_info_elem else ''
    
    # Construct issue info
    issue_info = f"{month} {year}".strip()
    if not year:
        if repub_year:
            if repub_info:
                issue_info = f"{repub_year}({repub_info} έκδοση)"
            else:
                issue_info = repub_year
    
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


def main():
    """Main scraping function."""
    extracted_data = []
    thislist = ["biblia-poy-diathetei-h-se", "vivlia-allon-ekdoton", "politiki-kai-koinonia",
                "ellhnikh-logotexnia", "paidiki-logotechnia", "marx-engkels-lenin",
                "komix-geloiografies", "xeni-logotechnia", "vivlia-gnoseon-vivlia"]
    
    totalbooksnum = 0
    
    # Generate filename with current date
    current_date = datetime.now().strftime('%Y%m%d')
    output_filename = f'data/{current_date}_sep_data.csv'
    latest_filename = 'data/latest.csv'
    
    for thisitem in thislist:
        start_url = f"https://sep.gr/product-category/vivlia/{thisitem}/?orderby=date"
        
        # Automatically calculate total books and pages needed
        print(f"\n{thisitem}: Calculating total books and pages...")
        total_books, total_pages = get_total_books_and_pages(start_url)
        
        if total_books == 0:
            print("✗ Could not determine total books count. Using default range.")
            total_pages = 1  # Fallback to original value
            print(f"default range: {total_pages} total pages")
        else:
            print(f"✓ Found {total_books} total books")
            print(f"✓ Will scrape {total_pages} pages")
        
        booksnum = 0
        
        # Scrape pages
        for page in tqdm(range(1, total_pages + 1), desc=f"Processing {thisitem}"):
            page_url = f"{start_url}&product-page={page}"
            
            product_urls = extract_urls(page_url)
            
            for url in product_urls:
                product_data = extract_product(url)
                
                if product_data:
                    extracted_data.append(product_data)
                    booksnum += 1
                    totalbooksnum += 1
    
    # Export data
    if extracted_data:
        # Deduplicate by (title, ISBN) - keep first occurrence
        seen = set()
        unique_data = []
        for item in extracted_data:
            key = (item.get('title', '').strip(), item.get('ISBN', '').strip())
            if key not in seen:
                seen.add(key)
                unique_data.append(item)
        extracted_data = unique_data

        # Create data directory if it doesn't exist
        import os
        import glob
        os.makedirs('data', exist_ok=True)
        
        dict_to_csv(extracted_data, output_filename)
        dict_to_csv(extracted_data, latest_filename)
        
        # Generate manifest of all CSV files
        csv_files = glob.glob('data/*.csv')
        csv_files_data = []
        most_recent_date = None #Track the most recent date
        
        for csv_file in sorted(csv_files, reverse=True):
            filename = os.path.basename(csv_file)
            if filename == 'latest.csv':
                continue
            
            # Extract date from filename (format: YYYYMMDD_sep_data.csv)
            if filename.endswith('_sep_data.csv'):
                date_str = filename.split('_')[0]
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    # Greek month names in genitive case (for dates)
                    greek_months = [
                        "Γενάρη", "Φλεβάρη", "Μάρτη", "Απρίλη", "Μάη", "Ιούνη",
                        "Ιούλη", "Αύγουστο", "Σεπτέμβρη", "Οχτώβρη", "Νοέμβρη", "Δεκέμβρη"
                    ]
                    
                    # Format: "day month_name year" to match JavaScript toLocaleDateString('el-GR')
                    day = date_obj.day
                    month_name = greek_months[date_obj.month - 1]
                    year = date_obj.year
                    formatted_date = f"{day} {month_name} {year}"
                    if most_recent_date is None:
                        most_recent_date = formatted_date
                    csv_files_data.append({
                        'filename': filename,
                        'date': formatted_date,
                        'display': f"{formatted_date} - {filename}"
                    })
                except ValueError:
                    pass
        
        # Add latest.csv at the beginning
        csv_files_data.insert(0, {
            'filename': 'latest.csv',
            'date': 'Latest',
            'display': f"Πιο πρόσφατο ({most_recent_date})"
        })
        
        # Save manifest as JSON
        with open('data/manifest.json', 'w', encoding='utf-8') as f:
            json.dump(csv_files_data, f, ensure_ascii=False, indent=2)
            
        dup_count = totalbooksnum - len(extracted_data)
        if dup_count > 0:
            print(f"\n✓ Successfully scraped {totalbooksnum} books ({dup_count} duplicates removed → {len(extracted_data)} unique)")
        else:
            print(f"\n✓ Successfully scraped {len(extracted_data)} books")
        print(f"✓ Data saved to: {output_filename}")
        print(f"✓ Latest data saved to: {latest_filename}")
        print(f"✓ Manifest updated with {len(csv_files_data)} files")
    else:
        print("\n✗ No data was extracted")


if __name__ == '__main__':
    main()
