import os
import time
from playwright.sync_api import sync_playwright

def grab_screenshot():
    print("Starting screenshot grabber...")
    with sync_playwright() as p:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile_ig")
        
        context = p.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            executable_path=chrome_path,
            headless=False,
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"]
        )
            
        page = context.new_page()
        page.goto("https://www.instagram.com/", timeout=60000)
        time.sleep(8)
        
        # Click new post
        create_btn = page.locator("svg[aria-label='New post']").first
        if create_btn.is_visible():
             create_btn.click()
        else:
             page.get_by_role("link", name="New post").click()
             
        time.sleep(3)
        page.screenshot(path="ig_modal_debug.png")
        print("Screenshot saved to ig_modal_debug.png")
        
        # Dump HTML
        with open("ig_modal_dump.html", "w", encoding="utf-8") as f:
            f.write(page.content())
            
        context.close()

if __name__ == "__main__":
    grab_screenshot()
