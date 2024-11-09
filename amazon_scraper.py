import requests
from bs4 import BeautifulSoup
import csv
import time
import random
from fake_useragent import UserAgent

class AmazonFullScraper:
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        
    def get_headers(self):
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Referer': 'https://www.amazon.in/'
        }

    def get_review_url(self, product_id, page):
        """Generate review URL that shows all reviews"""
        return f"https://www.amazon.in/product-reviews/{product_id}/ref=cm_cr_getr_d_paging_btm_next_{page}?ie=UTF8&reviewerType=all_reviews&pageNumber={page}&sortBy=recent"

    def extract_product_id(self, url):
        try:
            if '/dp/' in url:
                return url.split('/dp/')[1].split('/')[0]
            return None
        except:
            return None

    def get_reviews_from_page(self, soup):
        reviews_data = []
        try:
            # Find all review containers
            review_divs = soup.find_all('div', {'data-hook': 'review'})
            
            for review in review_divs:
                try:
                    # Extract username with multiple possible selectors
                    username_elem = review.find('span', {'class': 'a-profile-name'})
                    if not username_elem:
                        username_elem = review.find('div', {'class': 'a-profile-content'})
                    username = username_elem.text.strip() if username_elem else 'Anonymous'

                    # Extract date with multiple possible selectors
                    date_elem = review.find('span', {'data-hook': 'review-date'})
                    if not date_elem:
                        date_elem = review.find('span', {'class': 'review-date'})
                    date = date_elem.text.strip() if date_elem else 'No Date'
                    date = date.split('on ')[-1] if 'on ' in date else date

                    # Extract rating
                    rating_elem = review.find('i', {'data-hook': 'review-star-rating'})
                    if not rating_elem:
                        rating_elem = review.find('i', {'class': 'a-icon-star'})
                    rating = rating_elem.text.strip().split(' out')[0] if rating_elem else 'No Rating'

                    # Extract review text with multiple possible selectors
                    review_text_elem = review.find('span', {'data-hook': 'review-body'})
                    if not review_text_elem:
                        review_text_elem = review.find('div', {'class': 'a-row review-data'})
                    review_text = review_text_elem.text.strip() if review_text_elem else 'No Comment'

                    reviews_data.append({
                        'Username': username,
                        'Review_Date': date,
                        'Rating': rating,
                        'Comment': review_text
                    })
                except Exception as e:
                    print(f"Error processing individual review: {e}")
                    continue

        except Exception as e:
            print(f"Error parsing page: {e}")
            
        return reviews_data

    def smart_sleep(self):
        """Randomized delay between requests"""
        base_delay = random.uniform(2, 4)
        if random.random() < 0.1:  # 10% chance of longer delay
            base_delay += random.uniform(2, 4)
        time.sleep(base_delay)

    def scrape_reviews(self, url, max_reviews=500):
        product_id = self.extract_product_id(url)
        if not product_id:
            print("Could not extract product ID from URL")
            return None
            
        all_reviews = []
        page = 1
        empty_pages = 0
        max_empty_pages = 3

        print("Starting to scrape reviews...")
        
        while len(all_reviews) < max_reviews and empty_pages < max_empty_pages:
            try:
                print(f"\nScraping page {page}...")
                review_url = self.get_review_url(product_id, page)
                
                # Make request with new headers each time
                response = self.session.get(review_url, headers=self.get_headers())
                
                if response.status_code != 200:
                    print(f"Error: Status code {response.status_code}")
                    self.smart_sleep()
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Check for CAPTCHA
                if 'Enter the characters you see below' in str(soup):
                    print("CAPTCHA detected! Waiting longer...")
                    time.sleep(random.uniform(20, 30))
                    continue

                page_reviews = self.get_reviews_from_page(soup)
                
                if not page_reviews:
                    empty_pages += 1
                    print(f"No reviews found on page {page}")
                else:
                    empty_pages = 0
                    all_reviews.extend(page_reviews)
                    print(f"Total reviews collected: {len(all_reviews)}")

                if len(page_reviews) < 10:  # Typical page has 10 reviews
                    empty_pages += 1
                
                self.smart_sleep()
                page += 1

            except Exception as e:
                print(f"Error on page {page}: {e}")
                self.smart_sleep()
                continue
            
        print(f"\nFinished scraping. Total reviews collected: {len(all_reviews)}")
        return all_reviews[:max_reviews]

    def save_to_csv(self, reviews_data, filename="Samsung_Reviews.csv"):
        if not reviews_data:
            print("No data to save")
            return
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as file:
                fieldnames = ['Username', 'Review_Date', 'Rating', 'Comment']
                writer = csv.DictWriter(file, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(reviews_data)
                
            print(f"Successfully saved {len(reviews_data)} reviews to {filename}")
            
        except IOError as e:
            print(f"Error saving to CSV: {e}")

def main():
    # Your Amazon India URL
    url = "https://www.amazon.in/Samsung-Original-Type-C-Adaptor-without/dp/B0D2R2MXXJ"
    
    scraper = AmazonFullScraper()
    reviews = scraper.scrape_reviews(url, max_reviews=500)
    
    if reviews:
        scraper.save_to_csv(reviews)

if __name__ == "__main__":
    main()