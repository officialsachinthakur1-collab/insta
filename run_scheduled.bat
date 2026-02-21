@echo off
:: Run the bot NOW without any user prompt (for Task Scheduler)
cd /d "C:\Users\sachi\OneDrive\Desktop\Automation\Insta_AI_Bot"
echo 1 | python main.py >> bot_log.txt 2>&1
