
import time
from datetime import datetime
from bs4 import BeautifulSoup
import os
import re
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException


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

def login_user(driver, username, password):
    """Login to TDS portal"""
    try:
        wait = WebDriverWait(driver, 20)
        driver.get("https://www.tdscpc.gov.in/app/login.xhtml")
        time.sleep(1)

        # Enter Username
        username_field = wait.until(
            EC.visibility_of_element_located((By.ID, "userId"))
        )
        username_field.clear()
        username_field.send_keys(username)

        # Enter Password
        password_field = wait.until(
            EC.visibility_of_element_located((By.ID, "psw"))
        )
        password_field.clear()
        password_field.send_keys(password)

        # Enter TAN
        tan_field = wait.until(
            EC.visibility_of_element_located((By.ID, "tanpan"))
        )
        tan_field.clear()
        tan_field.send_keys(username)

        # Click Login Button
        login_btn = wait.until(
            EC.visibility_of_element_located((By.ID, "clickLogin"))
        )
        time.sleep(2)
        login_btn.send_keys(Keys.RETURN)

        # Wait for login to complete
        time.sleep(17)
        return True

    except Exception as e:
        print(f"Login failed for user {username}: {str(e)}")
        return False

def navigate_to_dashboard(driver, client_name):
    """Navigate to dashboard and extract demand data"""
    try:
        wait = WebDriverWait(driver, 20)
        
        # Click on Dashboard link
        dashboard_link = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/app/ded/dashboard.xhtml')]"))
        )
        dashboard_link.click()
        time.sleep(5)
        
        # Scroll to bottom of page
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        
        # Click on the outstanding demand link
        demand_link = wait.until(
            EC.element_to_be_clickable((By.ID, "allyear"))
        )
        demand_link.click()
        time.sleep(5)
        
        # Extract table data
        table_data = extract_demand_table(driver)

        tds_doc = get_or_create_tds_client_document(client_name)
        if not tds_doc:
            print(f"Error in get_or_create_tds_client_document document creation.")
            return False

        create_tds_notices_table(tds_doc, table_data)
        
        # Save to Excel
        # save_to_excel(table_data, user_download_dir)
        
        return True
        
    except Exception as e:
        print(f"Error navigating dashboard: {str(e)}")
        return False
    


def get_or_create_tds_client_document(client_name):
    """Get existing TDS Notice or create new one."""
    existing_records = frappe.get_all(
        "TDS Notice",
        filters={'client': client_name},
        fields=["name"]
    )
    
    if existing_records:
        return frappe.get_doc("TDS Notice", existing_records[0]['name'])
        
    # Create new record
    try:
        new_doc = frappe.get_doc({
            "doctype": "TDS Notice",
            "client": client_name
        })
        new_doc.insert()
        frappe.db.commit()
        return new_doc
    except Exception as e:
        frappe.log_error(f"Failed to create TDS Notice: {str(e)}")
        return None



def create_tds_notices_table(tds_doc, notices_data):
    """Create TDS Notice Item."""
    try:

        # tds_doc = get_or_create_tds_client_document(client_name)
        if not tds_doc:
            return False, "Failed to get or create TDS Notice document"


        tds_doc.notices = []
        
        # First, create a new TDS Additional Notice Reply
        for notice_data in notices_data:
            # child_notice_doc = frappe.get_doc({
            #     "doctype": "TDS Notice Item",
            #     "parent": tds_doc.name,
            #     "parenttype": "TDS Notice",
            #     "parentfield": "notices",
            #     **notice_data
            # })
            tds_doc.append("notices",{
                **notice_data
            })
            # child_notice_doc.insert()
            # frappe.db.commit()
        
        tds_doc.save()
        frappe.db.commit()
        

        return True, f"Successfully created all TDS Notice for {tds_doc.name}"
        
    except Exception as e:
        frappe.db.rollback()
        return False, f"Failed to create TDS Notice Item: {str(e)}"



def extract_demand_table(driver):
    """Extract data from the demand table"""
    try:
        wait = WebDriverWait(driver, 20)
        
        # Wait for table to be visible
        table = wait.until(
            EC.presence_of_element_located((By.ID, "fyAmtList"))
        )
        
        # Get table HTML
        table_html = table.get_attribute('outerHTML')
        soup = BeautifulSoup(table_html, 'html.parser')
        
        # Initialize lists to store data
        data = []
        
        # Extract rows
        rows = soup.find_all('tr', class_='ui-widget-content jqgrow ui-row-ltr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                financial_year = cells[0].get('title', '')
                manual_demand = float(cells[1].get('title', '0.00'))
                processed_demand = float(cells[2].get('title', '0.00'))
                
                data.append({
                    'financial_year': financial_year,
                    'manual_demand': manual_demand,
                    'processed_demand': processed_demand
                })
        
        return data
        
    except Exception as e:
        print(f"Error extracting table data: {str(e)}")
        return []

# def save_to_excel(data, filename='demand_data.xlsx'):
#     """Save the extracted data to Excel"""
#     try:
#         df = pd.DataFrame(data)
#         df.to_excel(filename, index=False)
#         print(f"Data saved to {filename}")
#     except Exception as e:
#         print(f"Error saving to Excel: {str(e)}")


def save_to_excel(data, user_download_dir):
    """Save extracted data to Excel file"""
    if data:
        try:
            df = pd.DataFrame(data)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            excel_path = os.path.join(user_download_dir, f"tds_data_{timestamp}.xlsx")
            df.to_excel(excel_path, index=False)
            print(f"Data saved to {excel_path}")
            return True
        except Exception as e:
            print(f"Failed to save Excel file: {str(e)}")
            return False
    return False


def process_tds(client_name, username, password):
    """Main function to process TDS data"""
    driver = None
    try:
        # Setup driver and get download directory
        driver, user_download_dir = setup_driver(username, "tds")
        
        # Login
        if not login_user(driver, username, password):
            print("Login failed. Cannot proceed.")
            return
        
        # Navigate to dashboard and extract data
        if not navigate_to_dashboard(driver, client_name):
            print("Failed to extract demand data")
            return
        
        print("Process completed successfully")
        
    except Exception as e:
        print(f"Error during execution: {str(e)}")
    finally:
        if driver:
            logout_user(driver)
            driver.quit()







def logout_user(driver):
    try:
        print("logout .......")
        driver.execute_script("document.body.scrollTop = 0; document.documentElement.scrollTop = 0;")

        # Allow time for scrolling
        time.sleep(1)

        logout_link = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((
            By.XPATH,
            "//li[@class='last_menu']/a[@title='Logout']"
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
                'fin_buddy.events.tds_gov.process_single_client',
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
        username = doc.tds_username
        password = doc.get_password("tds_password")
        
        if not username or not password:
            frappe.log_error(
                f"Missing credentials for client {client_name}",
                "TDS Portal Sync Error"
            )
            frappe.throw(f"Missing credentials for client {client_name}")
            return
        
        # Setup Selenium and process
        # driver = setup_driver(username, "tds")
        
        start_time = time.time()
        
        try:    
                # setup of driver, login and processing and logout
                process_tds(client_name, username, password)
                
        except Exception as e:
            error_msg = f"Error processing client {client_name}: {str(e)}"
            frappe.log_error(error_msg, "TDS Portal Processing Error")
        finally:
            # Calculate processing time
            doc.last_tds_sync = datetime.now()
            
            # Save the document
            doc.save()
            frappe.db.commit()


                
    except Exception as e:
        error_msg = f"An error occurred in process_single_client for {client_name}: {str(e)}"
        frappe.log_error(error_msg, "TDS Portal Sync Error")





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
                'fin_buddy.events.tds_gov.login',
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
        username = doc.tds_username
        password = doc.get_password("tds_password")
        
        if not username or not password:
            frappe.log_error(
                f"Missing credentials for client {client_name}",
                "TDS Portal Sync Error"
            )
            return
        
        # Setup Selenium and process
        driver, user_download_dir = setup_driver(username, "tds")
                
        try:
            login_user(driver, username, password)
        except Exception as e:
            frappe.log_error("Login User Failed", str(e))
    
    except Exception as e:
        frappe.log_error("Login Error In Client", str(e))



# def main():
#     try:
#         # Replace with actual credentials
#         username = "RTKH04289F1"
#         password = "ABCD1234"
        
#         if not username or not password:
#             print("Missing credentials")
#             return
        
#         process_tds(username, password)
        
#     except Exception as e:
#         print(f"Main execution error: {str(e)}")

# if __name__ == "__main__":
#     main()