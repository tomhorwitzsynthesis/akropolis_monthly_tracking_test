import os
import pandas as pd
import streamlit as st
from .config import DATA_ROOT  # <-- import here
from .date_utils import get_selected_date_range

# ------------------------
# 📄 Load Agility (News)
# ------------------------
@st.cache_data
def load_agility_data(company_name: str):
    path = os.path.join(DATA_ROOT, "agility", f"{company_name.lower()}_agility.xlsx")
    if not os.path.exists(path):
        return None
    try:
        xls = pd.ExcelFile(path)
        target_sheet = "Raw Data" if "Raw Data" in xls.sheet_names else xls.sheet_names[0]
        df = pd.read_excel(xls, sheet_name=target_sheet)
    except Exception as e:
        st.error(f"[Agility] Error loading {company_name}: {e}")
        return None

    # Normalize Published Date column if needed
    if "Published Date" not in df.columns:
        for candidate in ["PublishedDate", "published_date", "Date", "date"]:
            if candidate in df.columns:
                df = df.rename(columns={candidate: "Published Date"})
                break

    return df

# ------------------------
# 📱 Load Social Media Data
# ------------------------

@st.cache_data
def load_social_data(company_name: str, platform: str, use_consolidated: bool = True):
	"""Load Facebook or LinkedIn file for a company, normalize date format.
	
	Args:
		company_name: Name of the company
		platform: 'facebook' or 'linkedin'
		use_consolidated: If True, load from consolidated files (linkedin_posts.xlsx/fb_posts.xlsx)
		                 If False, load from individual company files
	"""
	platform = platform.lower()
	if platform not in {"facebook", "linkedin"}:
		raise ValueError("Platform must be 'facebook' or 'linkedin'")

	if use_consolidated:
		# Load from consolidated files
		if platform == "linkedin":
			filename = "linkedin_posts.xlsx"
			company_col = "user_id"
		else:  # facebook
			filename = "fb_posts.xlsx"
			company_col = "user_username_raw"
		
		path = os.path.join(DATA_ROOT, "social_media", filename)
		
		if not os.path.exists(path):
			return None
			
		try:
			df = pd.read_excel(path, sheet_name=0)
			# Filter for the specific company
			if company_col in df.columns:
				df = df[df[company_col] == company_name].copy()
				if df.empty:
					return None
			else:
				st.error(f"[Social] Company column '{company_col}' not found in {filename}")
				return None
		except Exception as e:
			st.error(f"[Social] Error loading {platform} data for {company_name}: {e}")
			return None
	else:
		# Load from individual company files (original behavior)
		filename = f"{company_name.lower()}_{platform}.xlsx"
		path = os.path.join(DATA_ROOT, "social_media", filename)

		if not os.path.exists(path):
			return None

		try:
			df = pd.read_excel(path, sheet_name=0)
		except Exception as e:
			st.error(f"[Social] Error loading {platform} data for {company_name}: {e}")
			return None

	# Normalize datetime column
	if "Published Date" not in df.columns:
		if "date_posted" in df.columns:
			df["Published Date"] = pd.to_datetime(df["date_posted"], utc=True, errors="coerce").dt.tz_localize(None)
		elif "PublishedDate" in df.columns:
			df["Published Date"] = pd.to_datetime(df["PublishedDate"], utc=True, errors="coerce").dt.tz_localize(None)
		else:
			st.warning(f"No recognizable date column in {filename}. Available columns: {list(df.columns)}")
			return None
	else:
		df["Published Date"] = pd.to_datetime(df["Published Date"], utc=True, errors="coerce").dt.tz_localize(None)

	return df

# ------------------------
# 🗃️ Load the Actual Volume 
# ------------------------

AGILITY_METADATA_PATH = os.path.join(DATA_ROOT, "agility", "agility_metadata.xlsx")

def load_agility_volume_map():
	if os.path.exists(AGILITY_METADATA_PATH):
		return pd.read_excel(AGILITY_METADATA_PATH, index_col="Company").to_dict()["Volume"]
	else:
		return {}

# ------------------------
# 🗃️ Load All Brands' Social Media Data for a Platform
# ------------------------

def load_all_social_data(brands, platform: str, use_consolidated: bool = False):
	"""Return dict[brand] = DataFrame for selected platform (e.g. Facebook).
	
	Args:
		brands: List of brand names
		platform: 'facebook' or 'linkedin'
		use_consolidated: If True, load from consolidated files (linkedin_posts.xlsx/fb_posts.xlsx)
		                 If False, load from individual company files
	"""
	results = {}
	for brand in brands:
		df = load_social_data(brand, platform, use_consolidated=use_consolidated)
		if df is not None and not df.empty:
			results[brand] = df
	return results

# ------------------------
# 📢 Load Ads Intelligence data
# ------------------------

@st.cache_data
def load_ads_data():
	"""
	Load ads scraping Excel and normalize key fields.
	Returns a pandas DataFrame or None if not found.
	"""
	# Build potential roots: configured root, module-relative root, and CWD/data
	module_dir = os.path.dirname(os.path.abspath(__file__))
	project_root = os.path.abspath(os.path.join(module_dir, os.pardir))
	module_data_root = os.path.join(project_root, "data")
	cwd_data_root = os.path.join(os.getcwd(), "data")
	roots = [DATA_ROOT, module_data_root, cwd_data_root]

	candidate_filenames = [
		"ads.xlsx",
		"ads_scraping.xlsx",
		"ads_scraping (2).xlsx",
		"ads_scraping_LP.xlsx",
	]

	candidate_paths = []
	for root in roots:
		candidate_paths.extend([os.path.join(root, "ads", fname) for fname in candidate_filenames])

	# Deduplicate while preserving order
	seen = set()
	candidate_paths = [p for p in candidate_paths if not (p in seen or seen.add(p))]

	path = next((p for p in candidate_paths if os.path.exists(p)), None)
	if path is None:
		st.warning("Ads data file not found in expected locations.")
		return None

	try:
		df = pd.read_excel(path, sheet_name=0)
	except Exception as e:
		st.error(f"[Ads] Error loading ads data: {e}")
		return None

	# Normalize dates
	for col in ["startDateFormatted", "endDateFormatted"]:
		if col in df.columns:
			df[col] = pd.to_datetime(df[col], utc=True, errors="coerce").dt.tz_localize(None)

	# Normalize numeric reach
	reach_col = "ad_details/aaa_info/eu_total_reach"
	if reach_col in df.columns:
		df["reach"] = pd.to_numeric(df[reach_col], errors="coerce")
	else:
		# Fallbacks commonly seen in exports
		for alt in ["reach", "estimated_audience_size", "eu_total_reach"]:
			if alt in df.columns:
				df["reach"] = pd.to_numeric(df[alt], errors="coerce")
				break
		else:
			df["reach"] = 0

	# Brand and flags
	if "pageName" in df.columns:
		df["brand"] = df["pageName"]
	elif "page_name" in df.columns:
		df["brand"] = df["page_name"]
	if "isActive" in df.columns:
		df["isActive"] = df["isActive"].astype(bool)

	# Duration
	if "startDateFormatted" in df.columns and "endDateFormatted" in df.columns:
		df["duration_days"] = (df["endDateFormatted"] - df["startDateFormatted"]).dt.days

	return df

# ------------------------
# 🎯 Load Audience Affinity outputs (pickled)
# ------------------------

@st.cache_data
def load_audience_affinity_outputs():
	"""Load audience affinity outputs from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = {}
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load audience affinity outputs
				audience_affinity_path = os.path.join(DATA_ROOT, month_folder, "social_media", "analysis", "audience_affinity", "audience_affinity_outputs.pkl")
				if os.path.exists(audience_affinity_path):
					try:
						import pickle
						with open(audience_affinity_path, 'rb') as f:
							month_data = pickle.load(f)
							# Merge data from this month (audience affinity data structure is different)
							if isinstance(month_data, dict):
								for key, value in month_data.items():
									if key not in all_data:
										all_data[key] = value
					except Exception as e:
						if 'st' in globals():
							st.warning(f"Could not load audience affinity data for {month_folder}: {e}")
						else:
							print(f"Could not load audience affinity data for {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						audience_affinity_path = os.path.join(DATA_ROOT, folder, "social_media", "analysis", "audience_affinity", "audience_affinity_outputs.pkl")
						if os.path.exists(audience_affinity_path):
							try:
								import pickle
								with open(audience_affinity_path, 'rb') as f:
									month_data = pickle.load(f)
									# Merge data from this month (audience affinity data structure is different)
									if isinstance(month_data, dict):
										for key, value in month_data.items():
											if key not in all_data:
												all_data[key] = value
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load audience affinity data for {folder}: {e}")
								else:
									print(f"Could not load audience affinity data for {folder}: {e}")
		
		if all_data:
			return all_data
		else:
			if 'st' in globals():
				st.warning("Audience affinity outputs not found in any monthly folders.")
			return None
			
	except Exception as e:
		if 'st' in globals():
			st.error(f"[Audience Affinity] Error loading outputs: {e}")
		else:
			print(f"[Audience Affinity] Error loading outputs: {e}")
		return None

# ------------------------
# 🧱 Load Content Pillars outputs (pickled)
# ------------------------

@st.cache_data
def load_content_pillar_outputs():
	"""Load content pillar outputs from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = {}
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load content pillar outputs
				content_pillars_path = os.path.join(DATA_ROOT, month_folder, "social_media", "analysis", "content_pillars", "content_pillar_outputs.pkl")
				if os.path.exists(content_pillars_path):
					try:
						import pickle
						with open(content_pillars_path, 'rb') as f:
							month_data = pickle.load(f)
							# Merge data from this month
							for brand, data in month_data.items():
								if brand not in all_data:
									all_data[brand] = data
					except Exception as e:
						if 'st' in globals():
							st.warning(f"Could not load content pillar data for {month_folder}: {e}")
						else:
							print(f"Could not load content pillar data for {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						content_pillars_path = os.path.join(DATA_ROOT, folder, "social_media", "analysis", "content_pillars", "content_pillar_outputs.pkl")
						if os.path.exists(content_pillars_path):
							try:
								import pickle
								with open(content_pillars_path, 'rb') as f:
									month_data = pickle.load(f)
									# Merge data from this month
									for brand, data in month_data.items():
										if brand not in all_data:
											all_data[brand] = data
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load content pillar data for {folder}: {e}")
								else:
									print(f"Could not load content pillar data for {folder}: {e}")
		
		if all_data:
			return all_data
		else:
			if 'st' in globals():
				st.warning("Content pillar outputs not found in any monthly folders.")
			return None
			
	except Exception as e:
		if 'st' in globals():
			st.error(f"[Content Pillars] Error loading outputs: {e}")
		else:
			print(f"[Content Pillars] Error loading outputs: {e}")
		return None

# ------------------------
# 📊 Load Monthly Dashboard Data
# ------------------------

def get_month_folder_name(year: int, month: int) -> str:
	"""Generate folder name in YYYY-MM format"""
	return f"{year}-{month:02d}"

@st.cache_data
def load_monthly_ads_data():
	"""Load ads data from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except Exception as e:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = []
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load ads master data
				ads_path = os.path.join(DATA_ROOT, month_folder, "ads", "ads_master_data.xlsx")
				if os.path.exists(ads_path):
					try:
						df = pd.read_excel(ads_path)
						df['month'] = month_folder
						all_data.append(df)
					except Exception as e:
						if 'st' in globals():
							st.warning(f"Could not load ads data for {month_folder}: {e}")
						else:
							print(f"Could not load ads data for {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						ads_path = os.path.join(DATA_ROOT, folder, "ads", "ads_master_data.xlsx")
						if os.path.exists(ads_path):
							try:
								df = pd.read_excel(ads_path)
								df['month'] = folder
								all_data.append(df)
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load ads data for {folder}: {e}")
								else:
									print(f"Could not load ads data for {folder}: {e}")
		
		if all_data:
			result = pd.concat(all_data, ignore_index=True)
			
			# Standardize column names for ads data
			if 'ad_details/aaa_info/eu_total_reach' in result.columns:
				result['reach'] = result['ad_details/aaa_info/eu_total_reach']
			elif 'reachEstimate' in result.columns:
				result['reach'] = result['reachEstimate']
			else:
				result['reach'] = 0  # Default to 0 if no reach data
			
			# Add standardized date column
			if 'startDateFormatted' in result.columns:
				result['date'] = pd.to_datetime(result['startDateFormatted'], errors='coerce')
			elif 'Date' in result.columns:
				result['date'] = pd.to_datetime(result['Date'], errors='coerce')
			else:
				result['date'] = pd.NaT
			
			return result
		else:
			return pd.DataFrame()
			
	except Exception as e:
		if 'st' in globals():
			st.error(f"Error loading monthly ads data: {e}")
		else:
			print(f"Error loading monthly ads data: {e}")
		return pd.DataFrame()

@st.cache_data
def load_monthly_social_media_data():
	"""Load social media data from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = []
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load social media master data
				social_path = os.path.join(DATA_ROOT, month_folder, "social_media", "social_media_master_data.xlsx")
				if os.path.exists(social_path):
					try:
						df = pd.read_excel(social_path)
						df['month'] = month_folder
						all_data.append(df)
					except Exception as e:
						if 'st' in globals():
							st.warning(f"Could not load social media data for {month_folder}: {e}")
						else:
							print(f"Could not load social media data for {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						social_path = os.path.join(DATA_ROOT, folder, "social_media", "social_media_master_data.xlsx")
						if os.path.exists(social_path):
							try:
								df = pd.read_excel(social_path)
								df['month'] = folder
								all_data.append(df)
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load social media data for {folder}: {e}")
								else:
									print(f"Could not load social media data for {folder}: {e}")
		
		if all_data:
			result = pd.concat(all_data, ignore_index=True)
			
			# Standardize column names for social media data
			# Calculate engagement from individual metrics
			if 'likes' in result.columns and 'num_comments' in result.columns and 'num_shares' in result.columns:
				# Calculate total engagement: likes + comments*3 + shares*5
				likes = pd.to_numeric(result['likes'], errors='coerce').fillna(0)
				comments = pd.to_numeric(result['num_comments'], errors='coerce').fillna(0)
				shares = pd.to_numeric(result['num_shares'], errors='coerce').fillna(0)
				result['calculated_engagement'] = likes + comments * 3 + shares * 5
			elif 'total_engagement' in result.columns:
				result['calculated_engagement'] = pd.to_numeric(result['total_engagement'], errors='coerce').fillna(0)
			else:
				result['calculated_engagement'] = 0  # Default to 0 if no engagement data
			
			# Add standardized date column
			if 'date_posted' in result.columns:
				result['date'] = pd.to_datetime(result['date_posted'], errors='coerce').dt.tz_localize(None)
			elif 'created_date' in result.columns:
				result['date'] = pd.to_datetime(result['created_date'], errors='coerce').dt.tz_localize(None)
			else:
				result['date'] = pd.NaT
			
			return result
		else:
			return pd.DataFrame()
			
	except Exception as e:
		if 'st' in globals():
			st.error(f"Error loading monthly social media data: {e}")
		else:
			print(f"Error loading monthly social media data: {e}")
		return pd.DataFrame()

@st.cache_data
def load_monthly_pr_data():
	"""Load PR data from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = []
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load PR master data
				pr_path = os.path.join(DATA_ROOT, month_folder, "pr", "pr_master_data.xlsx")
				if os.path.exists(pr_path):
					try:
						df = pd.read_excel(pr_path)
						df['month'] = month_folder
						all_data.append(df)
					except Exception as e:
						if 'st' in globals():
							st.warning(f"Could not load PR data for {month_folder}: {e}")
						else:
							print(f"Could not load PR data for {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						pr_path = os.path.join(DATA_ROOT, folder, "pr", "pr_master_data.xlsx")
						if os.path.exists(pr_path):
							try:
								df = pd.read_excel(pr_path)
								df['month'] = folder
								all_data.append(df)
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load PR data for {folder}: {e}")
								else:
									print(f"Could not load PR data for {folder}: {e}")
		
		if all_data:
			result = pd.concat(all_data, ignore_index=True)
			
			# Standardize column names for PR data
			# Use Impressions as reach metric for PR
			if 'Impressions' in result.columns:
				result['reach'] = result['Impressions']
			else:
				result['reach'] = 0  # Default to 0 if no impressions data
			
			# Add standardized date column
			if 'Published Date' in result.columns:
				result['date'] = pd.to_datetime(result['Published Date'], errors='coerce')
			else:
				result['date'] = pd.NaT
			
			return result
		else:
			return pd.DataFrame()
			
	except Exception as e:
		if 'st' in globals():
			st.error(f"Error loading monthly PR data: {e}")
		else:
			print(f"Error loading monthly PR data: {e}")
		return pd.DataFrame()

def load_creativity_analysis(media_type: str):
	"""Load creativity analysis from dashboard_data monthly folders - ONLY from selected month"""
	try:
		start_date, end_date = get_selected_date_range()
		all_data = []
		
		# Load ONLY from selected date range - no fallbacks
		current_date = start_date
		while current_date < end_date:
			year = current_date.year
			month = current_date.month
			month_folder = get_month_folder_name(year, month)
			
			# Try to load creativity analysis
			creativity_path = os.path.join(DATA_ROOT, month_folder, media_type, "analysis", "creativity", f"creativity_analysis_{media_type}.xlsx")
			if os.path.exists(creativity_path):
				try:
					df = pd.read_excel(creativity_path)
					df['month'] = month_folder
					all_data.append(df)
				except Exception as e:
					st.warning(f"Could not load creativity data for {media_type} in {month_folder}: {e}")
			
			# Move to next month
			if month == 12:
				current_date = current_date.replace(year=year + 1, month=1)
			else:
				current_date = current_date.replace(month=month + 1)
		
		if all_data:
			return pd.concat(all_data, ignore_index=True)
		else:
			return pd.DataFrame()
			
	except Exception as e:
		st.error(f"Error loading creativity analysis for {media_type}: {e}")
		return pd.DataFrame()

@st.cache_data
def load_compos_analysis(media_type: str):
	"""Load compos analysis from dashboard_data monthly folders"""
	try:
		# Try to get selected date range, fallback to all available months
		try:
			start_date, end_date = get_selected_date_range()
		except:
			# Fallback: load all available months
			start_date = None
			end_date = None
		
		all_data = []
		
		if start_date and end_date:
			# Use selected date range
			current_date = start_date
			while current_date < end_date:
				year = current_date.year
				month = current_date.month
				month_folder = get_month_folder_name(year, month)
				
				# Try to load compos analysis
				compos_path = os.path.join(DATA_ROOT, month_folder, media_type, "analysis", "compos", f"compos_analysis_{media_type}.xlsx")
				if os.path.exists(compos_path):
					try:
						df = pd.read_excel(compos_path)
						df['month'] = month_folder
						all_data.append(df)
					except Exception as e:
						st.warning(f"Could not load compos data for {media_type} in {month_folder}: {e}")
				
				# Move to next month
				if month == 12:
					current_date = current_date.replace(year=year + 1, month=1)
				else:
					current_date = current_date.replace(month=month + 1)
		else:
			# Load all available months
			if os.path.exists(DATA_ROOT):
				for folder in os.listdir(DATA_ROOT):
					if os.path.isdir(os.path.join(DATA_ROOT, folder)) and len(folder) == 7 and folder[4] == '-':
						compos_path = os.path.join(DATA_ROOT, folder, media_type, "analysis", "compos", f"compos_analysis_{media_type}.xlsx")
						if os.path.exists(compos_path):
							try:
								df = pd.read_excel(compos_path)
								df['month'] = folder
								all_data.append(df)
							except Exception as e:
								if 'st' in globals():
									st.warning(f"Could not load compos data for {media_type} in {folder}: {e}")
								else:
									print(f"Could not load compos data for {media_type} in {folder}: {e}")
		
		if all_data:
			return pd.concat(all_data, ignore_index=True)
		else:
			return pd.DataFrame()
			
	except Exception as e:
		st.error(f"Error loading compos analysis for {media_type}: {e}")
		return pd.DataFrame()
