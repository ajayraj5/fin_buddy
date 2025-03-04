import time
from datetime import datetime
from bs4 import BeautifulSoup # type: ignore
import os
import re
import pandas as pd # type: ignore
from selenium import webdriver # type: ignore
from selenium.webdriver.chrome.options import Options # type: ignore
from selenium.webdriver.support.ui import WebDriverWait # type: ignore
from selenium.webdriver.support import expected_conditions as EC # type: ignore
from selenium.webdriver.common.by import By # type: ignore
from selenium.webdriver.common.keys import Keys # type: ignore
from selenium.webdriver.common.action_chains import ActionChains # type: ignore
from selenium.common.exceptions import TimeoutException # type: ignore

import tempfile
import frappe
import fin_buddy.utils.dates as MakeDateValid


def setup_user_directory(username="user_not_defined", site_name="default_site"):
    """Create and return a user-specific download directory under a site-specific path"""
    base_download_dir = os.path.join(os.getcwd(), "downloads")
    site_dir = os.path.join(base_download_dir, site_name)
    user_dir = os.path.join(site_dir, username)
    
    # Create directories if they don't exist
    for directory in [base_download_dir, site_dir, user_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    return user_dir

def setup_chrome_options(user_download_dir):
    """Setup Chrome options with the specified download directory"""
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 20.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("useAutomationExtension", False)
    options.add_experimental_option('excludeSwitches', ['enable-automation'])

    # Always create a unique temporary directory for user data regardless of environment
    # Include timestamp to ensure uniqueness between runs
    import time
    timestamp = int(time.time())
    unique_user_data_dir = os.path.join(tempfile.gettempdir(), f"chrome_user_data_{os.getpid()}_{timestamp}")
    options.add_argument(f"--user-data-dir={unique_user_data_dir}")
    
    # Clean up any existing user data directories that might be causing conflicts
    try:
        import glob
        old_dirs = glob.glob(os.path.join(tempfile.gettempdir(), "chrome_user_data_*"))
        for old_dir in old_dirs:
            # Only delete directories older than 24 hours to avoid conflicts with running processes
            if os.path.isdir(old_dir) and os.path.getmtime(old_dir) < time.time() - 86400:
                import shutil
                try:
                    shutil.rmtree(old_dir, ignore_errors=True)
                except Exception:
                    pass  # Silently ignore errors in cleanup
    except Exception:
        pass  # Don't let cleanup failures affect main functionality
        
    settings = frappe.get_single("FinBuddy Settings")
    if settings.env == 'Production':
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

    prefs = {
        "download.default_directory": user_download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
        "profile.default_content_setting_values.automatic_downloads": 1,
        "profile.content_settings.exceptions.automatic_downloads.*.setting": 1,
        "plugins.always_open_pdf_externally": True,
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
        "profile.block_third_party_cookies": False,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.notifications": 2
    }
    options.add_experimental_option("prefs", prefs)
    return options

def setup_driver(username=None, site_name="default_site"):
    """Initialize and return Chrome WebDriver"""
    user_download_dir = setup_user_directory(username, site_name)
    options = setup_chrome_options(user_download_dir)
    driver = webdriver.Chrome(options=options)
    return driver, user_download_dir


def find_latest_download(directory):
        """Find the most recently downloaded file in the directory"""
        try:
            files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            if not files:
                return None
            return max(files, key=os.path.getctime)
        except Exception as e:
            print(f"Error finding latest download: {str(e)}")
            return None  

def get_or_create_gst_client_document(client_name):
    """Get existing GST Notice or create new one."""
    existing_records = frappe.get_all(
        "GST Notice",
        filters={'client': client_name},
        fields=["name"]
    )
    
    if existing_records:
        return frappe.get_doc("GST Notice", existing_records[0]['name'])
        
    # Create new record
    try:
        new_doc = frappe.get_doc({
            "doctype": "GST Notice",
            "client": client_name
        })
        new_doc.insert()
        frappe.db.commit()
        return new_doc
    except Exception as e:
        frappe.log_error(f"Failed to create GST Notice: {str(e)}")
        return None


def login_user_old(driver, username, password):
    """
    Start the login process and capture the captcha.
    Returns the captcha image path and maintains the session.
    """
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://services.gst.gov.in/services/login")
        time.sleep(1)

        # Enter Username
        username_field = wait.until(
            EC.visibility_of_element_located((By.ID, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)

        # Enter Password
        password_field = wait.until(
            EC.visibility_of_element_located((By.ID, "user_pass"))
        )
        password_field.clear()
        password_field.send_keys(password)

        time.sleep(4)
        # Find the captcha element
        captcha_element = wait.until(
            EC.visibility_of_element_located((By.ID, "imgCaptcha"))
        )
        
        # Take a screenshot of the captcha element
        captcha_image_path = os.path.join(frappe.get_site_path('public', 'files'), f'captcha_{username}_{int(time.time())}.png')
        captcha_element.screenshot(captcha_image_path)
        
        # Return the relative path to be used in the frontend
        relative_path = os.path.basename(captcha_image_path)
        return {
            "status": "captcha_needed",
            "captcha_path": f"/files/{relative_path}"
        }

    except Exception as e:
        print(f"Login preparation failed for user {username}: {str(e)}")
        return {"status": "error", "message": str(e)}
    


def complete_login(driver, captcha_text):
    """Complete the login process with the provided captcha"""
    try:
        wait = WebDriverWait(driver, 20)
        
        # Enter captcha
        captcha_field = wait.until(
            EC.visibility_of_element_located((By.ID, "captcha"))
        )
        captcha_field.clear()
        captcha_field.send_keys(captcha_text)

        # Click Login Button
        login_btn = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "button.btn-primary"))
        )
        login_btn.send_keys(Keys.RETURN)

        # Wait for login to complete
        time.sleep(17)
        
        # You can add additional checks here to verify login success
        
        return True

    except Exception as e:
        print(f"Login completion failed: {str(e)}")
        return False



def navigate_to_notices_old(driver):
    """Navigate through the GST portal to reach notices page"""
    try:
        wait = WebDriverWait(driver, 20)
        
        # Click on Services dropdown
        services_dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, "//a[@class='dropdown-toggle' and @aria-expanded='true' and contains(text(),'Services ')]")))
        services_dropdown.click()


        # Click on User Services
        user_services = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//a[@href='//services.gst.gov.in/services/auth/quicklinks/userservices' and contains(text(),'User Services')]")))
        user_services.click()

        # Click on View Notices and Orders
        notices_link = wait.until(EC.visibility_of_element_located((
            By.XPATH, "//a[@href='//services.gst.gov.in/services/auth/notices' and contains(text(),'View Notices and Orders')]")))
        notices_link.click()

        time.sleep(5)  # Wait for page to load completely
        return True

    except TimeoutException as e:
        print(f"Navigation failed: {str(e)}")
        return False


def navigate_to_notices(driver):
    """
    Navigate through the GST portal to reach notices page with improved hover handling
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if navigation successful, False otherwise
    """
    try:
        wait = WebDriverWait(driver, 30)
        actions = ActionChains(driver)
        
        # First find the Services dropdown without clicking
        services_dropdown = wait.until(EC.presence_of_element_located((
            By.XPATH, 
            "//li[contains(@class,'menuList')]//a[contains(text(),'Services')]"
        )))
        
        # Hover over the Services dropdown instead of clicking
        # actions.move_to_element(services_dropdown).perform()
        services_dropdown.click()
        time.sleep(1)  # Short pause to let hover effect take place
        
        # Now try to find User Services in the revealed dropdown
        user_services = wait.until(EC.visibility_of_element_located((
            By.XPATH,
            "//a[contains(@href,'services.gst.gov.in/services/auth/quicklinks/userservices')]"
        )))
        
        # Hover over User Services before clicking
        actions.move_to_element(user_services).perform()
        time.sleep(1)
        user_services.click()
        
        # Wait for the User Services page to load
        wait.until(EC.url_contains('services/auth/quicklinks/userservices'))
        
        # Wait for the "View Notices and Orders" link to be visible
        # notices_link = wait.until(EC.visibility_of_element_located((
        #     By.XPATH,
        #     "//li[./a[contains(text(), 'View Notices and Orders')]]/a"
        # )))

        # # Click on the link
        # notices_link.click()

        click_view_notices(driver)
        # Wait for the notices page to load
        # wait.until(EC.url_contains('services/auth/notices'))
        
        return True
        
    except TimeoutException as e:
        print(f"Navigation failed: {str(e)}")
        # Detailed debugging information
        try:
            print("\nCurrent URL:", driver.current_url)
            print("\nChecking element visibility:")
            
            # Check Services dropdown
            try:
                services = driver.find_element(By.XPATH, "//a[contains(text(),'Services')]")
                print("Services dropdown found:", services.is_displayed())
                print("Services dropdown classes:", services.get_attribute('class'))
            except:
                print("Services dropdown not found")
            
            # Check User Services visibility
            try:
                user_services = driver.find_element(By.XPATH, "//a[contains(text(),'User Services')]")
                print("User Services found:", user_services.is_displayed())
                print("User Services classes:", user_services.get_attribute('class'))
            except:
                print("User Services element not found")
                
        except Exception as debug_e:
            print(f"Error during debugging: {str(debug_e)}")
            
        return False
        
    except Exception as e:
        print(f"Unexpected error during navigation: {str(e)}")
        return False


def click_view_notices(driver):
    """
    Click on View Notices and Orders link after reaching User Services
    
    Args:
        driver: Selenium WebDriver instance
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        wait = WebDriverWait(driver, 20)
        
        # Try multiple approaches to find the notices link
        selectors = [
            # By exact link text
            "//a[text()='View Notices and Orders']",
            # By href
            "//a[@href='//services.gst.gov.in/services/auth/notices']",
            # By ng-if parent and link combination
            "//li[contains(@ng-if, 'udata.utype')]//a[contains(@href, 'notices')]",
            # By target and href combination
            "//a[@target='_self' and contains(@href, 'notices')]"
        ]
        
        for selector in selectors:
            try:
                notices_link = wait.until(
                    EC.presence_of_element_located((By.XPATH, selector))
                )
                if notices_link.is_displayed():
                    # Try scrolling to the element first
                    driver.execute_script("arguments[0].scrollIntoView(true);", notices_link)
                    time.sleep(1)  # Let the scroll complete
                    
                    # Try JavaScript click first
                    try:
                        driver.execute_script("arguments[0].click();", notices_link)
                        print(f"Successfully clicked using JavaScript with selector: {selector}")
                        time.sleep(2)  # Wait for navigation
                        return True
                    except:
                        # If JavaScript click fails, try regular click
                        notices_link.click()
                        print(f"Successfully clicked using regular click with selector: {selector}")
                        time.sleep(2)  # Wait for navigation
                        return True
            except:
                continue
                
        # If we get here, none of the selectors worked
        print("Failed to find or click the notices link with any selector")
        
        # Additional debugging information
        print("\nCurrent page source snippet:")
        try:
            # Get a snippet of the page source around where the link should be
            page_source = driver.page_source
            if "View Notices and Orders" in page_source:
                print("Link text found in page source but not clickable")
            if "services.gst.gov.in/services/auth/notices" in page_source:
                print("Link URL found in page source but not clickable")
        except:
            print("Could not analyze page source")
            
        return False
        
    except Exception as e:
        print(f"Error attempting to click notices link: {str(e)}")
        return False


def extract_notice_data(driver, user_download_dir, client_name):
    """Extract data from the notices table"""
    try:
        wait = WebDriverWait(driver, 20)
        table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "table")))
        rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # Skip header row
        
        gst_doc = get_or_create_gst_client_document(client_name)
        if not gst_doc:
            return False, "Failed to get or create GST Notice document"
        
        gst_doc.notices = []
        gst_doc.save()
        frappe.db.commit()


        notices_data = []
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if len(cols) >= 8:
                notice_data = {
                    'notice_id': cols[0].text,
                    'issued_by': cols[1].text,
                    'type': cols[2].text,
                    'description': cols[3].text,
                    'issue_date': cols[4].text,
                    'due_date': cols[5].text,
                    'amount': cols[6].text
                }

                converted_date = MakeDateValid.get_frappe_date(notice_data['issue_date'])
                notice_data['issue_date'] = converted_date

                converted_date = MakeDateValid.get_frappe_date(notice_data['due_date'])
                notice_data['due_date'] = converted_date
                
                # Handle document download
                download_btn = cols[7].find_element(By.CSS_SELECTOR, "a.btn-download")
                if download_btn:
                    try:
                        download_btn.click()
                        time.sleep(2)  # Wait for download to initiate

                        file_path = find_latest_download(user_download_dir)
                        if file_path:
                            response = create_and_attach_file_in_gst_notices_table(gst_doc, notice_data, file_path)
                            print(response)
                        else:
                            print(f"No file downloaded for Notice ID {notice_data['notice_id']} ")

                    except Exception as e:
                        print(f"Failed to download document for {notice_data['notice_id']}: {str(e)}")
                
                notices_data.append(notice_data)
        
        return notices_data

    except Exception as e:
        print(f"Data extraction failed: {str(e)}")
        return []
    
# def get_or_create_gst_notice(client_name):

#         existing_doc = frappe.get_all("GST Notice",
#             filters={'client': client_name},
#             field=['name']
#         )

#         if existing_doc:
#             gst_doc = frappe.get_doc("GST Notice", existing_doc[0]['name'])
#             gst_doc.notices = []
#             gst_doc.additional_notices = []
#             gst_doc.save()
#             frappe.db.commit()

#             return gst_doc
        
#         try:
#             gst_doc = frappe.get_doc({
#                 "doctype": "GST Notice",
#                 "client": client_name
#             })
#             gst_doc.insert()
#             frappe.db.commit()

#             return gst_doc
#         except Exception as e:
#             frappe.log_error(f"Failed to create GST Notice: {str(e)}")
#             return None


def create_and_attach_file_in_gst_notices_table(gst_doc, notice_data, file_path):
    """Create File document and attach to GST Notice."""
    try:
        # First, create a new GST Notice Reply
        child_notice_doc = frappe.get_doc({
            "doctype": "GST Notice Item",
            "parent": gst_doc.name,
            "parenttype": "GST Notice",
            "parentfield": "notices",
            **notice_data
        })
        child_notice_doc.insert()
        
        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()
        
        file_name = os.path.basename(file_path)
        # Create File document
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "GST Notice Item",
            "attached_to_field": "file",
            "attached_to_name": child_notice_doc.name,  # Added this line
            "is_private": 1,
            "content": content
        })
        
        new_doc = file_doc.insert()
        
        # Update the reply with the file URL
        child_notice_doc.file = new_doc.file_url
        child_notice_doc.save()
        frappe.db.commit()
        
        return True, f"Successfully added file '{notice_data['notice_id']}' to GST Notice {gst_doc.name}"
        
    except Exception as e:
        frappe.db.rollback()
        return False, f"Failed to create and attach file: {str(e)}"



def create_gst_additional_notice_table(client_name, notices_data):
    """Create GST Additional Notice Item."""
    try:

        gst_doc = get_or_create_gst_client_document(client_name)
        if not gst_doc:
            return False, "Failed to get or create GST Notice document"


        gst_doc.additional_notices = []
        
        # First, create a new GST Additional Notice Reply
        for notice_data in notices_data:
            # child_notice_doc = frappe.get_doc({
            #     "doctype": "GST Additional Notice Item",
            #     "parent": gst_doc.name,
            #     "parenttype": "GST Notice",
            #     "parentfield": "additional_notices",
            #     **notice_data
            # })
            # child_notice_doc.insert()
            # frappe.db.commit()
            gst_doc.append("additional_notices",{
                **notice_data
            })
        
        gst_doc.save()
        frappe.db.commit()

        return True, f"Successfully created all GST Additional Notice for {gst_doc.name}"
        
    except Exception as e:
        frappe.db.rollback()
        return False, f"Failed to create GST Additional Notice Item: {str(e)}"




# def add_hyperlink_to_gst_notices(notice_data, link_text, file_path):
#     """
#     Returns:
#         tuple: (bool, str) - (Success status, Message describing the outcome)
#     """
#     try:
#         # Validate input parameters
#         if not all([notice_data, link_text, file_path]):
#             return False, "Missing required parameters"
            
#         if not os.path.exists(file_path):
#             return False, f"File not found: {file_path}"
            
#         # Prepare filters for finding existing GST Notice
#         # filters = _prepare_filters(notice_data)
        
#         # Get or create GST Notice document
#         # doc = get_or_create_eproceeding(filters, notice_data)
#         # if not doc:
#             # return False, "Failed to get or create GST Notice document"
            
#         # Check for existing file
#         # if _file_exists_in_replies(doc, link_text):
#         #     return True, f"File '{link_text}' already exists in GST Notice {doc.name}"
            
#         # Create and attach new file
#         success, message = _create_and_attach_file(gst_doc, link_text, file_path)
#         return success, message
        
#     except Exception as e:
#         frappe.db.rollback()
#         return False, f"Error processing request: {str(e)}"






def save_to_excel(notices_data, user_download_dir):
    """Save extracted data to Excel file"""
    if notices_data:
        try:
            df = pd.DataFrame(notices_data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_path = os.path.join(user_download_dir, f"notices_data_{timestamp}.xlsx")
            df.to_excel(excel_path, index=False)
            print(f"Data saved to {excel_path}")
            return True
        except Exception as e:
            print(f"Failed to save Excel file: {str(e)}")
            return False
    return False


def extract_gst_additional_notice_data_old(driver):
    try:
        driver.execute_script("document.body.scrollTop = 0; document.documentElement.scrollTop = 0;")

        time.sleep(1)

        # Wait for and click on Additional Notices and Orders link
        additional_notices = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Additional Notices and Orders')]"))
        )
        additional_notices.click()
        
        # Wait for the page to load and click on 100 entries button
        # entries_100 = WebDriverWait(driver, 10).until(
        #     EC.element_to_be_clickable((By.XPATH, "//button[.//span[text()='100']]"))
        # )
        # entries_100.click()
        
        # Wait for table to load
        time.sleep(2)  # Add small delay to ensure table refreshes
        
        # Extract table data
        notices_data = []
        rows = driver.find_elements(By.XPATH, "//table[@class='table tbl inv table-bordered text-center ng-table']//tbody//tr")
        
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            notice_type = cols[0].find_element(By.TAG_NAME, "span").text
            description = cols[1].find_element(By.TAG_NAME, "span").text
            ref_id = cols[2].find_element(By.TAG_NAME, "span").text
            date = cols[3].find_element(By.TAG_NAME, "span").text

            converted_date = MakeDateValid.get_frappe_date(date)
            
            notices_data.append({
                'type_of_notice': notice_type,
                'description': description,
                'ref_id': ref_id,
                'date_of_issuance': converted_date
            })
            
        # Convert to pandas DataFrame
        # df = pd.DataFrame(notices_data)
        
        # Save to CSV
        # df.to_csv('gst_notices.csv', index=False)
        
        # return df
        return notices_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    

def extract_notice_details(driver):
    detail_info = {}
    try:
        # Extract all tables on the page
        tables = driver.find_elements(By.TAG_NAME, "table")
        
        for table in tables:
            # Scroll to make the table visible
            driver.execute_script("arguments[0].scrollIntoView(true);", table)
            time.sleep(1)
            
            # Extract rows from the table
            rows = table.find_elements(By.TAG_NAME, "tr")
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 2:
                    # First cell is header, second is value
                    header = cells[0].text.strip()
                    value = cells[1].text.strip()
                    if header and not header.startswith("Sr."):  # Skip numbered rows
                        detail_info[header] = value
        
        # Look for specific sections or elements
        try:
            # Case ID
            case_id_elem = driver.find_element(By.XPATH, "//div[contains(text(), 'Case ID')]/following-sibling::div")
            if case_id_elem:
                detail_info["Case ID"] = case_id_elem.text.strip()
                
            # GSTIN/UIN
            gstin_elem = driver.find_element(By.XPATH, "//div[contains(text(), 'GSTIN/UIN')]/following-sibling::div")
            if gstin_elem:
                detail_info["GSTIN/UIN"] = gstin_elem.text.strip()
                
            # Status
            status_elem = driver.find_element(By.XPATH, "//div[contains(text(), 'Status')]/following-sibling::div")
            if status_elem:
                detail_info["Status"] = status_elem.text.strip()
        except:
            pass
            
        return detail_info
        
    except Exception as e:
        print(f"Error extracting notice details: {str(e)}")
        return detail_info
    


# def get_latest_download_path():
#     """Get the most recently downloaded file path"""
#     download_dir = "Your download directory path"
#     files = glob.glob(os.path.join(download_dir, "*"))
#     return max(files, key=os.path.getctime)

def upload_file(file_path):
    """Upload a file to Frappe and return file URL"""
    file_url = frappe.get_doc({
        "doctype": "File",
        "file_name": os.path.basename(file_path),
        "content": open(file_path, "rb").read()
    }).insert().file_url
    return file_url

def extract_and_save_case_data(driver, downloaded_file_path):
    # First, get the case details from the header section
    case_id = driver.find_element(By.XPATH, "//div[contains(@class, 'panel-body')]//span[text()='Case ID']/following-sibling::p/b").text
    gstin = driver.find_element(By.XPATH, "//div[contains(@class, 'panel-body')]//span[text()='GSTIN/UIN/Temporary ID']/following-sibling::p/b").text
    case_creation_date = driver.find_element(By.XPATH, "//div[contains(@class, 'panel-body')]//span[text()='Date Of Application/Case Creation']/following-sibling::p/b").text
    status = driver.find_element(By.XPATH, "//div[contains(@class, 'panel-body')]//span[text()='Status']/following-sibling::p/b").text


    print("Case ID", case_id, gstin, case_creation_date, status)
    
    # Create a new Case Details document
    case_details = frappe.new_doc("Case Details")
    case_details.case_id = case_id
    case_details.gstin = gstin
    case_details.case_creation_date = case_creation_date
    case_details.status = status
    
    # Now get the table rows
    rows = driver.find_elements(By.XPATH, "//tbody/tr")
    
    for row in rows:
        # Extract data from each row
        reply_type = row.find_element(By.XPATH, ".//td[1]/span").text
        reply_filed_against = row.find_element(By.XPATH, ".//td[2]/span").text
        reply_date = row.find_element(By.XPATH, ".//td[3]/span").text
        personal_hearing = row.find_element(By.XPATH, ".//td[4]/span").text
        
        # Create a new Reply document
        reply = frappe.new_doc("Case Details Reply")
        reply.reply_type = reply_type
        reply.reply_filed_against = reply_filed_against
        reply.reply_date = reply_date
        reply.personal_hearing = personal_hearing
        
        # Generate a unique reply_id
        # reply.reply_id = f"{reply_filed_against}_{reply_date.replace('/', '')}"
        
        # Save the reply
        reply.save()
        frappe.db.commit()
        
        # Now find all attachment links in this row
        attachment_links = row.find_elements(By.XPATH, ".//td[5]//a[@download-doc-secure]")
        
        for link in attachment_links:
            
            # Get the file name
            file_name = link.find_element(By.XPATH, ".//span[@title='Attachments']").text
            
            # Click to download
            driver.execute_script("arguments[0].click();", link)
            time.sleep(3)  # Wait for download

            file_path = find_latest_download(downloaded_file_path)
            if file_path:
                response = attach_file_in_reply(reply, file_path)
            # Now find the downloaded file path
            # downloaded_file_path = get_latest_download_path()  # You'll need to implement this function
            
            # Upload the file to Frappe
            # file_doc = frappe.get_doc({
            #     "doctype": "File",
            #     "file_name": file_name,
            #     "attached_to_doctype": "Case Details Reply",
            #     "attached_to_name": reply.name,
            #     "file_url": upload_file(downloaded_file_path)  # You'll need to implement this function
            # }).insert()
            
            # # Add to attachment child table
            # reply.append("attachments", {
            #     "file": file_doc.file_url
            # })
        
        # Save reply again with attachments
        # reply.save()
        
        # Add to case details child table
        case_details.append("replies", {
            "reply_id": reply.name
        })
        
    # Save the case details document
    case_details.save()
    frappe.db.commit()
    return case_details.name

def attach_file_in_reply(reply, file_path):

            # Upload the file to Frappe
    # file_doc = frappe.get_doc({
    #             "doctype": "File",
    #             "file_name": file_name,
    #             "attached_to_doctype": "Case Details Reply",
    #             "attached_to_name": reply.name,
    #             "file_url": upload_file(downloaded_file_path)  # You'll need to implement this function
    #         }).insert()
    


    """Create File document and attach to GST Notice."""
    try:
        # First, create a new GST Notice Reply
        child_notice_doc = frappe.get_doc({
            "doctype": "Attachment Item",
            "parent": reply.name,
            "parenttype": "Case Details Reply",
            "parentfield": "attachments",
        })
        child_notice_doc.insert()
        
        # Read file content
        with open(file_path, "rb") as f:
            content = f.read()
        
        file_name = os.path.basename(file_path)
        # Create File document
        file_doc = frappe.get_doc({
            "doctype": "File",
            "file_name": file_name,
            "attached_to_doctype": "Attachment Item",
            "attached_to_field": "file",
            "attached_to_name": child_notice_doc.name,  # Added this line
            "is_private": 1,
            "content": content
        })
        
        new_doc = file_doc.insert()
        
        # Update the reply with the file URL
        child_notice_doc.file = new_doc.file_url
        child_notice_doc.save()
        frappe.db.commit()
        
        return True, f"Successfully added file"
        
    except Exception as e:
        frappe.db.rollback()
        return False, f"Failed to create and attach file: {str(e)}"




def extract_gst_additional_notice_data(driver, user_download_dir):
    try:
        # Make sure we're starting from the top of the page
        driver.execute_script("document.body.scrollTop = 0; document.documentElement.scrollTop = 0;")
        time.sleep(1)

        # Wait for and click on Additional Notices and Orders link
        additional_notices = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Additional Notices and Orders')]"))
        )
        additional_notices.click()
        
        # Wait for table to load
        time.sleep(2)
        
        # Extract basic table data first
        notices_data = []
        wait = WebDriverWait(driver, 10)
        
        # Find all rows in the table
        rows = driver.find_elements(By.XPATH, "//table[@class='table tbl inv table-bordered text-center ng-table']//tbody//tr")
        print(f"Found {len(rows)} notices")
        
        # First pass: Extract basic data from the table
        for i, row in enumerate(rows):
            cols = row.find_elements(By.TAG_NAME, "td")
            
            notice_type = cols[0].find_element(By.TAG_NAME, "span").text
            description = cols[1].find_element(By.TAG_NAME, "span").text
            ref_id = cols[2].find_element(By.TAG_NAME, "span").text
            date = cols[3].find_element(By.TAG_NAME, "span").text
            
            # Store the basic data
            notice_data = {
                'Type of Notice/Order': notice_type,
                'Description': description,
                'Ref ID': ref_id,
                'Date of Issuance': date,
                # 'Detail Info': {},
                # 'Attachments': []
            }
            
            notices_data.append(notice_data)
        
        # Save the initial data to Excel as a backup
        temp_df = pd.DataFrame(notices_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        temp_excel_path = os.path.join(user_download_dir, f"notices_basic_data_{timestamp}.xlsx")
        temp_df.to_excel(temp_excel_path, index=False)
        print(f"Basic data saved to {temp_excel_path}")
        
        # Second pass: Click each View button and extract detailed info
        for i in range(len(rows)):
            try:
                # Re-fetch the rows as they might become stale
                rows = driver.find_elements(By.XPATH, "//table[@class='table tbl inv table-bordered text-center ng-table']//tbody//tr")
                row = rows[i]
                
                # Find View button in the last column
                view_button = row.find_elements(By.TAG_NAME, "td")[-1].find_element(By.TAG_NAME, "a")
                
                if view_button.text == "View":
                    print(f"Clicking View for notice {i+1}/{len(rows)}: {notices_data[i]['Ref ID']}")
                    
                    # Scroll to and click the View button
                    # driver.execute_script("arguments[0].scrollIntoView(true);", view_button)
                    time.sleep(1)
                    try:
                        driver.execute_script("arguments[0].click();", view_button)
                    except:
                        view_button.click()
                    
                    # Wait for the details page to load
                    time.sleep(2)
                    
                    # Extract details from the new page
                    detail_info = extract_notice_details(driver)
                    notices_data[i]['Detail Info'] = detail_info
                    
                    # Download any attachments
                    attachments = download_attachments(driver, user_download_dir, notices_data[i]['Ref ID'])
                    notices_data[i]['Attachments'] = attachments
                    
                    # Navigate back to the notices list using the Additional Notices and Orders link
                    try:
                        # Find and click on the Dashboard link first (to navigate up in the hierarchy)
                        # dashboard_link = WebDriverWait(driver, 5).until(
                        #     EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Dashboard')]"))
                        # )
                        # dashboard_link.click()
                        # time.sleep(2)
                        
                        # Now click on "Additional Notices and Orders" link to get back to the list
                        additional_notices_link = WebDriverWait(driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Additional Notices and Orders')]"))
                        )
                        additional_notices_link.click()
                        time.sleep(2)
                    except Exception as nav_error:
                        print(f"Navigation error: {str(nav_error)}")
                        # Fallback: go directly to the notices page
                        driver.get("https://services.gst.gov.in/services/auth/notices")
                        time.sleep(3)
                        additional_notices = WebDriverWait(driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Additional Notices and Orders')]"))
                        )
                        additional_notices.click()
                        time.sleep(2)
                    
            except Exception as e:
                print(f"Error processing notice {i+1}: {str(e)}")
                # Try to get back to the notices list if there was an error
                try:
                    driver.get("https://services.gst.gov.in/services/auth/notices")
                    time.sleep(3)
                    additional_notices = WebDriverWait(driver, 10).until(
                        EC.element_to_be_clickable((By.XPATH, "//a[contains(text(), 'Additional Notices and Orders')]"))
                    )
                    additional_notices.click()
                    time.sleep(2)
                except:
                    print("Failed to recover from error")
        
        return notices_data
        
    except Exception as e:
        print(f"An error occurred during notice extraction: {str(e)}")
        return []


def download_attachments(driver, user_download_dir, ref_id):
    attachments = []
    try:
        table = driver.find_element(By.CSS_SELECTOR, ".table-responsive")  # Replace with your table's selector

        # Scroll the table to the right
        driver.execute_script("arguments[0].scrollLeft += 500;", table)
        
        # Check if there are attachments in the table
        attachment_cells = driver.find_elements(By.XPATH, "//div[@class='list-group']/a")

        print("attachments_cells", len(attachment_cells))

        
        if attachment_cells:
            for cell in attachment_cells:
                driver.execute_script("arguments[0].click();", cell)

                time.sleep(5)
                attachment_links = driver.find_elements(By.XPATH, "//span[@title='Attachments']/p/a")
                if len(attachment_links) <= 0:
                    # attachment_links = driver.find_elements(By.XPATH, "//a[@download-doc-secure and .//span[@title='Attachments']]")
                    case_details_name = extract_and_save_case_data(driver, user_download_dir)


                print("attachments_links", len(attachment_links))

                # Click on each attachment link
                for link in attachment_links:
                    driver.execute_script("arguments[0].click();", link)
                    time.sleep(3)
                
                # driver.execute_script("arguments[0].scrollLeft -= 500;", table)

        
        return attachments
        
    except Exception as e:
        print(f"Error processing attachments: {str(e)}")
        return attachments




def process_gst_notices(client_name, username, password):
    """Main function to process GST notices"""
    driver = None
    try:
        # Setup driver and get download directory
        driver, user_download_dir = setup_driver(username, "gst")
        
        # Login
        if not login_user(driver, username, password):
            print("Login failed. Cannot proceed.")
            return
        
        # Navigate to notices page
        if not navigate_to_notices(driver):
            print("Navigation to notices failed. Cannot proceed.")
            return
        
        # Extract notice data
        # notices_data = extract_notice_data(driver, user_download_dir, client_name)
        # if not notices_data:
        #     print("DONE for gst notices table")
        #     # Save to Excel
        #     # save_to_excel(notices_data, user_download_dir)
        #     # save_to_gst_client_document(notices_data, )
        # else:
        #     print("No notice data extracted.")

        # Extract additional notice data
        add_notices_data = extract_gst_additional_notice_data(driver, user_download_dir)
        if add_notices_data:
            # Save to Excel
            create_gst_additional_notice_table(client_name, add_notices_data)
            print("done for the notice additional table")
            # save_to_excel(add_notices_data, user_download_dir)
        else:
            print("No notice data extracted.")

        
        time.sleep(2)
        # Logout the current user
        logout_user(driver)
                
    except Exception as e:
        print(f"Error during execution: {str(e)}")
    
    finally:
        if driver:  
            driver.quit()




def logout_user(driver):
    try:
        print("logout .......")
        driver.execute_script("document.body.scrollTop = 0; document.documentElement.scrollTop = 0;")

        # Allow time for scrolling
        time.sleep(1)

        dropdown_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
            By.XPATH,
            "//a[contains(@class, 'dropdown-toggle') and .//i[contains(@class, 'fa-user')]]"
        )))

        # Click the link
        dropdown_link.click()

        # Wait for the Logout link by targeting the icon class 'fa-sign-out'
        logout_link = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((
            By.XPATH,
            "//a[contains(@href, 'logout') and .//i[contains(@class, 'fa-sign-out')]]"
        )))

        # Click the link
        logout_link.click()

        time.sleep(3)
        return True
    except Exception as e:
        print(f"Logout failed: {str(e)}")
        return False


@frappe.whitelist()
def process_selected_clients(client_names):
    """
    Queue background jobs for processing selected clients
    
    Args:
        client_names: List of client document names to process
    """
    if isinstance(client_names, str):
        # Convert string representation to list if passed as JSON string
        import json
        client_names = json.loads(client_names)
    
    # Queue each client for processing
    for client_name in client_names:
        # Get the client doc
        doc = frappe.get_doc("GST Client", client_name)
        
        
        # Queue the background job
        if not doc.disabled:
            frappe.enqueue(
                'fin_buddy.events.gst_gov.process_single_client',
                queue='long',
                timeout=3000,
                client_name=client_name
            )
    
    return {"message": "Successfully queued selected clients for processing"}


def process_single_client(client_name):
    """Process a single client in the background
    
    Args:
        client_name: Name of the client document to process
    """
    try:
        # Get the client document
        doc = frappe.get_doc("GST Client", client_name)
        
        
        # Get credentials
        username = doc.gst_username
        password = doc.get_password("gst_password")
        
        if not username or not password:
            frappe.log_error(
                f"Missing credentials for client {client_name}",
                "GST Portal Sync Error"
            )
            frappe.throw(f"Missing credentials for client {client_name}")
            return
        
        # Setup Selenium and process
        # driver = setup_driver(username, "gst")
        
        start_time = time.time()
        
        try:    
                # setup of driver, login and processing and logout
                process_gst_notices(client_name, username, password)
                
        except Exception as e:
            error_msg = f"Error processing client {client_name}: {str(e)}"
            frappe.log_error(error_msg, "GST Portal Processing Error")
        finally:
            # Calculate processing time
            doc.last_gst_sync = datetime.now()
            
            # Save the document
            doc.save()
            frappe.db.commit()
                
    except Exception as e:
        error_msg = f"An error occurred in process_single_client for {client_name}: {str(e)}"
        frappe.log_error(error_msg, "GST Portal Sync Error")





@frappe.whitelist()
def login_into_portal(client_name):
    """
    Queue background jobs for processing a selected client.
    
    Args:
        client_name: Client document name to process.
    """
    if client_name:
        # Get the client doc
        doc = frappe.get_doc("GST Client", client_name)

        # Queue the background job
        if not doc.disabled:
            frappe.enqueue(
                'fin_buddy.events.gst_gov.login',
                queue='long',
                timeout=3000,
                client_name=client_name
            )
        else:
            return {"message": f"Client {client_name} is disabled !!"}
        
        return {"message": f"Successfully queued client {client_name} for processing"}
    else:
        return {"message": "No client found to process"}


def login(client_name):
    try:
        doc = frappe.get_doc("GST Client", client_name)
        # Get credentials
        username = doc.gst_username
        password = doc.get_password("gst_password")
        
        if not username or not password:
            frappe.log_error(
                f"Missing credentials for client {client_name}",
                "GST Portal Sync Error"
            )
            return
        
        # Setup Selenium and process
        driver, user_download_dir = setup_driver(username, "gst")
                
        try:
            login_user(driver, username, password)
        except Exception as e:
            frappe.log_error("Login User Failed", str(e))
    
    except Exception as e:
        frappe.log_error("Login Error In Client", str(e))



@frappe.whitelist()
def process_gst_client_login_old(client_name):
    """Start GST client login process and get captcha"""
    try:
        # Get the client document
        doc = frappe.get_doc("GST Client", client_name)
        
        # Get credentials
        username = doc.gst_username
        password = doc.get_password("gst_password")
        
        if not username or not password:
            return {"status": "error", "message": f"Missing credentials for client {client_name}"}
        
        # Setup driver
        driver, user_download_dir = setup_driver(username, "gst")
        
        # Start login and get captcha
        login_result = login_user(driver, username, password)
        
        if login_result["status"] == "captcha_needed":
            # Store the driver in a cache for later use
            session_id = frappe.generate_hash()
            
            # We need to store the driver object in a way it can be retrieved later
            # This is a simplified approach - you might need a more robust solution
            frappe.cache().set_value(
                f"gst_login_driver:{session_id}", 
                {
                    "driver_id": id(driver),  # Just for reference, not actually usable
                    "username": username,
                    "client_name": client_name,
                    "download_dir": user_download_dir
                },
                expires_in_sec=300  # 5 minutes
            )
            
            # Store the driver object in a global variable or another cache
            # This is not ideal but works for this example
            if not hasattr(frappe, "gst_drivers"):
                frappe.gst_drivers = {}
            frappe.gst_drivers[session_id] = driver
            
            return {
                "status": "captcha_needed",
                "session_id": session_id,
                "captcha_url": login_result["captcha_path"],
                "client_name": client_name
            }
        else:
            # Handle error case
            if driver:
                driver.quit()
            return login_result
            
    except Exception as e:
        error_msg = f"Error starting login process for {client_name}: {str(e)}"
        frappe.log_error(error_msg, "GST Portal Login Error")
        return {"status": "error", "message": error_msg}


@frappe.whitelist()
def submit_gst_captcha_old(session_id, captcha_text):
    """Complete the GST login with the provided captcha"""
    try:
        # Retrieve session info
        session_info = frappe.cache().get_value(f"gst_login_driver:{session_id}")
        if not session_info:
            return {"status": "error", "message": "Session expired. Please try again."}
        
        # Retrieve the driver from cache
        if not hasattr(frappe, "gst_drivers") or session_id not in frappe.gst_drivers:
            return {"status": "error", "message": "Driver session lost. Please try again."}
        
        driver = frappe.gst_drivers[session_id]
        client_name = session_info["client_name"]
        username = session_info["username"]
        user_download_dir = session_info["download_dir"]
        
        # Complete the login
        if complete_login(driver, captcha_text):
            # Login successful, now process the client
            try:
                # Continue with your existing process flow
                if navigate_to_notices(driver):
                    # Extract notice data
                    notices_data = extract_notice_data(driver, user_download_dir, client_name)
                    if not notices_data:
                        print("DONE for gst notices table")
                        # Save to Excel
                        # save_to_excel(notices_data, user_download_dir)
                        # save_to_gst_client_document(notices_data, )
                    else:
                        print("No notice data extracted.")


                    add_notices_data = extract_gst_additional_notice_data(driver, user_download_dir)
                    if add_notices_data:
                        create_gst_additional_notice_table(client_name, add_notices_data)
                        
                # Logout
                logout_user(driver)
                
                # Update client document
                doc = frappe.get_doc("GST Client", client_name)
                doc.last_gst_sync = datetime.now()
                doc.save()
                frappe.db.commit()
                
                return {"status": "success", "message": "Processing completed successfully"}
            except Exception as e:
                error_msg = f"Error processing client {client_name} after login: {str(e)}"
                frappe.log_error(error_msg, "GST Portal Processing Error")
                return {"status": "error", "message": error_msg}
            finally:
                # Clean up
                if driver:
                    driver.quit()
                # Remove from cache
                if hasattr(frappe, "gst_drivers") and session_id in frappe.gst_drivers:
                    del frappe.gst_drivers[session_id]
                frappe.cache().delete_value(f"gst_login_driver:{session_id}")
        else:
            return {"status": "error", "message": "Login failed. Invalid captcha or other login error."}
            
    except Exception as e:
        error_msg = f"Error submitting captcha: {str(e)}"
        frappe.log_error(error_msg, "GST Portal Captcha Error")
        return {"status": "error", "message": error_msg}
    














def login_user(driver, username, password):
    """
    Start the login process and capture the captcha.
    Returns the captcha image path and maintains the session.
    """
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://services.gst.gov.in/services/login")
        time.sleep(2)  # Increased wait time

        # Enter Username
        username_field = wait.until(
            EC.visibility_of_element_located((By.ID, "username"))
        )
        username_field.clear()
        username_field.send_keys(username)

        # Enter Password
        password_field = wait.until(
            EC.visibility_of_element_located((By.ID, "user_pass"))
        )
        password_field.clear()
        password_field.send_keys(password)

        time.sleep(4)
        # Find the captcha element
        captcha_element = wait.until(
            EC.visibility_of_element_located((By.ID, "imgCaptcha"))
        )
        
        # Take a screenshot of the entire page first to ensure browser is rendering properly
        page_screenshot_path = os.path.join(frappe.get_site_path('public', 'files'), f'page_{username}_{int(time.time())}.png')
        driver.save_screenshot(page_screenshot_path)
        
        # Get the location and size of the captcha element
        location = captcha_element.location
        size = captcha_element.size
        
        # Take a screenshot of the captcha element using PIL for better handling
        from PIL import Image
        img = Image.open(page_screenshot_path)
        
        # Calculate coordinates
        left = location['x']
        top = location['y']
        right = location['x'] + size['width']
        bottom = location['y'] + size['height']
        
        # Crop the image
        img = img.crop((left, top, right, bottom))
        
        # Save the cropped image
        captcha_image_path = os.path.join(frappe.get_site_path('public', 'files'), f'captcha_{username}_{int(time.time())}.png')
        img.save(captcha_image_path)
        
        # Clean up the page screenshot
        os.remove(page_screenshot_path)
        
        # Return the relative path to be used in the frontend
        relative_path = os.path.basename(captcha_image_path)
        return {
            "status": "captcha_needed",
            "captcha_path": f"/files/{relative_path}"
        }

    except Exception as e:
        print(f"Login preparation failed for user {username}: {str(e)}")
        return {"status": "error", "message": str(e)}


# Add a cleanup function to be run periodically
def cleanup_stale_gst_sessions():
    """Clean up any stale GST sessions to prevent memory leaks"""
    try:
        if hasattr(frappe.local, "gst_drivers"):
            current_time = time.time()
            sessions_to_remove = []
            
            for session_id, driver in frappe.local.gst_drivers.items():
                # Check if session is still valid
                heartbeat = frappe.cache().get_value(f"gst_session_heartbeat:{session_id}")
                
                if not heartbeat or (current_time - heartbeat > 600):  # 10 minutes
                    # Session expired, clean up
                    try:
                        driver.quit()
                    except Exception:
                        pass  # Ignore errors during driver cleanup
                    
                    sessions_to_remove.append(session_id)
            
            # Remove expired sessions
            for session_id in sessions_to_remove:
                del frappe.local.gst_drivers[session_id]
                frappe.cache().delete_value(f"gst_login_session:{session_id}")
                frappe.cache().delete_value(f"gst_session_heartbeat:{session_id}")
    except Exception as e:
        frappe.log_error(f"Error cleaning up GST sessions: {str(e)}", "GST Session Cleanup Error")


# Register cleanup task
# You can call this in hooks.py to run periodically
# e.g., in hooks.py: scheduler_events = { "hourly": ["fin_buddy.events.gst_gov.cleanup_stale_gst_sessions"] }

# Create a persistent global registry for drivers
if not hasattr(frappe, "_persistent_gst_drivers"):
    frappe._persistent_gst_drivers = {}


@frappe.whitelist()
def process_gst_client_login(client_name):
    """Start GST client login process and get captcha"""
    try:
        # Get the client document
        doc = frappe.get_doc("GST Client", client_name)
        
        # Get credentials
        username = doc.gst_username
        password = doc.get_password("gst_password")
        
        if not username or not password:
            return {"status": "error", "message": f"Missing credentials for client {client_name}"}
        
        # Setup driver
        driver, user_download_dir = setup_driver(username, "gst")
        
        # Start login and get captcha
        login_result = login_user(driver, username, password)
        
        if login_result["status"] == "captcha_needed":
            # Generate a unique session ID
            session_id = frappe.generate_hash()
            
            # Store the driver in our persistent registry
            frappe._persistent_gst_drivers[session_id] = driver
            
            # Store driver metadata in Redis cache
            frappe.cache().set_value(
                f"gst_session:{session_id}", 
                {
                    "username": username,
                    "client_name": client_name,
                    "download_dir": user_download_dir,
                    "created_at": time.time(),
                    "pid": os.getpid()  # Store the process ID
                },
                expires_in_sec=1200  # 20 minutes - generous timeout
            )
            
            return {
                "status": "captcha_needed",
                "session_id": session_id,
                "captcha_url": login_result["captcha_path"],
                "client_name": client_name
            }
        else:
            # Handle error case
            if driver:
                driver.quit()
            return login_result
            
    except Exception as e:
        error_msg = f"Error starting login process for {client_name}: {str(e)}"
        frappe.log_error(error_msg, "GST Portal Login Error")
        return {"status": "error", "message": error_msg}

@frappe.whitelist()
def check_session_status(session_id):
    """Check if a session is still valid"""
    try:
        # Check if session exists in Redis
        session_info = frappe.cache().get_value(f"gst_session:{session_id}")
        if not session_info:
            return {"status": "error", "valid": False, "message": "Session expired or not found"}
        
        # Check if driver exists in registry
        if session_id not in frappe._persistent_gst_drivers:
            # Try to recover from another worker if possible
            return {"status": "error", "valid": False, "message": "Driver session not found in current process"}
        
        return {"status": "success", "valid": True}
    except Exception as e:
        return {"status": "error", "valid": False, "message": str(e)}

@frappe.whitelist()
def submit_gst_captcha(session_id, captcha_text):
    """Complete the GST login with the provided captcha"""
    try:
        # Check if session exists in Redis
        session_info = frappe.cache().get_value(f"gst_session:{session_id}")
        if not session_info:
            return {"status": "error", "message": "Session expired. Please try again."}
        
        # Check if we're in the same process
        current_pid = os.getpid()
        session_pid = session_info.get("pid")
        
        if current_pid != session_pid:
            frappe.log_error(
                f"PID mismatch: current={current_pid}, session={session_pid}", 
                "GST Session Error"
            )
            return {"status": "error", "message": "Session was created in a different process. Please try again with a new session."}
        
        # Check if driver exists in registry
        if session_id not in frappe._persistent_gst_drivers:
            frappe.log_error(
                f"Driver not found in registry for session {session_id}", 
                "GST Session Error"
            )
            return {"status": "error", "message": "Driver session lost. Please try again with a new session."}
        
        # Get driver and session details
        driver = frappe._persistent_gst_drivers[session_id]
        client_name = session_info["client_name"]
        username = session_info["username"]
        user_download_dir = session_info["download_dir"]
        
        # Complete the login
        try:
            if complete_login(driver, captcha_text):
                # Login successful, now process the client
                try:
                    # Continue with your existing process flow
                    if navigate_to_notices(driver):
                        # Extract notice data
                        notices_data = extract_notice_data(driver, user_download_dir, client_name)
                        if notices_data:
                            print(f"Processed notices data for {client_name}")
                            # Any additional processing here

                        add_notices_data = extract_gst_additional_notice_data(driver, user_download_dir)
                        if add_notices_data:
                            create_gst_additional_notice_table(client_name, add_notices_data)
                            
                    # Logout
                    logout_user(driver)
                    
                    # Update client document
                    doc = frappe.get_doc("GST Client", client_name)
                    doc.last_gst_sync = frappe.utils.now()
                    doc.save()
                    frappe.db.commit()
                    
                    return {"status": "success", "message": "Processing completed successfully"}
                except Exception as e:
                    error_msg = f"Error processing client {client_name} after login: {str(e)}"
                    frappe.log_error(error_msg, "GST Portal Processing Error")
                    return {"status": "error", "message": error_msg}
            else:
                return {"status": "error", "message": "Login failed. Invalid captcha or other login error."}
        except Exception as e:
            error_msg = f"Error in login completion: {str(e)}"
            frappe.log_error(error_msg, "GST Login Error")
            return {"status": "error", "message": error_msg}
        finally:
            # Always clean up resources
            try:
                if driver:
                    driver.quit()
            except Exception:
                pass  # Ignore errors during driver cleanup
                
            # Remove from registry and cache
            if session_id in frappe._persistent_gst_drivers:
                del frappe._persistent_gst_drivers[session_id]
                
            frappe.cache().delete_value(f"gst_session:{session_id}")
            
    except Exception as e:
        error_msg = f"Error submitting captcha: {str(e)}"
        frappe.log_error(error_msg, "GST Portal Captcha Error")
        return {"status": "error", "message": error_msg}