import os, sys, time
from playwright.sync_api import sync_playwright
sys.stdout.reconfigure(encoding='utf-8')

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

    # Click Create via JS
    page.evaluate("""
        () => {
            const svgs = document.querySelectorAll("svg[aria-label='New post']");
            if (svgs.length > 0) {
                let el = svgs[0];
                for (let i = 0; i < 5; i++) {
                    el = el.parentElement;
                    if (el && (el.tagName === 'A' || el.tagName === 'DIV' || el.getAttribute('role') === 'button')) {
                        el.click(); break;
                    }
                }
            }
        }
    """)
    time.sleep(2)

    # Click Post via JS
    page.evaluate("""
        () => {
            const all = document.querySelectorAll('span, div, a');
            for (const el of all) {
                if (el.innerText && el.innerText.trim() === 'Post') { el.click(); return; }
            }
        }
    """)
    
    # Wait for the modal to appear
    time.sleep(4)
    
    # Screenshot the modal
    page.screenshot(path="ig_upload_modal.png")
    print("Saved screenshot to ig_upload_modal.png")
    
    # Dump visible text
    with open("ig_modal_text.txt", "w", encoding="utf-8") as f:
        f.write(page.locator("body").inner_text())
    print("Saved modal text to ig_modal_text.txt")
    
    context.close()
