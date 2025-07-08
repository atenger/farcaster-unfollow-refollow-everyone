#!/usr/bin/env python3
"""
Farcaster Refollow All Script

This script refollows users from the CSV file created by the unfollow script.
"""

import argparse
import csv
import logging
import os
import sys
import time
from datetime import datetime
from farcaster_api import FarcasterAPI

# Configure logging
def setup_logging(my_fid: int, timestamp: str):
    """Setup logging with FID-specific log file"""
    log_filename = f"data/refollow_log_{my_fid}_{timestamp}.txt"
    
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Create a new logger instead of using basicConfig
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    
    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    # Create file handler with UTF-8 encoding
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Prevent propagation to avoid duplicate logs
    logger.propagate = False
    
    return logger

def confirm_action(message: str) -> bool:
    """Ask for user confirmation before proceeding"""
    while True:
        response = input(f"{message} (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            return True
        elif response in ['n', 'no']:
            return False
        else:
            print("Please enter 'y' or 'n'")

def load_users_from_csv(filename: str = None, my_fid: int = None, logger = None):
    """Load user data from CSV file"""
    try:
        # If no filename provided, find the most recent CSV file for your FID in data directory
        if filename is None:
            import glob
            import os
            from farcaster_api import FarcasterAPI
            
            # Get your FID to filter files
            try:
                api = FarcasterAPI()
                my_fid = api.get_my_fid()
                if not my_fid:
                    if logger:
                        logger.error("Could not determine your FID. Check your API credentials.")
                    return None
                
                # Look for files matching your FID
                csv_files = glob.glob(f"data/unfollowed_users_{my_fid}_*.csv")
                if not csv_files:
                    if logger:
                        logger.error(f"No CSV files found for your FID ({my_fid}) in data directory. Run unfollow_all.py first.")
                    return None
                
                # Sort by modification time (newest first)
                csv_files.sort(key=os.path.getmtime, reverse=True)
                filename = csv_files[0]
                if logger:
                    logger.info(f"Using most recent CSV file for your FID ({my_fid}): {filename}")
                
            except Exception as e:
                if logger:
                    logger.error(f"Error getting your FID: {e}")
                return None
        
        users = []
        with open(filename, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                users.append({
                    'fid': int(row['fid']),
                    'username': row['username'],
                    'display_name': row['display_name'],
                    'unfollowed_at': row['unfollowed_at']
                })
        
        if logger:
            logger.info(f"Loaded {len(users)} users from {filename}")
        return users
        
    except FileNotFoundError:
        if logger:
            logger.error(f"CSV file '{filename}' not found. Run unfollow_all.py first.")
        return None
    except Exception as e:
        if logger:
            logger.error(f"Error loading CSV file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Refollow users from CSV file')
    parser.add_argument('--csv-file', default=None,
                       help='CSV file to read users from (default: most recent file in data directory)')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (no actual follows)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between follows in seconds (default: 1.0)')
    parser.add_argument('--start-from', type=int, default=0,
                       help='Start from this index (useful for resuming)')
    
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api = FarcasterAPI()
        
        # Get my FID
        my_fid = api.get_my_fid()
        if not my_fid:
            print("Could not determine your FID. Check your API credentials.")
            return 1
        
        # Create timestamp for log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup logging with FID-specific log file
        logger = setup_logging(my_fid, timestamp)
        
        logger.info(f"Your FID: {my_fid}")
        
        # Load users from CSV
        users = load_users_from_csv(args.csv_file, my_fid, logger)
        if not users:
            return 1
        
        # Apply start-from index
        if args.start_from > 0:
            if args.start_from >= len(users):
                logger.error(f"Start index {args.start_from} is out of range (max: {len(users)-1})")
                return 1
            users = users[args.start_from:]
            logger.info(f"Starting from index {args.start_from}, {len(users)} users remaining")
        
        # Show preview
        print(f"\nFound {len(users)} users to refollow:")
        for i, user in enumerate(users[:5]):  # Show first 5
            username = user.get('username', 'unknown')
            display_name = user.get('display_name', '')
            print(f"  {i+1}. @{username} ({display_name})")
        
        if len(users) > 5:
            print(f"  ... and {len(users) - 5} more users")
        
        # Confirmation
        if args.dry_run:
            message = f"DRY RUN: Would refollow all {len(users)} users (no actual changes will be made)"
        else:
            message = f"WARNING: This will refollow all {len(users)} users. Are you sure?"
        
        if not confirm_action(message):
            logger.info("Operation cancelled by user")
            return 0
        
        # Process refollows
        successful_follows = []
        failed_follows = []
        
        for i, user in enumerate(users, 1):
            fid = user['fid']
            username = user.get('username', 'unknown')
            
            logger.info(f"Processing {i}/{len(users)}: @{username} (FID: {fid})")
            
            success = api.follow_user(fid, dry_run=args.dry_run)
            
            if success:
                successful_follows.append(user)
                logger.info(f"Successfully refollowed @{username}")
            else:
                failed_follows.append(user)
                logger.error(f"Failed to refollow @{username}")
            
            # Rate limiting
            if i < len(users):  # Don't delay after the last one
                time.sleep(args.delay)
        
        # Summary
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Total users processed: {len(users)}")
        logger.info(f"Successful refollows: {len(successful_follows)}")
        logger.info(f"Failed refollows: {len(failed_follows)}")
        
        if failed_follows:
            logger.warning("Some refollows failed. You may want to retry manually.")
            logger.info("Failed users:")
            for user in failed_follows:
                logger.info(f"  - @{user.get('username', 'unknown')} (FID: {user['fid']})")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nOperation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 