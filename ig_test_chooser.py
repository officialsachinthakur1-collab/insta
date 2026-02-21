import sys
import os
import time
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')

def test_chooser():
    print("Testing Chooser...")
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
        
        try:
            page.wait_for_selector("svg[aria-label='New post']", timeout=10000)
            
            create_btn = page.locator("svg[aria-label='New post']").first
            if create_btn.is_visible():
                # click the parent since SVG might not capture the click
                page.locator("a:has(svg[aria-label='New post']), div:has(svg[aria-label='New post'])").first.click()
            else:
                page.get_by_role("link", name="New post").click()
                
            print("Clicked Create Button (New Post)")
            time.sleep(2)
            
            # Instagram now shows a dropdown: 'Post' or 'Live video'. Click Post.
            page.locator("text=Post").locator("visible=true").first.click()
            print("Clicked 'Post' from dropdown menu")
            time.sleep(3)
            
            print("Looking for dialog text...")
            time.sleep(3)
            
            print("Waiting for 'Select from computer' text...")
            page.locator("text=Select from computer").wait_for(state='visible', timeout=15000)
            print("Found text! Opening file chooser...")
            
            with page.expect_file_chooser(timeout=10000) as fc_info:
                page.locator("text=Select from computer").click()
                
            file_chooser = fc_info.value
            print(f"File Chooser Caught! Ready to set files.")
            file_chooser.set_files("reference_image.jpg")
            print("Files set successfully!")
            
            time.sleep(5)
            
        except Exception as e:
            print(f"Error: {e}")
            
        finally:
            context.close()

if __name__ == "__main__":
    test_chooser()
