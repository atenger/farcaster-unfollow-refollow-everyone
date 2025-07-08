import os
import requests
import logging
import time
from dotenv import load_dotenv
from typing import List, Dict, Optional

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class FarcasterAPI:
    """Farcaster API client using Neynar API"""
    
    def __init__(self):
        self.api_key = os.getenv("NEYNAR_API_KEY")
        self.signer_uuid = os.getenv("NEYNAR_SIGNER_UUID")
        
        if not self.api_key:
            raise ValueError("NEYNAR_API_KEY environment variable is required")
        if not self.signer_uuid:
            raise ValueError("NEYNAR_SIGNER_UUID environment variable is required")
        
        self.base_url = "https://api.neynar.com/v2/farcaster"
        self.headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api_key": self.api_key
        }
    
    def get_following_list(self, fid: int) -> List[Dict]:
        """
        Get list of users that the specified FID is following
        
        Args:
            fid: The Farcaster ID to get following list for
            
        Returns:
            List of user dictionaries with FID, username, display_name, etc.
        """
        try:
            url = f"{self.base_url}/following/"
            all_users = []
            cursor = None
            page_count = 0
            
            logger.info(f"Fetching following list for FID {fid}")
            
            while True:
                params = {
                    "fid": fid,
                    "limit": 100  # Maximum allowed by API
                }
                
                if cursor:
                    params["cursor"] = cursor
                
                response = requests.get(url, headers=self.headers, params=params)
                response.raise_for_status()
                
                data = response.json()
                users_data = data.get("users", [])
                
                # Extract user information from the nested structure
                for user_item in users_data:
                    if "user" in user_item:
                        user = user_item["user"]
                        all_users.append({
                            "fid": user.get("fid"),
                            "username": user.get("username", ""),
                            "display_name": user.get("display_name", ""),
                            "pfp_url": user.get("pfp_url", ""),
                            "custody_address": user.get("custody_address", "")
                        })
                
                page_count += 1
                logger.info(f"Fetched page {page_count}: {len(users_data)} users")
                
                # Check if there are more pages
                next_cursor = data.get("next", {}).get("cursor")
                if not next_cursor:
                    break
                
                cursor = next_cursor
                time.sleep(0.1)  # Small delay between requests
            
            logger.info(f"Found {len(all_users)} total users being followed")
            return all_users
            
        except requests.RequestException as e:
            logger.error(f"Error fetching following list: {e}")
            raise
    
    def unfollow_user(self, target_fid: int, dry_run: bool = False) -> bool:
        """
        Unfollow a user by their FID
        
        Args:
            target_fid: The FID of the user to unfollow
            dry_run: If True, don't actually perform the unfollow action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would unfollow user with FID {target_fid}")
                return True
            
            url = f"{self.base_url}/user/follow"
            payload = {
                "signer_uuid": self.signer_uuid,
                "target_fids": [target_fid]
            }
            
            logger.info(f"Unfollowing user with FID {target_fid}")
            response = requests.delete(url, headers=self.headers, json=payload)
            
            # Check if not following (common API responses)
            if response.status_code in [400, 409]:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', '').lower()
                    if 'not following' in error_message or 'not followed' in error_message:
                        logger.info(f"Not following user with FID {target_fid}")
                        return True
                except:
                    pass
            
            response.raise_for_status()
            
            logger.info(f"Successfully unfollowed user with FID {target_fid}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error unfollowing user {target_fid}: {e}")
            return False
    
    def follow_user(self, target_fid: int, dry_run: bool = False) -> bool:
        """
        Follow a user by their FID
        
        Args:
            target_fid: The FID of the user to follow
            dry_run: If True, don't actually perform the follow action
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if dry_run:
                logger.info(f"[DRY RUN] Would follow user with FID {target_fid}")
                return True
            
            url = f"{self.base_url}/user/follow"
            payload = {
                "signer_uuid": self.signer_uuid,
                "target_fids": [target_fid]
            }
            
            logger.info(f"Following user with FID {target_fid}")
            response = requests.post(url, headers=self.headers, json=payload)
            
            # Check if already following (common API responses)
            if response.status_code in [400, 409]:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', '').lower()
                    if 'already following' in error_message or 'already followed' in error_message:
                        logger.info(f"Already following user with FID {target_fid}")
                        return True
                except:
                    pass
            
            response.raise_for_status()
            
            logger.info(f"Successfully followed user with FID {target_fid}")
            return True
            
        except requests.RequestException as e:
            logger.error(f"Error following user {target_fid}: {e}")
            return False
    
    def get_user_info(self, fid: int) -> Optional[Dict]:
        """
        Get user information by FID
        
        Args:
            fid: The Farcaster ID to get info for
            
        Returns:
            User information dictionary or None if not found
        """
        try:
            url = f"{self.base_url}/user"
            params = {"fid": fid}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json().get("user")
            
        except requests.RequestException as e:
            logger.error(f"Error fetching user info for FID {fid}: {e}")
            return None
    
    def get_my_fid(self) -> Optional[int]:
        """
        Get the FID of the authenticated user
        
        Returns:
            FID as integer or None if not found
        """
        try:
            url = f"{self.base_url}/signer/"
            params = {"signer_uuid": self.signer_uuid}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            signer_data = response.json()
            if signer_data and "fid" in signer_data:
                return signer_data["fid"]
            
            return None
            
        except requests.RequestException as e:
            logger.error(f"Error fetching my FID: {e}")
            return None 