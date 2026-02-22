@echo off
TITLE AI Influencer Daily Poster
cd /d "%~dp0"

echo -----------------------------------------------------
echo Starting AI Influencer Instagram Bot (Scheduled Mode)
echo -----------------------------------------------------

:: This will run the bot continuously in the background and auto-post every day at 11:30 AM
python main.py --schedule 11:30

pause
