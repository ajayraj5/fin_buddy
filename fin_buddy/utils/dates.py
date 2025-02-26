import datetime

def get_frappe_date(date_string):
    """
    Converts different date formats to Frappe-compatible 'YYYY-MM-DD' format.
    Handles both 'DD-MMM-YYYY' (e.g., '08-Jun-2022') and 'DD/MM/YYYY' (e.g., '02/02/2024') formats.
    Returns None for invalid dates or special values like 'NA'.
    
    Args:
        date_string (str): Date string in various possible formats
        
    Returns:
        str or None: Date in 'YYYY-MM-DD' format for Frappe, or None if input is invalid
    """
    # Handle None, empty strings, or special values
    if not date_string or not isinstance(date_string, str):
        return None
        
    # Clean the input
    date_string = date_string.strip()
    
    # Handle special values
    if date_string.upper() in ('NA', 'N/A', 'NONE', '-', ''):
        return None
    
    # Try different date formats
    formats_to_try = [
        "%d-%b-%Y",  # 08-Jun-2022
        "%d/%m/%Y",  # 02/02/2024
        "%Y-%m-%d"   # Already in Frappe format (for validation)
    ]
    
    for date_format in formats_to_try:
        try:
            parsed_date = datetime.datetime.strptime(date_string, date_format)
            # Convert to Frappe's format (YYYY-MM-DD)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If we get here, none of the formats worked
    return None