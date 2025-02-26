
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






def process_financial_years_only_click(driver, tds_doc=None):
    """Process all financial years (except Prior Years) from the dashboard"""
    wait = WebDriverWait(driver, 20)
    all_notices_data = []
    
    try:
        # First, collect all the year texts we want to process
        financial_year_links = driver.find_elements(By.XPATH, "//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr']")
        years_to_process = [link.text for link in financial_year_links if "Prior Years" not in link.text]
        
        print("Years to process:", years_to_process)
        
        # Process each year by finding the element fresh each time
        for year_text in years_to_process:
            print("")
            print(f"Processing financial year: {year_text}")
            
            # Find the element again each time to avoid stale element issues
            year_element = driver.find_element(By.XPATH, f"//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr' and text()='{year_text}']")
            
            # Click on the year
            driver.execute_script("arguments[0].click();", year_element)
            time.sleep(3)
            
            # Process data for this year here
            # ... your processing code ...
            
            # Go back
            driver.back()
            time.sleep(10)  # Allow page to fully reload
        
        # Create TDS notices
        if all_notices_data:
            print("all notice data", all_notices_data)
            # create_tds_notices_table(tds_doc, all_notices_data)
        
    except Exception as e:
        print(f"Error processing financial years: {str(e)}")
        import traceback
        traceback.print_exc()  # This will print the full stack trace for better debugging


def process_quarters_old(driver, tds_doc, year_text):
    """
    Process all quarters for a specific financial year and return HTML tables
    
    Args:
        driver: Selenium WebDriver instance
        year_text: The financial year text (e.g., "2023-24")
    
    Returns:
        Dictionary with quarter information and HTML tables
    """
    wait = WebDriverWait(driver, 10)
    quarters_data = []
    new_doc = frappe.get_doc({
        "doctype":"TDS Summary Details",
        "fy": year_text,
        "tds_notice": tds_doc.name,
    })
    
    try:
        # Wait for the quarters table to be visible
        wait.until(EC.visibility_of_element_located((By.ID, "demandsumFY1")))
        
        # Find all quarter links in the first column
        quarter_links = driver.find_elements(By.XPATH, "//table[@id='demandsumFY1']/tbody/tr/td[1]/a")
        
        print(f"Found {len(quarter_links)} quarters for {year_text}")
        
        # Collect quarter texts for processing
        quarters_to_process = [link.find_element(By.XPATH, ".//span").text for link in quarter_links]
        
        # Process each quarter
        for quarter_text in quarters_to_process:
            print(f"  Processing quarter: {quarter_text}")
            
            # Find the quarter element fresh to avoid stale element issues
            quarter_element = driver.find_element(By.XPATH, f"//table[@id='demandsumFY1']/tbody/tr/td[1]/a/span[text()='{quarter_text}']/parent::a")
            
            # Click on the quarter
            driver.execute_script("arguments[0].click();", quarter_element)
            time.sleep(3)
            
            # Check if the table exists
            tables = driver.find_elements(By.XPATH, "//table[@class='userList w750']")
            
            if tables:
                # Get the HTML of the table
                table_html = tables[0].get_attribute('outerHTML')
                
                # Store the data
                quarter_data = {
                    'quarter': quarter_text,
                    'table_html': table_html
                }
                
                # quarters_data.append(quarter_data)
                new_doc.append("items",{
                    **quarter_data
                })
                print(f"    Captured table HTML for {year_text} - {quarter_text}")
            else:
                print(f"    No table found for {year_text} - {quarter_text}")
            
            # Go back to the year page
            driver.back()
            time.sleep(5)  # Allow page to fully reload
        
        return quarters_data
        
    except Exception as e:
        print(f"Error processing quarters for {year_text}: {str(e)}")
        import traceback
        traceback.print_exc()
        return quarters_data


def process_quarters_old_best(driver, tds_doc, year_text):
    """
    Process all quarters for a specific financial year and return data
    
    Args:
        driver: Selenium WebDriver instance
        year_text: The financial year text (e.g., "2023-24")
    
    Returns:
        Dictionary with quarter information, table HTML, and extracted data
    """
    wait = WebDriverWait(driver, 10)
    # quarters_data = []
    new_doc = frappe.get_doc({
        "doctype":"TDS Summary Details",
        "fy": year_text,
        "tds_notice": tds_doc.name,
    })
    
    try:
        # Wait for the quarters table to be visible
        wait.until(EC.visibility_of_element_located((By.ID, "demandsumFY1")))
        
        # Find all quarter links in the first column
        quarter_links = driver.find_elements(By.XPATH, "//table[@id='demandsumFY1']/tbody/tr/td[1]/a")
        
        print(f"Found {len(quarter_links)} quarters for {year_text}")
        
        # Process each quarter by getting row data first
        for i, quarter_link in enumerate(quarter_links):
            # Get the quarter text
            quarter_text = quarter_link.find_element(By.XPATH, ".//span").text
            print(f"  Processing quarter: {quarter_text}")
            
            # Get the form type and net payable from the same row
            # The form type is in the second column of the same row
            # row = quarter_link.find_element(By.XPATH, "./../../..")  # Go up to the TR element
            # form_type = row.find_element(By.XPATH, "./td[2]/span").text
            # net_payable = row.find_element(By.XPATH, "./td[3]/span").text
            
            # print(f"    Form Type: {form_type}, Net Payable: {net_payable}")
            
            # Find the quarter element fresh to avoid stale element issues
            quarter_element = driver.find_element(By.XPATH, f"//table[@id='demandsumFY1']/tbody/tr/td[1]/a/span[text()='{quarter_text}']/parent::a")
            
            # Click on the quarter
            driver.execute_script("arguments[0].click();", quarter_element)
            time.sleep(3)
            
            # Check if the table exists
            tables = driver.find_elements(By.XPATH, "//table[@class='userList w750']")
            
            if tables:
                # Get the HTML of the table
                table_html = tables[0].get_attribute('outerHTML')
                
                # Store the data
                quarter_data = {
                    'quarter': quarter_text,
                    'form_type': "",
                    'net_payable': "",
                    'table_html': table_html
                }
                new_doc.append("items",{
                    **quarter_data
                })
                
                # quarters_data.append(quarter_data)
                print(f"    Captured table HTML for {year_text} - {quarter_text}")
            else:
                # Still save the form type and net payable even if table isn't found
                quarter_data = {
                    'quarter': quarter_text,
                    'form_type': "",
                    'net_payable': "",
                    'table_html': None
                }
                new_doc.append("items",{
                    **quarter_data
                })
                
                # quarters_data.append(quarter_data)
                print(f"    No table found for {year_text} - {quarter_text}")
            
            # Go back to the year page
            driver.back()
            time.sleep(5)  # Allow page to fully reload
        

        doc = new_doc.insert()
        frappe.db.commit()

        return doc
        
    except Exception as e:
        print(f"Error processing quarters for {year_text}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None





def process_quarters_without_some_fields(driver, tds_doc, year_text):
    """
    Process all quarters for a specific financial year and return data
    """
    wait = WebDriverWait(driver, 10)
    new_doc = frappe.get_doc({
        "doctype":"TDS Summary Details",
        "fy": year_text,
        "tds_notice": tds_doc.name,
    })
    
    try:
        # Wait for the quarters table to be visible
        wait.until(EC.visibility_of_element_located((By.ID, "demandsumFY1")))
        
        # Get the count of quarters first
        quarter_links = driver.find_elements(By.XPATH, "//table[@id='demandsumFY1']/tbody/tr/td[1]/a")
        quarter_count = len(quarter_links)
        
        print(f"Found {quarter_count} quarters for {year_text}")
        
        # Process each quarter by index rather than keeping references to elements
        for i in range(quarter_count):
            # Find quarter links fresh each time to avoid stale elements
            fresh_quarter_links = driver.find_elements(By.XPATH, "//table[@id='demandsumFY1']/tbody/tr/td[1]/a")
            current_quarter = fresh_quarter_links[i]
            
            # Get the quarter text
            quarter_text = current_quarter.find_element(By.XPATH, ".//span").text
            print(f"  Processing quarter: {quarter_text}")
            
            # Click on the quarter
            driver.execute_script("arguments[0].click();", current_quarter)
            time.sleep(3)
            
            # Check if the table exists
            tables = driver.find_elements(By.XPATH, "//table[@class='userList w750']")
            
            if tables:
                # Get the HTML of the table
                table_html = tables[0].get_attribute('outerHTML')
                
                print(table_html)

                # Store the data
                quarter_data = {
                    'quarter': quarter_text,
                    'form_type': "",
                    'net_payable': "",
                    'table_html': table_html
                }
                new_doc.append("items", quarter_data)
                
                print(f"    Captured table HTML for {year_text} - {quarter_text}")
            else:
                quarter_data = {
                    'quarter': quarter_text,
                    'form_type': "",
                    'net_payable': "",
                    'table_html': None
                }
                new_doc.append("items", quarter_data)
                
                print(f"    No table found for {year_text} - {quarter_text}")
            
            # Go back to the year page
            driver.back()
            time.sleep(5)  # Allow page to fully reload
        
        doc = new_doc.insert()
        frappe.db.commit()
        return doc
        
    except Exception as e:
        print(f"Error processing quarters for {year_text}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None
    


def process_quarters(driver, tds_doc, year_text):
    """
    Process all quarters for a specific financial year and return data
    """
    wait = WebDriverWait(driver, 10)
    new_doc = frappe.get_doc({
        "doctype": "TDS Summary Details",
        "fy": year_text,
        "tds_notice": tds_doc.name,
    })
    
    try:
        # Wait for the quarters table to be visible
        wait.until(EC.visibility_of_element_located((By.ID, "demandsumFY1")))
        
        # Process the initial table to get quarter, form type, and net payable data
        quarters_table = driver.find_element(By.ID, "demandsumFY1")
        table_rows = quarters_table.find_elements(By.XPATH, ".//tr[contains(@class, 'odd') or contains(@class, 'even')]")
        
        print(f"Found {len(table_rows)} quarters for {year_text}")
        
        # Store the quarter links separately to avoid stale elements
        quarter_links = []
        quarters_data = []
        
        for row in table_rows:
            try:
                # Get all cells from the row
                cells = row.find_elements(By.TAG_NAME, "td")
                
                if len(cells) >= 3:
                    # Extract quarter link element
                    quarter_link = cells[0].find_element(By.TAG_NAME, "a")
                    quarter_links.append(quarter_link)
                    
                    # Extract quarter text, form type, and net payable
                    quarter_text = cells[0].find_element(By.XPATH, ".//span").text
                    form_type = cells[1].find_element(By.XPATH, ".//span").text
                    net_payable = cells[2].find_element(By.XPATH, ".//span").text
                    
                    # Store this initial data
                    quarters_data.append({
                        'quarter': quarter_text,
                        'form_type': form_type,
                        'net_payable': net_payable
                    })
                    
                    print(f"  Found quarter: {quarter_text}, form type: {form_type}, net payable: {net_payable}")
            except Exception as e:
                print(f"Error processing table row: {str(e)}")
        
        # Now process each quarter by clicking on them
        for i, data in enumerate(quarters_data):
            try:
                # Find quarter links fresh each time to avoid stale elements
                fresh_quarter_links = driver.find_elements(By.XPATH, "//table[@id='demandsumFY1']/tbody/tr/td[1]/a")
                if i < len(fresh_quarter_links):
                    current_quarter = fresh_quarter_links[i]
                    quarter_text = data['quarter']
                    
                    print(f"  Processing quarter details: {quarter_text}")
                    
                    # Click on the quarter
                    driver.execute_script("arguments[0].click();", current_quarter)
                    time.sleep(3)
                    
                    # Check if the table exists
                    tables = driver.find_elements(By.XPATH, "//table[@class='userList w750']")
                    
                    table_html = None
                    if tables:
                        # Get the HTML of the table
                        table_html = tables[0].get_attribute('outerHTML')
                        print(f"    Captured table HTML for {year_text} - {quarter_text}")
                    else:
                        print(f"    No table found for {year_text} - {quarter_text}")
                    
                    # Store the data with form type and net payable from the initial scan
                    quarter_data = {
                        'quarter': quarter_text,
                        'form_type': data['form_type'],
                        'net_payable': data['net_payable'],
                        'table_html': table_html
                    }
                    new_doc.append("items", quarter_data)
                    
                    # Go back to the year page
                    driver.back()
                    time.sleep(5)  # Allow page to fully reload
            except Exception as e:
                print(f"Error processing quarter {data['quarter']}: {str(e)}")
        
        doc = new_doc.insert()
        frappe.db.commit()
        return doc
        
    except Exception as e:
        print(f"Error processing quarters for {year_text}: {str(e)}")
        import traceback
        traceback.print_exc()
        return None



def process_financial_years_old(driver, tds_doc, table_data):
    """Process all financial years (except Prior Years) from the dashboard"""
    wait = WebDriverWait(driver, 20)
    # all_quarters_data = []

    tds_doc.notice = []
    try:
        # First, collect all the year texts we want to process
        financial_year_links = driver.find_elements(By.XPATH, "//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr']")
        years_to_process = [link.text for link in financial_year_links if "Prior Years" not in link.text]
        
        print("Years to process:", years_to_process)
        
        # Process each year by finding the element fresh each time
        for year_text in years_to_process:
            print("")
            print(f"Processing financial year: {year_text}")
            
            # Find the element again each time to avoid stale element issues
            year_element = driver.find_element(By.XPATH, f"//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr' and text()='{year_text}']")
            
            # Click on the year
            driver.execute_script("arguments[0].click();", year_element)
            time.sleep(3)
            
            # Process all quarters for this year
            # quarters_doc = process_quarters(driver, tds_doc, year_text)

            # print("quarters_doc", quarters_doc)
            # print("quarters_doc name", quarters_doc.name)
            # all_quarters_data.extend(quarters_data)
            # table_data[year_text]['tds_summary_details'] = quarters_doc

            # tds_doc.append("notices", {
            #     **table_data[year_text]
            # })

            quarters_doc = process_quarters(driver, tds_doc, year_text)

            if quarters_doc:
                print("quarters_doc", quarters_doc)
                print("quarters_doc name", quarters_doc.name)
                table_data[year_text]['tds_summary_details'] = quarters_doc
                
                tds_doc.append("notices", {
                    **table_data[year_text]
                })
            else:
                print(f"Failed to process quarters for {year_text}")
                        
            # Go back
            driver.back()
            time.sleep(10)  # Allow page to fully reload

        tds_doc.save()
        frappe.db.commit()
        
        return True
        
    except Exception as e:
        print(f"Error processing financial years: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def process_financial_years(driver, tds_doc, table_data):
    """Process all financial years (except Prior Years) from the dashboard"""
    wait = WebDriverWait(driver, 20)
    
    try:
        # First, collect all the year texts we want to process
        financial_year_links = driver.find_elements(By.XPATH, "//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr']")
        years_to_process = [link.text for link in financial_year_links if "Prior Years" not in link.text]
        
        print("Years to process:", years_to_process)
        
        # Process each year by finding the element fresh each time
        for year_text in years_to_process:
            print("")
            print(f"Processing financial year: {year_text}")
            
            # Find the element again each time to avoid stale element issues
            year_element = driver.find_element(By.XPATH, f"//table[@id='fyAmtList']/tbody/tr/td[@aria-describedby='fyAmtList_finYr' and text()='{year_text}']")
            
            # Click on the year
            driver.execute_script("arguments[0].click();", year_element)
            time.sleep(3)
            
            # Process all quarters for this year and get the quarters document
            quarters_doc = process_quarters(driver, tds_doc, year_text)
            
            if quarters_doc:
                print(f"Successfully processed quarters for {year_text}, doc name: {quarters_doc.name}")
                
                # Create a copy of the year's data
                year_data = table_data.get(year_text, {}).copy()
                
                # Set the quarters document link for this specific year
                year_data['tds_summary_details'] = quarters_doc.name
                
                # Append this year's data to the notices child table
                tds_doc.append("notices", year_data)
                
                # Save immediately to persist this link
                frappe.db.commit()
            else:
                print(f"Failed to process quarters for {year_text}")
            
            # Go back
            driver.back()
            time.sleep(10)  # Allow page to fully reload
        
        # Save the main document with all years processed
        tds_doc.save()
        frappe.db.commit()
        
        return True
        
    except Exception as e:
        print(f"Error processing financial years: {str(e)}")
        import traceback
        traceback.print_exc()
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

        process_financial_years(driver, tds_doc, table_data)
        # create_tds_notices_table(tds_doc, table_data)
        
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
        
        # Initialize dict to store data
        data = {}
        
        # Extract rows
        rows = soup.find_all('tr', class_='ui-widget-content jqgrow ui-row-ltr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) >= 3:
                financial_year = cells[0].get('title', '')
                manual_demand = float(cells[1].get('title', '0.00'))
                processed_demand = float(cells[2].get('title', '0.00'))
                
                data[financial_year] = {
                    'financial_year':financial_year,
                    'manual_demand': manual_demand,
                    'processed_demand': processed_demand
                }
        
        return data
        
    except Exception as e:
        print(f"Error extracting table data: {str(e)}")
        return {}

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