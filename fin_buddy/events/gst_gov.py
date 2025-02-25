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


import frappe


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



def login_user(driver, username, password):
    """Login to GST portal"""
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

        # Click Login Button
        login_btn = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "button.btn-primary"))
        )
        # time.sleep(2)
        login_btn.send_keys(Keys.RETURN)

        # Wait for login to complete
        time.sleep(17)
        return True

    except Exception as e:
        print(f"Login failed for user {username}: {str(e)}")
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
        
        file_doc.insert()
        
        # Update the reply with the file URL
        child_notice_doc.file = file_doc.file_url
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


def extract_gst_additional_notice_data(driver):
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
            
            notices_data.append({
                'type_of_notice': notice_type,
                'description': description,
                'ref_id': ref_id,
                'date_of_issuance': date
            })
            
        # Convert to pandas DataFrame
        # df = pd.DataFrame(notices_data)
        
        # Save to CSV
        # df.to_csv('gst_notices.csv', index=False)
        
        # return df
        return notices_data
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    

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
        notices_data = extract_notice_data(driver, user_download_dir, client_name)
        if not notices_data:
            print("DONE for gst notices table")
            # Save to Excel
            # save_to_excel(notices_data, user_download_dir)
            # save_to_gst_client_document(notices_data, )
        else:
            print("No notice data extracted.")

        # Extract additional notice data
        add_notices_data = extract_gst_additional_notice_data(driver)
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
        doc = frappe.get_doc("Client", client_name)
        
        
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
        doc = frappe.get_doc("Client", client_name)
        
        
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
        doc = frappe.get_doc("Client", client_name)

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
        doc = frappe.get_doc("Client", client_name)
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


# def main():
#     try:
#         # Replace with actual credentials
#         username = "AADCH3199K1"
#         password = "Aarya@2025"
        
#         if not username or not password:
#             print("Missing credentials")
#             return
        
#         process_gst_notices(username, password)
        
#     except Exception as e:
#         print(f"Main execution error: {str(e)}")

# if __name__ == "__main__":
#     main()