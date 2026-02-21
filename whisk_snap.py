import os, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')

with sync_playwright() as p:
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = os.path.join(os.getcwd(), "chrome_profile")
    context = p.chromium.launch_persistent_context(
        user_data_dir=user_data_dir,
        executable_path=chrome_path,
        headless=False,
        channel="chrome",
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = context.new_page()
    page.goto("https://labs.google/fx/tools/whisk/project", timeout=60000)
    time.sleep(6)
    
    # Dismiss popup
    try:
        for btn in page.locator("button:has-text('CLOSE')").all():
            if btn.is_visible():
                btn.click(); time.sleep(1); break
    except: pass

    # Click aspect_ratio button
    print("Clicking aspect_ratio button...")
    page.evaluate("""
        () => {
            const btns = document.querySelectorAll('button');
            for (const b of btns) {
                if (b.innerText && b.innerText.includes('aspect_ratio')) {
                    b.click(); return;
                }
            }
        }
    """)
    time.sleep(2)
    page.screenshot(path="whisk_aspect_ratio.png")
    print("Screenshot: whisk_aspect_ratio.png")
    
    # Print all visible text/buttons in the ratio picker
    print("\n--- Visible text after clicking aspect_ratio ---")
    print(page.locator("body").inner_text()[:1000])
    
    context.close()
