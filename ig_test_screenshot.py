import os
import time
from playwright.sync_api import sync_playwright

def test_screenshot():
    print("Capturing state...")
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
        time.sleep(5)
        
        print("Clicking Create Link...")
        # Use exact name matcher for the sidebar link
        page.get_by_role("link", name="New post").click()
        time.sleep(2)
        
        print("Clicking Post from dropdown...")
        page.get_by_role("link", name="Post", exact=True).click()
        time.sleep(3) # Wait for modal to render
            
        print("Taking a picture of the upload modal...")
        # Take a picture of what happened
        page.screenshot(path="ig_modal_state.png")
        print("Saved visual state to ig_modal_state.png")
        context.close()

if __name__ == "__main__":
    test_screenshot()
