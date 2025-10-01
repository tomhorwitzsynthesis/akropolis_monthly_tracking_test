# utils/date_utils.py
import streamlit as st
import os
from datetime import datetime
from calendar import month_name

# Dynamically discover available months from dashboard_data folder
def get_available_months():
    """Get available months from dashboard_data folder structure"""
    # Try different possible paths for dashboard_data
    possible_paths = ["dashboard_data", "../dashboard_data", "../../dashboard_data"]
    data_root = None
    
    for path in possible_paths:
        if os.path.exists(path):
            data_root = path
            break
    
    available_months = []
    
    if data_root and os.path.exists(data_root):
        for folder in os.listdir(data_root):
            if os.path.isdir(os.path.join(data_root, folder)):
                try:
                    # Parse YYYY-MM format
                    if len(folder) == 7 and folder[4] == '-':
                        year = int(folder[:4])
                        month = int(folder[5:7])
                        if 2020 <= year <= 2030 and 1 <= month <= 12:
                            available_months.append((year, month))
                except (ValueError, IndexError):
                    continue
    
    # Sort by year, then month
    available_months.sort()
    return available_months

# Get available months dynamically - this will be called each time
def get_available_months_list():
    """Get the list of available months, with fallback"""
    months = get_available_months()
    if not months:
        months = [(2025, 8), (2025, 9)]  # Default fallback
    return months

def get_selected_date_range():
    selected = st.session_state.get("selected_months", [])
    if not selected:
        st.sidebar.error("No months selected.")
        st.stop()

    selected.sort()
    start_year, start_month = selected[0]
    end_year, end_month = selected[-1]

    start_date = datetime(start_year, start_month, 1)
    if end_month == 12:
        end_date = datetime(end_year + 1, 1, 1)
    else:
        end_date = datetime(end_year, end_month + 1, 1)

    return start_date, end_date

def init_month_selector():
    st.sidebar.markdown("### Select Month")

    # Get available months dynamically
    available_months = get_available_months_list()
    
    # Prepare options for dropdown
    options = [
        (year, month, f"{month_name[month]} {year}")
        for year, month in available_months
    ]
    labels = [opt[2] for opt in options]

    # Default to the most recent month
    default_idx = len(options) - 1

    selected_idx = st.sidebar.selectbox(
        "Month", options=range(len(options)), format_func=lambda i: labels[i], index=default_idx
    )

    # Set selected month
    selected_month = (options[selected_idx][0], options[selected_idx][1])
    st.session_state["selected_months"] = [selected_month]
