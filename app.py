"""
operator Signup App - Streamlit Tablet Interface
Replaces physical clipboards with a digital signup system
Date: December 31, 2025
"""

import streamlit as st
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List
from zoneinfo import ZoneInfo
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# Timezone configuration - all times in Eastern
EASTERN = ZoneInfo("America/New_York")

def now_eastern():
    """Get current time in Eastern timezone"""
    return datetime.now(EASTERN)

# App configuration
st.set_page_config(
    page_title="Operator Signup System",
    page_icon="🚌",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for tablet-friendly interface
st.markdown("""
<style>
    .main-header {
        text-align: center;
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f4e79;
        margin-bottom: 1rem;
    }
    
    /* Default button styling */
    .stButton > button {
        font-size: 1.2rem !important;
        font-weight: bold !important;
        padding: 15px 25px !important;
        min-height: 60px !important;
        border-radius: 8px !important;
        border: 2px solid #e0e0e0 !important;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
        transition: all 0.3s ease !important;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%) !important;
        white-space: normal !important;
        word-wrap: break-word !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
        border-color: #007bff !important;
    }
    
    /* Keep form submit buttons styled */
    div[data-testid="stForm"] .stButton > button {
        font-size: 1.4rem !important;
        padding: 20px 30px !important;
        min-height: 80px !important;
        border-radius: 10px !important;
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
        color: white !important;
        border-color: #28a745 !important;
    }
    
    /* Larger input fields for tablets */
    .stTextInput > div > div > input {
        font-size: 1.2rem;
        padding: 15px;
    }
    
    .stSelectbox > div > div > div {
        font-size: 1.2rem;
    }
    
    /* Desktop/Tablet: large buttons */
    @media screen and (min-width: 769px) {
        .stButton > button {
            font-size: 1.4rem !important;
            padding: 20px 20px !important;
            min-height: 80px !important;
            border-radius: 12px !important;
        }
        
        div[data-testid="stForm"] .stButton > button {
            font-size: 1.4rem !important;
            padding: 20px 30px !important;
            min-height: 80px !important;
        }
    }
    
    /* Mobile portrait: compact buttons */
    @media screen and (max-width: 768px) {
        .main-header {
            font-size: 1.6rem !important;
        }
        
        .stButton > button {
            font-size: 1rem !important;
            padding: 10px 10px !important;
            min-height: 44px !important;
            min-width: unset !important;
            border-radius: 8px !important;
        }
        
        div[data-testid="stForm"] .stButton > button {
            font-size: 1.1rem !important;
            padding: 12px 15px !important;
            min-height: 50px !important;
        }
        
        .stTextInput > div > div > input {
            font-size: 1rem !important;
            padding: 10px !important;
        }
        
        .stSelectbox > div > div > div {
            font-size: 1rem !important;
        }
        
        /* Stack columns vertically on mobile */
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
            gap: 0.5rem !important;
        }
        
        [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            flex: 1 1 100% !important;
            min-width: 100% !important;
        }
        
        /* Normalize all vertical spacing to match */
        [data-testid="stVerticalBlock"] {
            gap: 0.5rem !important;
        }
    }
</style>""", unsafe_allow_html=True)

# Data file paths
DATA_DIR = "signup_data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)


# Google Sheets Configuration
GOOGLE_SHEETS_ENABLED = True
MAIN_SHEET_ID = "1HP6B7FAIquGi8yTjb35L2Er9fxt13Prw9dIAmXAnvkE"  # Main database sheet
CREDENTIALS_FILE = "service_account_credentials.json"  # Your service account file
DAILY_SHEETS_ENABLED = True  # Re-enabled for testing with manually created sheets
SCHEDULER_FOLDER_ID = "1dYd5Lk0O2x8-huNXfslRHpjWVEMu3L2q"  # Scheduler sheets folder

# Operators Sheet Configuration
OPERATORS_SHEET_ID = "1shAyat8-g_CAF22I6shcVnSxHz3OQxMtcfZ7EmjlNWE"
OPERATORS_SHEET_TAB = 0  # Use first worksheet/tab

@st.cache_data(show_spinner=False)
def get_operators_data():
    """Fetch operator data from Operators Google Sheet, only Active employees."""
    try:
        client = setup_google_sheets()
        if not client:
            return [], {}, {}
        sheet = client.open_by_key(OPERATORS_SHEET_ID)
        worksheet = sheet.get_worksheet(OPERATORS_SHEET_TAB)
        records = worksheet.get_all_records()
        # Build display list, lookup dict, and reverse lookup
        display_list = []
        id_lookup = {}
        display_to_id = {}
        for row in records:
            op_id = str(row.get("ID #", "")).strip()
            status = str(row.get("Employee Status", "")).strip().lower()
            first = str(row.get("First Name", "")).strip()
            last = str(row.get("Last Name", "")).strip()
            if op_id and status == "active":
                display = f"{op_id} - {first} {last}"
                display_list.append(display)
                id_lookup[op_id] = row
                display_to_id[display] = op_id
        return display_list, id_lookup, display_to_id
    except Exception as e:
        print(f"Error loading operators sheet: {e}")
        return [], {}, {}

def setup_google_sheets():
    """Setup Google Sheets connection - supports local file or Streamlit Cloud Secrets"""
    try:
        # Define the scope
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        
        # Option 1: Load from local credentials file (for local development)
        if os.path.exists(CREDENTIALS_FILE):
            credentials = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=scope)
        # Option 2: Load from Streamlit Secrets (for Streamlit Cloud deployment)
        elif hasattr(st, 'secrets') and "gcp_service_account" in st.secrets:
            from google.oauth2.service_account import Credentials as ServiceCredentials
            credentials = ServiceCredentials.from_service_account_info(
                st.secrets["gcp_service_account"], scopes=scope
            )
        else:
            print("No Google Sheets credentials found. Skipping Google Sheets integration.")
            return None
        
        # Authorize and get the client
        client = gspread.authorize(credentials)
        
        return client
    except Exception as e:
        print(f"Error setting up Google Sheets: {e}")
        return None

def save_to_main_sheet(clipboard_type: str, date: str, operator_name: str, additional_info: Dict = None):
    """Save signup data to main Google Sheet"""
    if not GOOGLE_SHEETS_ENABLED:
        return
    
    try:
        client = setup_google_sheets()
        if not client:
            return
        
        # Open the main sheet
        main_sheet = client.open_by_key(MAIN_SHEET_ID)
        
        # Use a single "All Signups" worksheet for the main database
        try:
            worksheet = main_sheet.worksheet("All Signups")
        except gspread.WorksheetNotFound:
            worksheet = main_sheet.add_worksheet(title="All Signups", rows=5000, cols=10)
            # Add headers
            headers = ["Date Requested", "Clipboard Type", "Operator Name", "Operator ID", "Shift Time Requested", "Work Requested", "Phone #", "Signup Time", "Notes"]
            worksheet.append_row(headers)
        
        # Convert clipboard type to display format for Google Sheets
        clipboard_display_map = {
            "SPARE_WORK": "SPARE",
            "EXTRA_WORK": "EXTRA", 
            "RDO": "RDO"
        }
        display_clipboard_type = clipboard_display_map.get(clipboard_type, clipboard_type)
        
        # Prepare row data for main sheet
        signup_time = now_eastern().strftime("%Y-%m-%d %H:%M:%S")
        additional_info = additional_info or {}
        
        row_data = [
            date,
            display_clipboard_type,
            operator_name,
            additional_info.get("operator_id", ""),
            additional_info.get("shift_time", ""),
            additional_info.get("work_choice", additional_info.get("work_interested", "")),
            additional_info.get("phone_number", ""),
            signup_time,
            additional_info.get("notes", "")
        ]
        
        # Append to main sheet
        worksheet.append_row(row_data)
        print(f"Successfully saved to Main Sheet: {clipboard_type} - {operator_name} - {date}")
        
    except Exception as e:
        print(f"Error saving to Main Sheet: {e}")

def check_and_create_daily_sheet(target_date: str):
    """Check if daily sheet exists for date in scheduler folder, create if it doesn't"""
    if not GOOGLE_SHEETS_ENABLED or not DAILY_SHEETS_ENABLED:
        return None
        
    try:
        client = setup_google_sheets()
        if not client:
            return None
            
        # Format date for sheet title to match your naming convention (YYYY-MM-DD)
        daily_sheet_title = target_date  # Use the date directly (e.g., "2026-01-29")
        
        # Check if sheet already exists by trying to open it
        try:
            existing_sheet = client.open(daily_sheet_title)
            print(f"Daily sheet already exists: {daily_sheet_title}")
            return existing_sheet.id
        except gspread.SpreadsheetNotFound:
            # Sheet doesn't exist, create it
            print(f"Creating new daily sheet: {daily_sheet_title}")
            pass
        
        # Since you manually created the sheet, we'll skip the creation part and just try to open it
        # Create new sheet directly in the scheduler folder (avoids service account storage quota)
        # daily_sheet = client.create(daily_sheet_title, folder_id=SCHEDULER_FOLDER_ID)
        print(f"Skipping sheet creation - using manually created sheet: {daily_sheet_title}")
        
        # Try to open the manually created sheet
        try:
            daily_sheet = client.open(daily_sheet_title)
            print(f"Successfully opened manually created sheet: {daily_sheet_title}")
        except gspread.SpreadsheetNotFound:
            print(f"Could not find manually created sheet: {daily_sheet_title}")
            return None
        
        print(f"Created daily sheet in scheduler folder: {daily_sheet_title}")
        print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{daily_sheet.id}")
        
        # Check if worksheets already exist, create them if they don't
        existing_worksheets = [ws.title for ws in daily_sheet.worksheets()]
        print(f"Existing worksheets: {existing_worksheets}")
        
        # Create three worksheets with headers (if they don't exist)
        clipboard_types = {
            "SPARE": "Spare Work",
            "EXTRA": "Extra Work", 
            "RDO": "RDO"
        }
        
        for clipboard_key, tab_name in clipboard_types.items():
            if tab_name not in existing_worksheets:
                # Create worksheet
                if len(existing_worksheets) == 0:
                    # Use the default first sheet if no worksheets exist
                    worksheet = daily_sheet.sheet1
                    worksheet.update_title(tab_name)
                else:
                    worksheet = daily_sheet.add_worksheet(title=tab_name, rows=100, cols=10)
                
                # Add headers matching main sheet structure
                headers = ["Date Requested", "Operator Name", "Operator ID", "Shift Time Requested", "Work Requested", "Phone #", "Signup Time", "Notes"]
                worksheet.append_row(headers)
                print(f"Created new worksheet: {tab_name}")
            else:
                print(f"Worksheet already exists: {tab_name}")
        
        return daily_sheet.id
        
    except Exception as e:
        print(f"Error checking/creating daily sheet: {e}")
        return None

def add_to_daily_sheet(target_date: str, clipboard_type: str, operator_name: str, additional_info: Dict = None):
    """Add signup to the appropriate daily sheet tab"""
    if not GOOGLE_SHEETS_ENABLED or not DAILY_SHEETS_ENABLED:
        return
        
    try:
        # Ensure daily sheet exists
        daily_sheet_id = check_and_create_daily_sheet(target_date)
        if not daily_sheet_id:
            return
            
        client = setup_google_sheets()
        if not client:
            return
            
        # Open the daily sheet
        daily_sheet = client.open_by_key(daily_sheet_id)
        
        # Map clipboard types to tab names
        clipboard_display_map = {
            "SPARE_WORK": "Spare Work",
            "EXTRA_WORK": "Extra Work", 
            "RDO": "RDO"
        }
        
        tab_name = clipboard_display_map.get(clipboard_type, clipboard_type)
        worksheet = daily_sheet.worksheet(tab_name)
        
        # Prepare row data for daily sheet (excluding clipboard type since it's separated by tabs)
        signup_time = now_eastern().strftime("%Y-%m-%d %H:%M:%S")
        additional_info = additional_info or {}
        
        row_data = [
            target_date,
            operator_name,
            additional_info.get("operator_id", ""),
            additional_info.get("shift_time", ""),
            additional_info.get("work_choice", additional_info.get("work_interested", "")),
            additional_info.get("phone_number", ""),
            signup_time,
            additional_info.get("notes", "")
        ]
        
        # Append to daily sheet
        worksheet.append_row(row_data)
        print(f"Successfully added to daily sheet {tab_name}: {operator_name}")
        
    except Exception as e:
        print(f"Error adding to daily sheet: {e}")

def create_daily_sheet(target_date: str):
    """Create a new daily sheet with 3 tabs for a specific date"""
    if not GOOGLE_SHEETS_ENABLED:
        print("Google Sheets not enabled. Cannot create daily sheet.")
        return None
    
    try:
        client = setup_google_sheets()
        if not client:
            return None
        
        # Open main sheet to get data
        main_sheet = client.open_by_key(MAIN_SHEET_ID)
        all_signups_worksheet = main_sheet.worksheet("All Signups")
        
        # Get all records and filter for target date
        all_records = all_signups_worksheet.get_all_records()
        target_records = [record for record in all_records if record['Date'] == target_date]
        
        if not target_records:
            print(f"No signups found for {target_date}")
            return None
        
        # Create new sheet for the day
        date_formatted = datetime.strptime(target_date, "%Y-%m-%d").strftime("%m-%d-%Y")
        daily_sheet_title = f"Daily Signups {date_formatted}"
        
        # Create the new spreadsheet
        daily_sheet = client.create(daily_sheet_title)
        
        # Share with the same permissions as main sheet (you'll need to do this manually or add logic)
        print(f"Created daily sheet: {daily_sheet_title}")
        print(f"Sheet URL: https://docs.google.com/spreadsheets/d/{daily_sheet.id}")
        
        # Create three worksheets and populate them
        clipboard_types = {
            "SPARE_WORK": "Spare Work",
            "EXTRA_WORK": "Extra Work", 
            "RDO": "RDO"
        }
        
        for clipboard_key, tab_name in clipboard_types.items():
            # Filter records for this clipboard type
            clipboard_records = [r for r in target_records if r['Clipboard Type'] == clipboard_key]
            
            if clipboard_records:
                # Create worksheet
                if tab_name == "Spare Work":
                    worksheet = daily_sheet.sheet1  # Use the default first sheet
                    worksheet.update_title(tab_name)
                else:
                    worksheet = daily_sheet.add_worksheet(title=tab_name, rows=100, cols=10)
                
                # Add headers
                headers = ["operator Name", "operator ID", "Shift Time", "Work Interest", "Notes", "Signup Time"]
                worksheet.append_row(headers)
                
                # Add data rows
                for record in clipboard_records:
                    row_data = [
                        record['operator Name'],
                        record['operator ID'],
                        record['Shift Time'], 
                        record['Work Choice/Interest'],
                        record['Notes'],
                        record['Signup Time']
                    ]
                    worksheet.append_row(row_data)
                    
                print(f"Added {len(clipboard_records)} {tab_name} signups to daily sheet")
        
        return daily_sheet.id
        
    except Exception as e:
        print(f"Error creating daily sheet: {e}")
        return None

def get_signup_file(clipboard_type: str, date: str) -> str:
    """Get the file path for storing signup data"""
    return os.path.join(DATA_DIR, f"{clipboard_type}_{date}.json")

def load_signups(clipboard_type: str, date: str) -> List[Dict]:
    """Load existing signups for a specific clipboard and date"""
    file_path = get_signup_file(clipboard_type, date)
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            return json.load(f)
    return []

def save_signup(clipboard_type: str, date: str, operator_name: str, additional_info: Dict = None):
    """Save a new signup to local JSON, Main Google Sheet, and Daily Sheet"""
    # Save to local JSON file (existing functionality)
    signups = load_signups(clipboard_type, date)
    
    new_signup = {
        "operator_name": operator_name,
        "signup_time": now_eastern().isoformat(),
        "additional_info": additional_info or {}
    }
    
    signups.append(new_signup)
    
    file_path = get_signup_file(clipboard_type, date)
    with open(file_path, 'w') as f:
        json.dump(signups, f, indent=2)
    
    # Save to Main Google Sheet
    save_to_main_sheet(clipboard_type, date, operator_name, additional_info)
    
    # Save to Daily Sheet (creates sheet if it doesn't exist)
    add_to_daily_sheet(date, clipboard_type, operator_name, additional_info)

def get_work_dates(days: int = 31) -> List[str]:
    """Get available work dates from tomorrow (if before 11am) or day after tomorrow (if after 11am)"""
    dates = []
    now = now_eastern()
    today = now.date()
    
    # Before 11:00 AM: can sign up for tomorrow
    # After 11:00 AM: can only sign up starting day after tomorrow
    if now.hour < 11:
        start_day = 1  # Start from tomorrow
    else:
        start_day = 2  # Start from day after tomorrow
    
    # Add dates starting from the determined start day
    for i in range(start_day, days + start_day):
        date = today + timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))
    return dates

def format_date_display(date_str: str) -> str:
    """Format date for display with day name"""
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    today = now_eastern().date()
    now = now_eastern()
    
    # Show time-sensitive labeling for the first available day
    if now.hour < 11:
        # Before 11am: first available is tomorrow
        if date == today + timedelta(days=1):
            return f"Tomorrow - {date.strftime('%A, %m/%d')}\nAvailable until 11am"
        elif date == today + timedelta(days=2):
            return f"{date.strftime('%A, %m/%d')}"
    else:
        # After 11am: first available is day after tomorrow
        if date == today + timedelta(days=2):
            return f"{date.strftime('%A, %m/%d')} - Available until 11am"
    
    # All other dates show day name and date
    return f"{date.strftime('%A, %m/%d')}"

# Initialize session state
if 'current_clipboard' not in st.session_state:
    st.session_state.current_clipboard = None
if 'selected_date' not in st.session_state:
    st.session_state.selected_date = None
if 'show_success' not in st.session_state:
    st.session_state.show_success = False
if 'success_info' not in st.session_state:
    st.session_state.success_info = {}

# Main app header
st.markdown('<h1 class="main-header">🚌 Operator Signup System</h1>', unsafe_allow_html=True)

# Clipboard selection screen
if st.session_state.current_clipboard is None:
    print(f"DEBUG: On home page - Current clipboard: {st.session_state.current_clipboard}")
    print(f"DEBUG: Home page session state keys: {list(st.session_state.keys())}")
    
    st.markdown("### Select a signup sheet:")
    
    # Tile-based layout with 3 equal columns
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Custom HTML button for Spare Work
        if st.button("🚌 Spare Work Sign Up", key="spare_work", help="Spare work opportunities", width='stretch'):
            print("DEBUG: Spare Work button clicked")
            st.session_state.current_clipboard = "SPARE_WORK"
            print(f"DEBUG: Set clipboard to: {st.session_state.current_clipboard}")
            st.rerun()
            
    with col2:
        # Custom HTML button for Extra Work
        if st.button("⭐ Extra Work Sign Up", key="extra_work", help="Additional work opportunities", width='stretch'):
            print("DEBUG: Extra Work button clicked")
            st.session_state.current_clipboard = "EXTRA_WORK"
            print(f"DEBUG: Set clipboard to: {st.session_state.current_clipboard}")
            st.rerun()

    with col3:
        # Custom HTML button for RDO
        if st.button("📋 RDO Sign Up", key="rdo", help="Regular Day Off signup", width='stretch'):
            print("DEBUG: RDO button clicked")
            st.session_state.current_clipboard = "RDO"
            print(f"DEBUG: Set clipboard to: {st.session_state.current_clipboard}")
            st.rerun()

# Date selection screen
elif st.session_state.selected_date is None:
    st.markdown(f"### 📅 Select date for {st.session_state.current_clipboard.replace('_', ' ').upper()}:")
    
    # Back button
    if st.button("← Back to Clipboards", key="back_to_clipboards"):
        st.session_state.current_clipboard = None
        st.rerun()
    
    dates = get_work_dates(31)  # Show next 31 days starting tomorrow
    
    # Show first 14 days (2 weeks) prominently
    st.markdown("#### 📅 Next 2 Weeks:")
    
    for i in range(0, min(14, len(dates)), 2):
        row_cols = st.columns(2)
        with row_cols[0]:
            date = dates[i]
            button_text = format_date_display(date)
            if st.button(button_text, key=f"date_{date}", width='stretch'):
                st.session_state.selected_date = date
                st.rerun()
        if i + 1 < len(dates[:14]):
            with row_cols[1]:
                date = dates[i + 1]
                button_text = format_date_display(date)
                if st.button(button_text, key=f"date_{date}", width='stretch'):
                    st.session_state.selected_date = date
                    st.rerun()
    
    # Show remaining dates in an expander
    if len(dates) > 14:
        with st.expander("📆 View More Dates (Weeks 3-5)", expanded=False):
            extended_dates = dates[14:]
            for i in range(0, len(extended_dates), 2):
                row_cols = st.columns(2)
                with row_cols[0]:
                    date = extended_dates[i]
                    button_text = format_date_display(date)
                    if st.button(button_text, key=f"date_extended_{date}", width='stretch'):
                        st.session_state.selected_date = date
                        st.rerun()
                if i + 1 < len(extended_dates):
                    with row_cols[1]:
                        date = extended_dates[i + 1]
                        button_text = format_date_display(date)
                        if st.button(button_text, key=f"date_extended_{date}", width='stretch'):
                            st.session_state.selected_date = date
                            st.rerun()

# Signup form screen
else:
    clipboard_type = st.session_state.current_clipboard
    selected_date = st.session_state.selected_date
    
    st.markdown(f"### 📝 {clipboard_type.replace('_', ' ').upper()} - {format_date_display(selected_date)}")
    
    # Back buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("← Back to Dates", key="back_to_dates"):
            st.session_state.selected_date = None
            st.rerun()
    with col2:
        if st.button("← Back to Clipboards", key="back_to_clipboards_2"):
            st.session_state.current_clipboard = None
            st.session_state.selected_date = None
            st.rerun()
    
    # Show current signups
    current_signups = load_signups(clipboard_type, selected_date)
    
    if current_signups:
        st.markdown("#### Current Signups:")
        
        if clipboard_type == "RDO":
            # RDO-specific display with ID, Name, and Choice of Work
            signup_data = []
            for signup in current_signups:
                additional_info = signup.get("additional_info", {})
                work_choice = additional_info.get("work_choice", "Not specified")
                phone_number = additional_info.get("phone_number", "")
                
                row_data = {
                    "ID #": additional_info.get("operator_id", "Not provided"),
                    "operator Name": signup["operator_name"],
                    "Choice of Work": work_choice
                }
                
                # Only add phone column if someone has provided a phone number
                if phone_number:
                    row_data["Phone #"] = phone_number
                
                signup_data.append(row_data)
        elif clipboard_type == "SPARE_WORK":
            # Spare Work-specific display
            signup_data = []
            for signup in current_signups:
                additional_info = signup.get("additional_info", {})
                
                signup_data.append({
                    "Shift": additional_info.get("shift_time", "Not specified"),
                    "ID #": additional_info.get("operator_id", "Not provided"),
                    "operator Name": signup["operator_name"],
                    "Work Interested IN": additional_info.get("work_interested", "Not specified")
                })
        elif clipboard_type == "EXTRA_WORK":
            # Extra Work-specific display
            signup_data = []
            for signup in current_signups:
                additional_info = signup.get("additional_info", {})
                
                signup_data.append({
                    "Shift": additional_info.get("shift_time", "Not specified"),
                    "ID #": additional_info.get("operator_id", "Not provided"),
                    "operator Name": signup["operator_name"],
                    "Work Interested IN": additional_info.get("work_interested", "Not specified")
                })
        else:
            # Default display for other clipboard types
            signup_data = []
            for signup in current_signups:
                row_data = {
                    "operator Name": signup["operator_name"],
                    "Signup Time": datetime.fromisoformat(signup["signup_time"]).strftime("%I:%M %p")
                }
                # Add notes if they exist
                additional_info = signup.get("additional_info", {})
                if additional_info.get("notes"):
                    row_data["Notes"] = additional_info["notes"]
                signup_data.append(row_data)
        
        signup_df = pd.DataFrame(signup_data)
        st.dataframe(signup_df, width='stretch', hide_index=True)
    else:
        st.info("No signups yet for this date.")
    
    # Check if we should show success message and countdown AFTER the table
    if st.session_state.show_success:
        success_info = st.session_state.success_info
        st.success(f"✅ Your request has been successfully submitted!")
        st.info(f"**{success_info['operator_name']}** signed up for **{success_info['clipboard_type']}** on **{success_info['formatted_date']}**")
        
        # Show countdown and return to home
        placeholder = st.empty()
        for seconds in range(6, 0, -1):
            placeholder.info(f"🏠 Returning to home page in {seconds} seconds...")
            import time
            time.sleep(1)
        
        # Reset session state to return to home
        st.session_state.current_clipboard = None
        st.session_state.selected_date = None
        st.session_state.show_success = False
        st.session_state.success_info = {}
        placeholder.empty()
        st.rerun()
    
    # Signup form
    st.markdown("#### Add Your Signup:")
    


    # --- Operator Data Integration ---
    operator_display_list, operator_lookup, display_to_id = get_operators_data()

    with st.form("signup_form", clear_on_submit=True):
        # Operator dropdown (Active only)
        operator_display = st.selectbox(
            "ID # - Operator Name",
            options=["Select your ID..."] + operator_display_list,
            index=0,
            help="Select your employee ID number and name"
        )

        # Map display string back to ID
        if operator_display != "Select your ID..." and operator_display in display_to_id:
            operator_id = display_to_id[operator_display]
            op_row = operator_lookup[operator_id]
            default_name = f"{op_row.get('First Name', '').strip()} {op_row.get('Last Name', '').strip()}"
            emp_status = op_row.get('Employee Status', '').strip()
        else:
            operator_id = ""
            default_name = ""
            emp_status = ""


        # Employee Status info message removed for faster signup

        # Set operator_name from selected operator ID
        operator_name = default_name

        # Clipboard-specific fields
        additional_info = {}

        if clipboard_type == "RDO":
            work_choice = st.text_input(
                "Choice of Work",
                placeholder="Enter your preferred work assignment...",
                help="Specify your preferred work assignment (e.g., AM Spare, PM Spare, Extra Board, etc.)"
            )
            phone_number = st.text_input(
                "Phone # (Optional)",
                placeholder="Enter phone number if you'd like to be on a call list...",
                help="Optional: Provide your phone number to be included on the call list"
            )
            additional_info = {
                "operator_id": operator_id if operator_id != "Select your ID..." else "",
                "work_choice": work_choice,
                "phone_number": phone_number
            }
        elif clipboard_type == "SPARE_WORK":
            shift_time = st.radio(
                "AM/PM",
                options=["AM", "PM", "Either"],
                index=None,
                help="Select when you're available to work",
                horizontal=True
            )
            work_interested = st.text_input(
                "Work Interested in",
                placeholder="Enter any work you're interested in...",
                help="Specify the type of spare work or assignment you're interested in"
            )
            additional_info = {
                "shift_time": shift_time,
                "operator_id": operator_id if operator_id != "Select your ID..." else "",
                "work_interested": work_interested
            }
        elif clipboard_type == "EXTRA_WORK":
            shift_time = st.radio(
                "AM/PM",
                options=["AM", "PM", "Either"],
                index=None,
                help="Select when you're available to work",
                horizontal=True
            )
            work_interested = st.text_input(
                "Work Interested in",
                placeholder="Enter any work you're interested in...",
                help="Specify the type of work or assignment you're interested in"
            )
            additional_info = {
                "shift_time": shift_time,
                "operator_id": operator_id if operator_id != "Select your ID..." else "",
                "work_interested": work_interested
            }
        else:
            notes = st.text_area(
                "Notes (Optional)",
                placeholder="Any additional information...",
                help="Optional notes or special requirements"
            )
            additional_info = {"notes": notes} if notes else {}
        
        submitted = st.form_submit_button("✅ Sign Me Up!", width='stretch')
        
        if submitted:
            # Validation based on clipboard type
            valid = True
            error_messages = []
            

            # No need to check operator_name, it's auto-filled from ID
            
            if clipboard_type == "RDO":
                if not operator_id.strip():
                    error_messages.append("Please enter your ID number.")
                    valid = False
                if not work_choice.strip():
                    error_messages.append("Please enter your choice of work.")
                    valid = False
            
            elif clipboard_type == "SPARE_WORK": 
                if not operator_id.strip():
                    error_messages.append("Please enter your ID number.")
                    valid = False
                if not shift_time:
                    error_messages.append("Please select a shift time.")
                    valid = False
                if not work_interested.strip():
                    error_messages.append("Please enter the spare work you're interested in.")
                    valid = False
            
            elif clipboard_type == "EXTRA_WORK":
                if not operator_id.strip():
                    error_messages.append("Please enter your ID number.")
                    valid = False
                if not shift_time:
                    error_messages.append("Please select a shift time.")
                    valid = False
                if not work_interested.strip():
                    error_messages.append("Please enter the work you're interested in.")
                    valid = False
            
            if valid:

                save_signup(clipboard_type, selected_date, operator_name.strip(), additional_info)
                
                # Set success info in session state and trigger page refresh
                st.session_state.show_success = True
                st.session_state.success_info = {
                    'operator_name': operator_name.strip(),
                    'clipboard_type': clipboard_type.replace('_', ' ').title(),
                    'formatted_date': format_date_display(selected_date)
                }
                st.rerun()
            else:
                for error in error_messages:
                    st.error(error)

# Footer
st.markdown("---")
st.markdown("**NICE Operator Signup System** • Questions? Contact your supervisor")