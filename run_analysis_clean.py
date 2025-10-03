#!/usr/bin/env python3
"""
Clean run script that clears Python cache and runs the analysis.
Use this when running from your IDE to avoid cache issues.
"""

import os
import sys
import shutil
import subprocess

def clear_python_cache():
    """Clear all Python cache files in the current directory and subdirectories."""
    print("[CLEAN] Clearing Python cache...")
    
    # Remove .pyc files
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.pyc'):
                try:
                    os.remove(os.path.join(root, file))
                    print(f"  Removed: {os.path.join(root, file)}")
                except:
                    pass
    
    # Remove __pycache__ directories
    for root, dirs, files in os.walk('.'):
        for dir_name in dirs:
            if dir_name == '__pycache__':
                try:
                    shutil.rmtree(os.path.join(root, dir_name))
                    print(f"  Removed: {os.path.join(root, dir_name)}")
                except:
                    pass
    
    print("[OK] Cache cleared!")

def main():
    """Main function to clear cache and run analysis."""
    print("=" * 60)
    print("CLEAN ANALYSIS RUN")
    print("=" * 60)
    
    # Clear cache
    clear_python_cache()
    
    print("\n[RUN] Running analysis...")
    print("-" * 40)
    
    # Run the analysis
    try:
        # Import and run the main analysis
        from run_analysis import main as run_main
        run_main()
    except Exception as e:
        print(f"[ERROR] Error running analysis: {e}")
        return 1
    
    print("\n[SUCCESS] Analysis completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
