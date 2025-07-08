#!/usr/bin/env python3
"""
Test Connection Script

This script tests the connection to the Farcaster API and verifies credentials.
"""

import sys
from farcaster_api import FarcasterAPI

def main():
    try:
        print("Testing Farcaster API connection...")
        
        # Initialize API client
        api = FarcasterAPI()
        print("✓ API client initialized successfully")
        
        # Test getting my FID
        my_fid = api.get_my_fid()
        if my_fid:
            print(f"✓ Successfully retrieved your FID: {my_fid}")
        else:
            print("✗ Could not retrieve your FID")
            return 1
        
        # Test getting following list (just a small sample)
        try:
            following = api.get_following_list(my_fid)
            print(f"✓ Successfully retrieved following list ({len(following)} users)")
            
            if following:
                print("Sample users you're following:")
                for user in following[:3]:
                    username = user.get('username', 'unknown')
                    display_name = user.get('display_name', '')
                    fid = user.get('fid', '')
                    print(f"  - @{username} ({display_name}) - FID: {fid}")
        except Exception as e:
            print(f"⚠ Warning: Could not retrieve following list: {e}")
        
        print("\n✓ All tests passed! Your API credentials are working correctly.")
        print("You can now run unfollow_all.py or refollow_all.py")
        
        return 0
        
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print("Please check your .env file and ensure NEYNAR_API_KEY and NEYNAR_SIGNER_UUID are set correctly.")
        return 1
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 