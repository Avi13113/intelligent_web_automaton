from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import logging
import os
import time
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define the category structure
CATEGORY_STRUCTURE = {
    "Concerts": {
        "popular": ["Rock", "Hip-Hop/Rap", "Country", "Latin", "Alternative"],
        "discover": [
            "Alternative", "Ballads/Romantic", "Blues", "Children's Music",
            "Classical", "Country", "Dance/Electronic", "Folk", "Hip-Hop/Rap",
            "Holiday", "Jazz", "Latin", "Medieval/Renaissance", "Metal",
            "New Age", "Other", "Pop", "R&B", "Reggae", "Religious",
            "Rock", "World"
        ]
    },
    "Sports": {
        "popular": ["MLB", "NFL", "NBA", "NHL", "MLS"],
        "discover": [
            "Baseball", "Basketball", "Boxing", "Equestrian", "eSports",
            "Football", "Golf", "Gymnastics", "Hockey", "Ice Skating",
            "Indoor Soccer", "Lacrosse", "Martial Arts", "Motorsports/Racing",
            "Rodeo", "Rugby", "Soccer", "Softball", "Swimming", "Tennis",
            "Track & Field", "Volleyball", "Wrestling"
        ]
    },
    "Arts, Theater & Comedy": {
        "popular": ["Comedy", "Broadway", "Spectacular"],
        "discover": [
            "Broadway", "Children's Theater", "Circus & Specialty Acts",
            "Classical", "Comedy", "Cultural", "Dance", "Espectaculo",
            "Fashion", "Fine Art", "Magic & Illusion", "Miscellaneous",
            "Multimedia", "Music", "Opera", "Performance Art", "Puppetry",
            "Spectacular", "Theater", "Variety"
        ]
    },
    "Family": {
        "popular": ["Ice Shows", "Circus/Specialty Acts", "Children's Theater"],
        "discover": [
            "Children's Music", "Children's Theater", "Circus/Specialty Acts",
            "Fairs/Festivals", "Film/Family", "Ice Shows", "Latin Children's",
            "Magic/Illusion", "Miscellaneous/Family", "Puppetry", "Rodeo"
        ]
    }
}

def setup_driver():
    """Set up Chrome driver with proper options"""
    try:
        options = webdriver.ChromeOptions()
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        # SSL Error fixes
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--ignore-ssl-errors')
        options.add_argument('--allow-insecure-localhost')
        
        # WebGL and GPU related fixes
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-software-rasterizer')
        options.add_argument('--disable-webgl')
        options.add_argument('--disable-webgl2')
        
        # Additional stability options
        options.add_argument('--disable-notifications')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--start-maximized')
        options.add_argument('--disable-blink-features=AutomationControlled')
        
        # Automation detection prevention
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Add realistic user agent
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Additional preferences
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values.notifications': 2,
            'profile.default_content_settings.popups': 0,
            'download.prompt_for_download': False,
            'download.directory_upgrade': True,
            'safebrowsing.enabled': True
        })
        
        # Create and configure driver
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(30)  # Set page load timeout
        driver.implicitly_wait(10)
        
        # Set window size explicitly
        driver.set_window_size(1920, 1080)
        
        return driver
    except Exception as e:
        logging.error(f"Failed to setup driver: {str(e)}")
        raise

def wait_for_page_load(driver, timeout=10):
    """Wait for page to load completely"""
    try:
        old_page = driver.find_element(By.TAG_NAME, 'html')
        yield
        WebDriverWait(driver, timeout).until(EC.staleness_of(old_page))
    except Exception as e:
        logging.warning(f"Page load wait timed out: {str(e)}")

def safe_click(driver, element):
    """Safely click an element using multiple methods"""
    try:
        # Try regular click
        try:
            element.click()
            return True
        except:
            pass
        
        # Try JavaScript click
        try:
            driver.execute_script("arguments[0].click();", element)
            return True
        except:
            pass
        
        # Try ActionChains
        try:
            ActionChains(driver).move_to_element(element).click().perform()
            return True
        except:
            pass
        
        return False
    except Exception as e:
        logging.warning(f"All click attempts failed: {str(e)}")
        return False

def click_popular_section(driver, section_name):
    """Click on a popular section"""
    try:
        # Try different approaches to find and click the section
        selectors = [
            f"//div[contains(@class, 'popular')]//div[text()='{section_name}']",
            f"//div[contains(@class, 'popular')]//a[text()='{section_name}']",
            f"//div[contains(@class, 'popular')]//div[contains(text(), '{section_name}')]",
            f"//div[text()='{section_name}']",
            f"//a[contains(text(), '{section_name}')]"
        ]
        
        for selector in selectors:
            try:
                with wait_for_page_load(driver):
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if safe_click(driver, element):
                        time.sleep(3)  # Wait for content to load
                        return True
            except:
                continue
                
        return False
    except Exception as e:
        logging.warning(f"Failed to click popular section {section_name}: {str(e)}")
        return False

def click_discover_section(driver, section_name):
    """Click on a discover section"""
    try:
        # Try different approaches to find and click the section
        selectors = [
            f"//div[contains(@class, 'discover')]//a[text()='{section_name}']",
            f"//div[contains(@class, 'discover')]//div[text()='{section_name}']",
            f"//a[text()='{section_name}']",
            f"//div[contains(text(), '{section_name}')]",
            f"//a[contains(@href, '{section_name.lower()}')]"
        ]
        
        for selector in selectors:
            try:
                with wait_for_page_load(driver):
                    element = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if safe_click(driver, element):
                        time.sleep(3)  # Wait for content to load
                        return True
            except:
                continue
                
        return False
    except Exception as e:
        logging.warning(f"Failed to click discover section {section_name}: {str(e)}")
        return False

def scroll_through_all_events(driver):
    """Scroll through all events on the page until no more new events load"""
    try:
        last_height = driver.execute_script("return document.body.scrollHeight")
        events_found = set()
        max_attempts = 15  # Increased max attempts
        attempts = 0

        while attempts < max_attempts:
            # Scroll down smoothly
            driver.execute_script("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});")
            time.sleep(3)  # Increased wait time

            # Get all current events
            events = driver.find_elements(By.CSS_SELECTOR, "[data-bdd='event-card'], .event-item")
            current_events = set(event.get_attribute('outerHTML') for event in events)

            if len(current_events - events_found) == 0:
                attempts += 1
            else:
                attempts = 0
                events_found.update(current_events)

            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                attempts += 1
            last_height = new_height

            logging.info(f"Found {len(events_found)} unique events so far...")

        return list(driver.find_elements(By.CSS_SELECTOR, "[data-bdd='event-card'], .event-item"))
    except Exception as e:
        logging.error(f"Error during scrolling: {str(e)}")
        return []

def click_more_events(driver):
    """Click the More Events button and wait for new events to load"""
    try:
        # Try different selectors for More Events button
        selectors = [
            "//button[contains(text(), 'More Events')]",
            "//div[contains(text(), 'More Events')]",
            "//button[contains(@class, 'more-events')]",
            "//div[contains(@class, 'more-events')]"
        ]
        
        for selector in selectors:
            try:
                more_events = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, selector))
                )
                if safe_click(driver, more_events):
                    time.sleep(3)  # Wait for new events to load
                    return True
            except:
                continue
        
        return False
    except Exception as e:
        logging.warning(f"Failed to click More Events: {str(e)}")
        return False

def get_total_event_count(driver):
    """Get the total number of events shown in the counter"""
    try:
        # Try different selectors for event counter
        selectors = [
            "//div[contains(text(), 'Loaded')]",
            "//div[contains(text(), 'out of')]",
            "//div[contains(@class, 'event-count')]"
        ]
        
        for selector in selectors:
            try:
                counter = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                text = counter.text
                # Extract numbers from text like "Loaded 40 out of 3762 events"
                import re
                numbers = re.findall(r'\d+', text)
                if len(numbers) >= 2:
                    return int(numbers[-1])  # Get the last number (total)
            except:
                continue
        
        return None
    except Exception as e:
        logging.warning(f"Failed to get total event count: {str(e)}")
        return None

def explore_event_details(driver, event_url):
    """Get detailed information from an event page"""
    try:
        main_window = driver.current_window_handle
        driver.execute_script(f"window.open('{event_url}', '_blank');")
        time.sleep(2)
        
        new_window = [window for window in driver.window_handles if window != main_window][0]
        driver.switch_to.window(new_window)
        
        details = {}
        
        # Wait for page to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "h1"))
        )
        
        # Get event name
        try:
            details['event_name'] = driver.find_element(By.CSS_SELECTOR, "h1").text
        except:
            details['event_name'] = "Not found"
            
        # Get date and time
        try:
            details['datetime'] = driver.find_element(By.CSS_SELECTOR, "[datetime]").get_attribute("datetime")
        except:
            details['datetime'] = "Not found"
            
        # Get venue
        try:
            details['venue'] = driver.find_element(By.CSS_SELECTOR, "[data-bdd='event-venue']").text
        except:
            details['venue'] = "Not found"
            
        # Get price range
        try:
            details['price_range'] = driver.find_element(By.CSS_SELECTOR, "[data-bdd='event-price-range']").text
        except:
            details['price_range'] = "Not found"
            
        # Try to click Find Tickets if available
        try:
            find_tickets_selectors = [
                "//a[contains(text(), 'Find Tickets')]",
                "//button[contains(text(), 'Find Tickets')]",
                "//a[contains(@class, 'find-tickets')]",
                "//button[contains(@class, 'find-tickets')]"
            ]
            
            for selector in find_tickets_selectors:
                try:
                    find_tickets = WebDriverWait(driver, 5).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    if safe_click(find_tickets):
                        time.sleep(3)
                        # Get ticket details after clicking Find Tickets
                        try:
                            details['ticket_types'] = [
                                elem.text for elem in driver.find_elements(By.CSS_SELECTOR, ".ticket-type")
                            ]
                        except:
                            details['ticket_types'] = []
                        
                        try:
                            details['ticket_prices'] = [
                                elem.text for elem in driver.find_elements(By.CSS_SELECTOR, ".ticket-price")
                            ]
                        except:
                            details['ticket_prices'] = []
                        
                        break
                except:
                    continue
        except:
            logging.warning("Could not find or click Find Tickets button")
            
        # Get additional info
        try:
            details['additional_info'] = driver.find_element(By.CSS_SELECTOR, ".event-info").text
        except:
            details['additional_info'] = "Not found"
            
        driver.close()
        driver.switch_to.window(main_window)
        return details
    except Exception as e:
        logging.error(f"Error getting event details: {str(e)}")
        try:
            driver.switch_to.window(main_window)
        except:
            pass
        return {}

def process_events_list(driver, category, section_type, section_name):
    """Process all events in the current view, including clicking More Events"""
    events_data = []
    processed_urls = set()
    
    try:
        # Get total events count if available
        total_events = get_total_event_count(driver)
        if total_events:
            logging.info(f"Total events to process: {total_events}")
        
        while True:
            # Get current events
            events = driver.find_elements(By.CSS_SELECTOR, "[data-bdd='event-card'], .event-item")
            
            # Process each event
            for idx, event in enumerate(events, 1):
                try:
                    event_url = event.find_element(By.CSS_SELECTOR, "a").get_attribute("href")
                    
                    # Skip if already processed
                    if event_url in processed_urls:
                        continue
                        
                    # Scroll event into view
                    driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", event)
                    time.sleep(1)
                    
                    # Get event details
                    event_details = explore_event_details(driver, event_url)
                    event_details.update({
                        'main_category': category,
                        'section_type': section_type,
                        'section_name': section_name,
                        'url': event_url
                    })
                    
                    events_data.append(event_details)
                    processed_urls.add(event_url)
                    
                    logging.info(f"Processed event {len(processed_urls)}: {event_details.get('event_name', 'Unknown')}")
                    
                except Exception as e:
                    logging.warning(f"Failed to process event: {str(e)}")
                    continue
            
            # Try to click More Events
            if not click_more_events(driver):
                break
            
            # Wait for new events to load
            time.sleep(3)
            
            # Check if we've processed all events
            if total_events and len(processed_urls) >= total_events:
                break
    
    except Exception as e:
        logging.error(f"Error processing events list: {str(e)}")
    
    return events_data

def scrape_ticketmaster():
    """Main scraping function"""
    driver = None
    try:
        driver = setup_driver()
        logging.info("Driver setup successful")
        
        driver.get("https://www.ticketmaster.com")
        logging.info("Navigated to Ticketmaster")
        
        try:
            cookie_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            cookie_button.click()
            logging.info("Accepted cookies")
        except:
            logging.info("No cookie consent needed")
        
        all_data = []
        
        # Process each main category
        for category, sections in CATEGORY_STRUCTURE.items():
            try:
                logging.info(f"\nProcessing main category: {category}")
                
                # Navigate to category
                category_link = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.XPATH, f"//a[contains(text(), '{category}')]"))
                )
                driver.execute_script("arguments[0].click();", category_link)
                time.sleep(3)
                
                # Process popular sections
                for popular_section in sections['popular']:
                    try:
                        if click_popular_section(driver, popular_section):
                            logging.info(f"Processing popular section: {popular_section}")
                            
                            # Process all events including More Events
                            section_data = process_events_list(driver, category, 'popular', popular_section)
                            all_data.extend(section_data)
                            
                            # Save progress
                            if all_data:
                                df = pd.DataFrame(all_data)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f'ticketmaster_events_progress_{timestamp}.csv'
                                df.to_csv(filename, index=False)
                                logging.info(f"Progress saved to {filename}")
                            
                            # Return to category page
                            driver.get(f"https://www.ticketmaster.com/{category.lower()}")
                            time.sleep(2)
                    except Exception as e:
                        logging.error(f"Error processing popular section {popular_section}: {str(e)}")
                        continue
                
                # Process discover sections
                for discover_section in sections['discover']:
                    try:
                        if click_discover_section(driver, discover_section):
                            logging.info(f"Processing discover section: {discover_section}")
                            
                            # Process all events including More Events
                            section_data = process_events_list(driver, category, 'discover', discover_section)
                            all_data.extend(section_data)
                            
                            # Save progress
                            if all_data:
                                df = pd.DataFrame(all_data)
                                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                filename = f'ticketmaster_events_progress_{timestamp}.csv'
                                df.to_csv(filename, index=False)
                                logging.info(f"Progress saved to {filename}")
                            
                            # Return to category page
                            driver.get(f"https://www.ticketmaster.com/{category.lower()}")
                            time.sleep(2)
                    except Exception as e:
                        logging.error(f"Error processing discover section {discover_section}: {str(e)}")
                        continue
                
                # Return to homepage for next category
                driver.get("https://www.ticketmaster.com")
                time.sleep(2)
                
            except Exception as e:
                logging.error(f"Error processing category {category}: {str(e)}")
                continue
        
        # Save final data
        if all_data:
            df = pd.DataFrame(all_data)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f'ticketmaster_events_final_{len(all_data)}_{timestamp}.csv'
            df.to_csv(filename, index=False)
            logging.info(f"Final data saved to {filename}")
        
        return all_data
    
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
        return None
    
    finally:
        if driver:
            driver.quit()
            logging.info("Driver closed")

if __name__ == "__main__":
    try:
        logging.info("Starting scraper...")
        results = scrape_ticketmaster()
        if results:
            logging.info(f"Successfully scraped {len(results)} events")
        else:
            logging.error("No results obtained")
    except Exception as e:
        logging.error(f"Main execution failed: {str(e)}") 