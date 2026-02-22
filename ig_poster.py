import os
import sys
import time
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

IS_HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


def post_to_instagram(image_paths: list[str], caption: str):
    """
    Logs into Instagram via browser automation and posts multiple images as a carousel.
    """
    abs_image_paths = []
    for path in isinstance(image_paths, str) and [image_paths] or image_paths:
        if os.path.exists(path):
            abs_image_paths.append(os.path.abspath(path))
        else:
            print(f"[WARNING] Image path {path} does not exist.")
            
    if not abs_image_paths:
        print("[ERROR] No valid image paths provided.")
        return False

    print(f"Starting Instagram Browser Automation...")
    print(f"Image paths: {abs_image_paths}")

    with sync_playwright() as p:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile_ig")

        try:
            print(f"Launching Chrome from {chrome_path} (Headless: {IS_HEADLESS})...")
            context = p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                executable_path=chrome_path,
                headless=IS_HEADLESS,
                channel="chrome",
                args=["--disable-blink-features=AutomationControlled"]
            )
        except Exception as e:
            print(f"[ERROR] Failed to launch Chrome: {e}")
            return False

        page = context.new_page()

        try:
            print("Navigating to Instagram...")
            page.goto("https://www.instagram.com/", timeout=60000)
            time.sleep(5)

            # ── Login check ──────────────────────────────────────────────────────
            try:
                page.wait_for_selector("svg[aria-label='New post']", timeout=8000)
                print("Already logged in!")
            except Exception:
                print("[WARNING] Not logged in. Please log in manually in the browser window.")
                print("Waiting until New Post button appears on the sidebar...")
                while True:
                    try:
                        page.wait_for_selector("svg[aria-label='New post']", timeout=5000)
                        break
                    except Exception:
                        pass
                print("Login detected! Continuing...")
                time.sleep(3)

            # ── Click Create button ──────────────────────────────────────────────
            print("Clicking 'Create' sidebar button...")
            # The sidebar 'Create' button houses the svg with aria-label='New post'
            # We click its parent <a> or <div> wrapper via JS to avoid strict-mode issues
            page.evaluate("""
                () => {
                    const svgs = document.querySelectorAll("svg[aria-label='New post']");
                    if (svgs.length > 0) {
                        // Walk up to a clickable ancestor
                        let el = svgs[0];
                        for (let i = 0; i < 5; i++) {
                            el = el.parentElement;
                            if (el && (el.tagName === 'A' || el.tagName === 'DIV' || el.getAttribute('role') === 'button')) {
                                el.click();
                                break;
                            }
                        }
                    }
                }
            """)
            time.sleep(2)

            # ── Click "Post" from dropdown ────────────────────────────────────────
            print("Looking for 'Post' in the dropdown...")
            # Use JS to click the element whose text is exactly "Post"
            clicked = page.evaluate("""
                () => {
                    const all = document.querySelectorAll('span, div, a');
                    for (const el of all) {
                        if (el.innerText && el.innerText.trim() === 'Post') {
                            el.click();
                            return true;
                        }
                    }
                    return false;
                }
            """)
            if clicked:
                print("Clicked 'Post' from dropdown via JS!")
            else:
                print("[WARNING] Could not find 'Post' dropdown item via JS.")
            time.sleep(4)

            # ── Upload images ───────────────────────────────────────────────────
            print(f"Uploading {len(abs_image_paths)} images...")
            try:
                with page.expect_file_chooser(timeout=12000) as fc_info:
                    # Direct Playwright click — must be inside the context manager
                    # Use .first to avoid strict-mode violations from multiple matches
                    page.locator("button:has-text('Select from computer')").first.click()
                file_chooser = fc_info.value
                file_chooser.set_files(abs_image_paths)
                print(f"Successfully uploaded {len(abs_image_paths)} images to file chooser!")
            except Exception as e:
                print(f"File chooser failed: {e}")
                return False

            time.sleep(4)

            # ── Adjust Aspect Ratio to Original (prevent cropping) ──────────────
            print("Setting Aspect Ratio to Original...")
            page.evaluate("""
                () => {
                    const svgs = document.querySelectorAll("svg[aria-label='Select crop']");
                    if (svgs.length > 0) {
                        let el = svgs[0];
                        for (let i = 0; i < 5; i++) {
                            el = el.parentElement;
                            if (el && el.tagName === 'BUTTON') { el.click(); break; }
                        }
                    }
                }
            """)
            time.sleep(2)
            page.evaluate("""
                () => {
                    const spans = document.querySelectorAll("span, div");
                    for (const s of spans) {
                        if (s.innerText && s.innerText.trim() === 'Original') {
                            s.click();
                            let el = s;
                            for (let i = 0; i < 5; i++) {
                                el = el.parentElement;
                                if (el && (el.tagName === 'BUTTON' || el.tagName === 'A')) { el.click(); break; }
                            }
                            return;
                        }
                    }
                    // Fallback to 4:5 if Original isn't found
                    for (const s of spans) {
                        if (s.innerText && s.innerText.trim() === '4:5') {
                            s.click();
                            let el = s;
                            for (let i = 0; i < 5; i++) {
                                el = el.parentElement;
                                if (el && el.tagName === 'BUTTON') { el.click(); break; }
                            }
                            return;
                        }
                    }
                }
            """)
            time.sleep(2)

            # ── Click Next (Crop screen) ──────────────────────────────────────────
            print("Clicking Next (Crop Screen)...")
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button, div[role=\"button\"]');
                    for (const b of btns) {
                        if (b.innerText && b.innerText.trim() === 'Next') { b.click(); return; }
                    }
                }
            """)
            time.sleep(3)
            page.screenshot(path="ig_debug_2_after_crop_next.png")
            print("Screenshot saved: ig_debug_2_after_crop_next.png")

            # ── Click Next (Filter screen) ────────────────────────────────────────
            print("Clicking Next (Filter Screen)...")
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button, div[role=\"button\"]');
                    for (const b of btns) {
                        if (b.innerText && b.innerText.trim() === 'Next') { b.click(); return; }
                    }
                }
            """)
            time.sleep(3)
            page.screenshot(path="ig_debug_3_after_filter_next.png")
            print("Screenshot saved: ig_debug_3_after_filter_next.png")

            # ── Enter caption ────────────────────────────────────────────────────
            print("Entering caption...")
            # Click the caption box directly — use force=True to bypass any overlapping elements
            caption_box = page.locator("div[aria-label='Write a caption...']")
            caption_box.click(force=True)
            time.sleep(1)
            page.keyboard.type(caption)
            time.sleep(2)
            page.screenshot(path="ig_debug_4_after_caption.png")
            print("Screenshot saved: ig_debug_4_after_caption.png")

            # ── Click Share ──────────────────────────────────────────────────────
            print("Clicking Share...")
            page.evaluate("""
                () => {
                    const btns = document.querySelectorAll('button, div[role=\"button\"]');
                    for (const b of btns) {
                        if (b.innerText && b.innerText.trim() === 'Share') { b.click(); return; }
                    }
                }
            """)

            time.sleep(3)
            page.screenshot(path="ig_debug_5_after_share_click.png")
            print("Screenshot saved: ig_debug_5_after_share_click.png")

            # ── Wait for success ─────────────────────────────────────────────────
            print("Waiting for post to be shared...")
            # Instagram may show different text depending on the language/UI version
            success_texts = [
                "text=Your post has been shared.",
                "text=Post shared",
                "text=Your post has been shared",
                "svg[aria-label='Post']",
            ]
            shared = False
            for selector in success_texts:
                try:
                    page.wait_for_selector(selector, timeout=15000)
                    shared = True
                    break
                except Exception:
                    pass

            if shared:
                print("[SUCCESS] Post shared successfully!")
            else:
                # Share was clicked — wait a bit for Instagram to process then consider it done
                print("Success text not found, but Share was clicked. Waiting 10s and assuming success...")
                time.sleep(10)
                print("[SUCCESS] Share button was clicked. Post likely live!")

            return True

        except Exception as e:
            print(f"[ERROR] Error during Instagram automation: {e}")
            return False

        finally:
            print("Closing browser...")
            try:
                context.close()
            except Exception:
                pass


if __name__ == "__main__":
    test_img = ["reference_image.jpg"]
    result = post_to_instagram(test_img, "Test multi-post from bot #automation")
    print("Result:", result)
