"""
Simple timezone fix utility to handle datetime columns safely.
This ensures timezone-aware datetime objects are converted to timezone-naive
before saving to Excel files, preventing Excel export errors.
"""

import pandas as pd


def remove_timezone_from_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Remove timezone information from all datetime columns in a DataFrame.
    This prevents Excel export errors while preserving the datetime values.
    
    Args:
        df: pandas DataFrame
        
    Returns:
        DataFrame with timezone information removed from datetime columns
    """
    df_clean = df.copy()
    
    for col in df_clean.columns:
        if df_clean[col].dtype.name.startswith('datetime64'):
            try:
                # Check if column has timezone info
                if df_clean[col].dtype.name == 'datetime64[ns, UTC]':
                    df_clean[col] = df_clean[col].dt.tz_localize(None)
                elif hasattr(df_clean[col].dtype, 'tz') and df_clean[col].dtype.tz is not None:
                    df_clean[col] = df_clean[col].dt.tz_localize(None)
                # If it's already timezone-naive, leave it as is
            except Exception as e:
                print(f"Warning: Could not remove timezone from column '{col}': {e}")
                continue
    
    return df_clean


def safe_to_datetime(series: pd.Series, utc: bool = False) -> pd.Series:
    """
    Safely convert a series to datetime and remove timezone information.
    
    Args:
        series: pandas Series to convert
        utc: Whether to parse as UTC first (then remove timezone)
        
    Returns:
        Series converted to datetime with timezone information removed
    """
    try:
        if utc:
            # Parse as UTC first, then remove timezone
            dt_series = pd.to_datetime(series, errors='coerce', utc=True)
            if dt_series.dtype.name == 'datetime64[ns, UTC]':
                return dt_series.dt.tz_localize(None)
            return dt_series
        else:
            # Parse as timezone-naive
            return pd.to_datetime(series, errors='coerce')
    except Exception as e:
        print(f"Warning: Error converting to datetime: {e}")
        return series
