import os
import re
import time
from playwright.sync_api import sync_playwright
from notifications import broadcast_push_notification

# Configuration
LISTING_URL = "https://www.sharesansar.com/category/share-listing"
CACHE_FILE = "last_listing_headline.txt"

def scrape_latest_listing():
    print("Checking for new secondary market listings on ShareSansar...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(LISTING_URL, timeout=60000)
            # Wait for news items to load
            page.wait_for_selector(".featured-news-list, .news-standard-list", timeout=15000)
            
            # Extract headlines
            # ShareSansar usually has headlines in h4 or a tags inside listing containers
            news_items = page.evaluate("""
                () => {
                    const items = Array.from(document.querySelectorAll('.news-standard-list h4 a, .featured-news-list h4 a'));
                    return items.map(el => el.innerText.trim()).filter(t => t.length > 5);
                }
            """)
            
            if not news_items:
                print("No news items found.")
                return None

            latest_headline = news_items[0]
            print(f"Latest Headline: {latest_headline}")
            
            # Check if it mentions "listed" or "listing"
            keywords = ["listed", "listing", "secondary market", "open for trading"]
            if any(k in latest_headline.lower() for k in keywords):
                return latest_headline
            else:
                print("Latest news doesn't seem to be a listing announcement.")
                return None
                
        except Exception as e:
            print(f"Error during scraping: {e}")
            return None
        finally:
            browser.close()

def main():
    latest = scrape_latest_listing()
    if not latest:
        return

    # Check against cache
    last_processed = ""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            last_processed = f.read().strip()

    if latest != last_processed:
        print("New Listing Detected! Sending notifications...")
        
        title = "🚀 New NEPSE Listing"
        body = latest
        
        # Broadcast to all users
        broadcast_push_notification(title, body)
        
        # Update cache
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            f.write(latest)
        
        print("Notification sent and cache updated.")
    else:
        print("No new listing since last check.")

if __name__ == "__main__":
    main()
