# Farcaster Follow Manager

A command-line tool to manage your Farcaster follows. This project provides two main scripts:

1. **unfollow_all.py** - Unfollows all your Farcaster follows and logs them to a CSV file
2. **refollow_all.py** - Refollows users from the CSV file created by the unfollow script

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your Neynar API credentials:

```bash
# Copy the template
cp env_template.txt .env
# Then edit .env with your actual credentials
```

Add your credentials to the `.env` file:

```
NEYNAR_API_KEY=your_api_key_here
NEYNAR_SIGNER_UUID=your_signer_uuid_here
```

You can get these from [Neynar's dashboard](https://neynar.com/).

3. Test your connection:

```bash
python test_connection.py
```

## Usage

### Unfollow All Follows

```bash
# Basic usage
python unfollow_all.py

# Dry run (no actual unfollows)
python unfollow_all.py --dry-run

# Dry run but limit to subset of users (recommended)
python unfollow_all.py --dry-run --limit 50

# Custom delay between unfollows (default: 1 second)
python unfollow_all.py --delay 2.0

# Limit number of users to process
python unfollow_all.py --limit 500
```

This will:

- Fetch all users you're currently following
- Loop through all users, or the number of users in LIMIT
- Unfollow each user
- Log each unfollowed user to `unfollowed_users_FID_DATE.csv`

### Refollow Users

```bash
# Basic usage
python refollow_all.py

# Dry run (no actual follows)
python refollow_all.py --dry-run

# Custom delay between follows
python refollow_all.py --delay 2.0

# Resume from a specific index (useful if interrupted)
python refollow_all.py --start-from 100

# Use a different CSV file
python refollow_all.py --csv-file data/my_users.csv
```

This will:

- Read the `unfollowed_users.csv` file
- Refollow each user listed in the file

## Files

- `unfollow_all.py` - Main script to unfollow all users
- `refollow_all.py` - Main script to refollow users from CSV
- `farcaster_api.py` - API utilities for Farcaster operations
- `test_connection.py` - Test script to verify API credentials
- `env_template.txt` - Template for environment variables
- `unfollowed_users.csv` - Generated CSV file with unfollowed users (created after running unfollow script)

## Safety Features

- Both scripts include confirmation prompts before execution
- Dry-run mode available to test without making actual changes
- Rate limiting to avoid API limits
- Error handling and logging

## Notes

- The scripts use the Neynar API to interact with Farcaster
- Make sure you have the necessary API permissions
- Consider using dry-run mode first to test the functionality
- Script results are logged into a text file

# TO DO

- For refollow, make sure it doesnt break if user is already following someone (in case of manual follows)
