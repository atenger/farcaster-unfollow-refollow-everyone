@echo off
echo Farcaster Follow Manager - Refollow All
echo ======================================
echo.
echo This will refollow users from the unfollowed_users.csv file.
echo Make sure you have set up your .env file with your API credentials.
echo.
pause
python refollow_all.py
pause 