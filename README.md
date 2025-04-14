import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import logging
import os
import pandas as pd
from datetime import datetime
import re
import sys

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticket_scraper.log'),
        logging.StreamHandler()
    ]
)

class TicketScraper:
    def __init__(self):
        """Initialize the scraper with basic options"""
        try:
            # Set up Chrome options with additional compatibility settings
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-notifications')
            options.add_argument('--disable-popup-blocking')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-gpu')  # Disable GPU hardware acceleration
            options.add_argument('--disable-software-rasterizer')  # Disable software rasterizer
            options.add_argument('--ignore-certificate-errors')  # Ignore certificate errors
            options.add_argument('--disable-extensions')  # Disable extensions
            
            # Add additional Windows-specific options
            if sys.platform == 'win32':
                options.add_argument('--disable-win32k-locks')
                options.add_argument('--disable-site-isolation-trials')
            
            try:
                # First try with undetected-chromedriver
                self.driver = uc.Chrome(options=options)
            except Exception as e:
                logging.error(f"Failed to initialize with undetected-chromedriver: {str(e)}")
                # If that fails, try with regular Chrome
                from selenium import webdriver
                from selenium.webdriver.chrome.service import Service
                from webdriver_manager.chrome import ChromeDriverManager
                
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=options)
            
            # Set up WebDriverWait with increased timeout
            self.wait = WebDriverWait(self.driver, 30)
            
            # Create directory for HTML files if it doesn't exist
            self.html_dir = "ticket_html_files"
            if not os.path.exists(self.html_dir):
                os.makedirs(self.html_dir)
            
            # Define categories and their subcategories
            self.categories = {
                "concerts": {
                    "popular": ["Rock", "Pop", "Hip-Hop/Rap", "Country", "R&B"],
                    "discover": ["Alternative", "Blues", "Classical", "Comedy", "Dance/Electronic", "Folk", "Jazz", "Latin", "Metal", "Reggae", "World"]
                },
                "sports": {
                    "popular": ["Baseball", "Basketball", "Football", "Hockey", "Soccer"],
                    "discover": ["Auto Racing", "Boxing", "Golf", "Lacrosse", "MMA", "Rugby", "Tennis", "Wrestling"]
                },
                "arts": {
                    "popular": ["Broadway", "Comedy", "Dance", "Musical Theatre", "Opera"],
                    "discover": ["Ballet", "Classical Music", "Contemporary Art", "Performance Art", "Theatre"]
                },
                "family": {
                    "popular": ["Children's Theatre", "Circus", "Family Shows", "Magic Shows", "Puppet Shows"],
                    "discover": ["Educational", "Interactive", "Musical", "Storytelling", "Workshops"]
                }
            }
            
            self.collected_tickets = []
            logging.info("Scraper initialized successfully")
            
        except Exception as e:
            logging.error(f"Failed to initialize scraper: {str(e)}")
            raise

    def scroll_to_bottom(self):
        """Scroll to the bottom of the page gradually"""
        try:
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            while True:
                # Scroll down gradually
                for i in range(10):
                    self.driver.execute_script(f"window.scrollTo(0, {(i + 1) * last_height / 10});")
                    time.sleep(0.5)
                
                # Wait for new content to load
                time.sleep(2)
                
                # Calculate new scroll height
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                
                # Break if no more content loaded
                if new_height == last_height:
                    break
                last_height = new_height
                
                # Try to click "More Events" if available
                try:
                    more_events = self.driver.find_element(By.XPATH, "//*[contains(text(), 'More Events')]")
                    actions = ActionChains(self.driver)
                    actions.move_to_element(more_events).click().perform()
                    time.sleep(3)
                except:
                    pass
                
        except Exception as e:
            logging.error(f"Error during scrolling: {str(e)}")

    def save_ticket_html(self, subcategory, ticket_number):
        """Save the current ticket page HTML to a file"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{subcategory}_ticket_{ticket_number}_{timestamp}.html"
            filepath = os.path.join(self.html_dir, filename)
            
            # Save the page source
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            logging.info(f"Saved HTML for ticket {ticket_number} in {subcategory}")
            return filepath
            
        except Exception as e:
            logging.error(f"Error saving HTML for ticket {ticket_number}: {str(e)}")
            return None

    def process_subcategory_tickets(self, subcategory):
        """Process all tickets in a subcategory"""
        try:
            logging.info(f"Processing tickets for subcategory: {subcategory}")
            
            # Initialize counters
            processed_tickets = 0
            total_tickets_found = 0
            retry_count = 0
            max_retries = 3
            
            while retry_count < max_retries:
                try:
                    # Find all ticket elements in current view
                    ticket_elements = self.driver.find_elements(
                        By.CSS_SELECTOR, 
                        "[data-test='event-card'], .event-card, [class*='EventCard']"
                    )
                    
                    current_view_count = len(ticket_elements)
                    if current_view_count > total_tickets_found:
                        total_tickets_found = current_view_count
                        logging.info(f"Found {total_tickets_found} total tickets")
                    
                    # Process tickets from the last processed index
                    for idx in range(processed_tickets, len(ticket_elements)):
                        ticket = ticket_elements[idx]
                        try:
                            # Scroll ticket into view
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", ticket)
                            time.sleep(2)
                            
                            # Find and click the "Find Tickets" button
                            find_tickets_selectors = [
                                ".//a[contains(text(), 'Find Tickets')]",
                                ".//button[contains(text(), 'Find Tickets')]",
                                ".//a[contains(@class, 'find-tickets')]",
                                ".//button[contains(@class, 'find-tickets')]",
                                ".//a[contains(@data-test, 'find-tickets')]",
                                ".//a[contains(@class, 'event-link')]"
                            ]
                            
                            find_tickets_button = None
                            for selector in find_tickets_selectors:
                                try:
                                    find_tickets_button = ticket.find_element(By.XPATH, selector)
                                    if find_tickets_button.is_displayed() and find_tickets_button.is_enabled():
                                        break
                                except:
                                    continue
                            
                            if find_tickets_button:
                                # Get the href before clicking
                                ticket_url = find_tickets_button.get_attribute('href')
                                if not ticket_url:
                                    continue
                                
                                # Open in new tab
                                self.driver.execute_script("window.open(arguments[0], '_blank');", ticket_url)
                                time.sleep(3)
                                
                                # Switch to new tab
                                self.driver.switch_to.window(self.driver.window_handles[-1])
                                
                                # Wait for ticket details page to load
                                try:
                                    self.wait.until(
                                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-test='event-detail'], .event-detail"))
                                    )
                                    
                                    # Extract detailed ticket information
                                    detailed_data = self.extract_detailed_ticket_data()
                                    
                                    # Save the detailed page data
                                    self.save_ticket_html(subcategory, processed_tickets + 1)
                                    
                                except Exception as e:
                                    logging.error(f"Error extracting detailed ticket data: {str(e)}")
                                
                                # Close the ticket details tab
                                self.driver.close()
                                
                                # Switch back to main window
                                self.driver.switch_to.window(self.driver.window_handles[0])
                                time.sleep(2)
                            
                            processed_tickets += 1
                            
                        except Exception as e:
                            logging.error(f"Error processing ticket {idx + 1}: {str(e)}")
                            continue
                    
                    # Scroll down to load more tickets
                    last_height = self.driver.execute_script("return document.body.scrollHeight")
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    
                    # Check if we've reached the end
                    new_height = self.driver.execute_script("return document.body.scrollHeight")
                    if new_height == last_height:
                        # Try to click "More Events" if available
                        try:
                            more_events = self.driver.find_element(By.XPATH, "//button[contains(text(), 'More Events')]")
                            if not self.safe_click(more_events):
                                break
                            time.sleep(3)
                        except:
                            break
                    
                    retry_count = 0  # Reset retry count on successful iteration
                    
                except Exception as e:
                    logging.error(f"Error in main processing loop: {str(e)}")
                    retry_count += 1
                    if retry_count < max_retries:
                        time.sleep(5)
                        continue
                    break
            
            logging.info(f"Processed {processed_tickets} tickets for {subcategory}")
            return True
            
        except Exception as e:
            logging.error(f"Error processing subcategory tickets: {str(e)}")
            return False

    def extract_detailed_ticket_data(self):
        """Extract detailed information from the ticket details page"""
        try:
            detailed_data = {}
            
            # Extract event details
            selectors = {
                'event_name': "[data-test='event-name'], .event-name, h1",
                'event_date': "[data-test='event-date'], .event-date, [class*='eventDate']",
                'venue_name': "[data-test='venue-name'], .venue-name, [class*='venueName']",
                'venue_address': "[data-test='venue-address'], .venue-address, [class*='venueAddress']",
                'price_range': "[data-test='price-range'], .price-range, [class*='priceRange']",
                'event_info': "[data-test='event-info'], .event-info, [class*='eventInfo']",
                'ticket_limit': "[data-test='ticket-limit'], .ticket-limit, [class*='ticketLimit']",
                'age_restriction': "[class*='ageRestriction'], [data-test='age-restriction']",
                'accessibility': "[data-test='accessibility'], [class*='accessibility']",
                'parking_info': "[data-test='parking-info'], [class*='parkingInfo']"
            }
            
            for key, selector in selectors.items():
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    detailed_data[key] = element.text.strip()
                except:
                    detailed_data[key] = None
            
            # Extract ticket types and prices if available
            try:
                ticket_types = self.driver.find_elements(
                    By.CSS_SELECTOR,
                    "[data-test='ticket-type'], .ticket-type, [class*='ticketType']"
                )
                
                ticket_info = []
                for ticket_type in ticket_types:
                    try:
                        type_name = ticket_type.find_element(By.CSS_SELECTOR, "[class*='name']").text.strip()
                        type_price = ticket_type.find_element(By.CSS_SELECTOR, "[class*='price']").text.strip()
                        ticket_info.append({
                            'type': type_name,
                            'price': type_price
                        })
                    except:
                        continue
                
                detailed_data['ticket_types'] = ticket_info
                
            except Exception as e:
                logging.warning(f"Could not extract ticket types: {str(e)}")
            
            return detailed_data
            
        except Exception as e:
            logging.error(f"Error extracting detailed ticket data: {str(e)}")
            return {}

    def navigate_to_concerts(self):
        """Navigate to the concerts section"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Navigate to Ticketmaster
                self.driver.get("https://www.ticketmaster.com")
                time.sleep(5)
                
                # Click on concerts - try multiple selector approaches
                selectors = [
                    "//a[contains(@href, '/concerts')]",
                    "//a[contains(text(), 'Concerts')]",
                    "//a[contains(@data-ga, 'concerts')]"
                ]
                
                for selector in selectors:
                    try:
                        concerts_link = self.wait.until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        concerts_link.click()
                        time.sleep(5)
                        logging.info("Navigated to concerts section")
                        return True
                    except:
                        continue
                
                logging.error(f"Failed to find concerts link on attempt {attempt + 1}")
                
            except Exception as e:
                logging.error(f"Error navigating to concerts on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(5)
                    continue
                return False
        
        return False

    def navigate_to_subcategory(self, subcategory):
        """Navigate to a specific subcategory"""
        try:
            # Find and click the subcategory link
            subcategory_link = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{subcategory}')]"))
            )
            subcategory_link.click()
            time.sleep(5)
            
            logging.info(f"Navigated to subcategory: {subcategory}")
            return True
            
        except Exception as e:
            logging.error(f"Error navigating to subcategory {subcategory}: {str(e)}")
            return False

    def process_concert_subcategories(self):
        """Process all concert subcategories"""
        concert_subcategories = [
            "Rock", "Hip-Hop/Rap", "Country", "Latin",
            "Pop", "R&B", "Alternative", "Blues",
            "Classical", "Comedy", "Dance/Electronic",
            "Folk", "Jazz", "Metal", "Reggae", "World"
        ]
        
        try:
            if not self.navigate_to_concerts():
                return
            
            for subcategory in concert_subcategories:
                try:
                    logging.info(f"\nProcessing {subcategory}")
                    
                    if self.navigate_to_subcategory(subcategory):
                        self.process_subcategory_tickets(subcategory)
                        
                    # Go back to concerts main page
                    self.driver.back()
                    time.sleep(5)
                    
                except Exception as e:
                    logging.error(f"Error processing {subcategory}: {str(e)}")
                    continue
                
        except Exception as e:
            logging.error(f"Error in process_concert_subcategories: {str(e)}")

    def save_results(self):
        """Save collected tickets to Excel file"""
        try:
            if not self.collected_tickets:
                logging.error("No results obtained")
                return
            
            df = pd.DataFrame(self.collected_tickets)
            filename = f"ticketmaster_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            logging.info(f"Results saved to {filename}")
            
        except Exception as e:
            logging.error(f"Error saving results: {str(e)}")

    def close(self):
        """Close the browser"""
        try:
            self.driver.quit()
            logging.info("Browser closed")
        except Exception as e:
            logging.error(f"Error closing browser: {str(e)}")

def main():
    """Main function to run the scraper"""
    max_retries = 3
    for attempt in range(max_retries):
        scraper = None
        try:
            scraper = TicketScraper()
            scraper.process_concert_subcategories()
            break
            
        except Exception as e:
            logging.error(f"Error in main (attempt {attempt + 1}): {str(e)}")
            if scraper:
                scraper.close()
            if attempt < max_retries - 1:
                time.sleep(10)
                continue
            
        finally:
            if scraper:
                scraper.save_results()
                scraper.close()

if __name__ == "__main__":
    main() 
