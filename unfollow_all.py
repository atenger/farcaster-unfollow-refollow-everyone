#!/usr/bin/env python3
"""
Farcaster Unfollow All Script

This script unfollows all users you're currently following on Farcaster
and logs them to a CSV file for later refollowing.
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
    log_filename = f"data/unfollow_log_{my_fid}_{timestamp}.txt"
    
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

def save_user_to_csv(user: dict, my_fid: int, timestamp: str, csv_filename: str = None):
    """Save a single user to CSV file with FID and timestamp"""
    try:
        # Create filename with FID and timestamp if not provided
        if csv_filename is None:
            csv_filename = f"data/unfollowed_users_{my_fid}_{timestamp}.csv"
        
        # Check if file exists to determine if we need to write header
        file_exists = os.path.exists(csv_filename)
        
        with open(csv_filename, 'a', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['fid', 'username', 'display_name', 'unfollowed_at']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            # Write header only if file is new
            if not file_exists:
                writer.writeheader()
            
            writer.writerow({
                'fid': user['fid'],
                'username': user.get('username', ''),
                'display_name': user.get('display_name', ''),
                'unfollowed_at': datetime.now().isoformat()
            })
        
        return csv_filename
        
    except Exception as e:
        logger.error(f"Error saving user to CSV: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Unfollow all Farcaster users')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Run in dry-run mode (no actual unfollows)')
    parser.add_argument('--delay', type=float, default=1.0,
                       help='Delay between unfollows in seconds (default: 1.0)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of users to process (useful for testing)')

    
    args = parser.parse_args()
    
    try:
        # Initialize API client
        api = FarcasterAPI()
        
        # Get my FID
        my_fid = api.get_my_fid()
        if not my_fid:
            print("Could not determine your FID. Check your API credentials.")
            return 1
        
        # Create timestamp once for both CSV and log files
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup logging with FID-specific log file using same timestamp
        logger = setup_logging(my_fid, timestamp)
        
        logger.info(f"Your FID: {my_fid}")
        
        # Get following list
        following_users = api.get_following_list(my_fid)
        
        if not following_users:
            logger.info("You're not following anyone.")
            return 0
        
        logger.info(f"Found {len(following_users)} users you're following")
        
        # Apply limit if specified
        if args.limit:
            original_count = len(following_users)
            following_users = following_users[:args.limit]
            logger.info(f"Limited to first {args.limit} users (out of {original_count} total)")
        
        # Show preview
        print(f"\nYou're currently following {len(following_users)} users:")
        for i, user in enumerate(following_users[:5]):  # Show first 5
            username = user.get('username', 'unknown')
            display_name = user.get('display_name', '')
            print(f"  {i+1}. @{username} ({display_name})")
        
        if len(following_users) > 5:
            print(f"  ... and {len(following_users) - 5} more users")
        
        # Confirmation
        if args.dry_run:
            message = f"DRY RUN: Would unfollow all {len(following_users)} users (no actual changes will be made)"
        else:
            message = f"WARNING: This will unfollow all {len(following_users)} users. Are you sure?"
        
        if not confirm_action(message):
            logger.info("Operation cancelled by user")
            return 0
        
        # Process unfollows
        successful_unfollows = []
        failed_unfollows = []
        csv_filename = None
        
        for i, user in enumerate(following_users, 1):
            fid = user['fid']
            username = user.get('username', 'unknown')
            
            logger.info(f"Processing {i}/{len(following_users)}: @{username} (FID: {fid})")
            
            success = api.unfollow_user(fid, dry_run=args.dry_run)
            
            if success:
                successful_unfollows.append(user)
                logger.info(f"Successfully unfollowed @{username}")
                
                # Save to CSV immediately after successful unfollow
                csv_filename = save_user_to_csv(user, my_fid, timestamp, csv_filename)
                if csv_filename:
                    logger.info(f"Saved @{username} to {csv_filename}")
                else:
                    logger.error(f"Failed to save @{username} to CSV")
            else:
                failed_unfollows.append(user)
                logger.error(f"Failed to unfollow @{username}")
            
            # Rate limiting
            if i < len(following_users):  # Don't delay after the last one
                time.sleep(args.delay)
        
        # Summary
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Total users processed: {len(following_users)}")
        logger.info(f"Successful unfollows: {len(successful_unfollows)}")
        logger.info(f"Failed unfollows: {len(failed_unfollows)}")
        
        if csv_filename:
            logger.info(f"All unfollowed users saved to {csv_filename}")
        else:
            logger.error("Failed to save users to CSV")
        
        if failed_unfollows:
            logger.warning("Some unfollows failed. You may want to retry manually.")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("\nOperation interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 