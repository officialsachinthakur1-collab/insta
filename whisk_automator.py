import os
import sys
import time
import shutil
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv

load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

REFERENCE_IMAGE_PATH = os.getenv("REFERENCE_IMAGE_PATH", "reference_image.jpg")
STATE_FILE = "whisk_state.json"
IS_HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"


def generate_images(prompts: list, output_prefix: str = "generated_daily_post"):
    """
    Automates Whisk AI to generate multiple images by looping over a list of prompts.
    Uses the double-generation trick for maximum face accuracy per prompt.
    """
    print(f"Starting Whisk AI Automation for {len(prompts)} prompts...")
    
    if not os.path.exists(REFERENCE_IMAGE_PATH):
        print(f"[ERROR] Reference image not found: {REFERENCE_IMAGE_PATH}")
        return []

    abs_ref_image = os.path.abspath(REFERENCE_IMAGE_PATH)
    abs_output_prefix = os.path.abspath(output_prefix)

    saved_images = []

    with sync_playwright() as p:
        chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        if not os.path.exists(chrome_path):
            chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        user_data_dir = os.path.join(os.getcwd(), "chrome_profile")

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
            return _fallback_all(abs_ref_image, abs_output_prefix, len(prompts))

        page = context.new_page()

        try:
            print("Navigating to Whisk AI...")
            page.goto("https://labs.google/fx/tools/whisk/project", timeout=60000)
            time.sleep(6)

            # ── Dismiss popup if present ────────────────────────────────────────
            try:
                close_btns = page.locator("button:has-text('CLOSE'), button:has-text('Close')").all()
                for btn in close_btns:
                    if btn.is_visible():
                        btn.click()
                        print("Dismissed popup.")
                        time.sleep(1)
                        break
            except Exception:
                pass

            # ── Check if logged in ──────────────────────────────────────────────
            if "google.com/signin" in page.url or "accounts.google.com" in page.url:
                print("[WARNING] Not logged in to Google. Please log in manually.")
                while "google.com/signin" in page.url or "accounts.google.com" in page.url:
                    time.sleep(3)
                print("Login detected! Continuing...")
                time.sleep(5)

            # ── Upload face (Subject slot) ──────────────────────────────────────
            print(f"Uploading reference face image: {abs_ref_image}")
            page.locator("button:has-text('ADD IMAGES')").click()
            time.sleep(2)

            face_uploaded = False
            try:
                file_inputs = page.locator("input[type='file'][accept='image/*']").all()
                if file_inputs:
                    file_inputs[0].set_input_files(abs_ref_image)
                    print("Face image uploaded to SUBJECT slot via file input!")
                    face_uploaded = True
                    time.sleep(3)
                else:
                    print("[WARNING] No file inputs found after ADD IMAGES click.")
            except Exception as e:
                print(f"[WARNING] Direct file input failed: {e}")

            if not face_uploaded:
                try:
                    with page.expect_file_chooser(timeout=8000) as fc_info:
                        page.locator("button:has-text('control_point')").first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_ref_image)
                    print("Face uploaded via control_point button!")
                    time.sleep(3)
                except Exception as e2:
                    print(f"[WARNING] All face upload attempts failed: {e2}. Proceeding without face reference.")

            # ── Wait for face analysis ──────────────────────────────────────────
            print("Waiting for Whisk to analyze the face image...")
            for i in range(30):
                time.sleep(1)
                try:
                    page_text = page.locator("body").inner_text()
                    if "analyzing image" not in page_text.lower():
                        print(f"Image analysis complete! ({i+1}s)")
                        break
                    if i % 5 == 0:
                        print(f"  Still analyzing... ({i+1}s)")
                except Exception:
                    pass
            time.sleep(15)  # Buffer after analysis

            def click_generate():
                page.evaluate("""
                    () => {
                        const btns = document.querySelectorAll('button');
                        for (const b of btns) {
                            if (b.innerText && b.innerText.includes('arrow_forward')) {
                                b.click(); return;
                            }
                        }
                        for (const b of btns) {
                            if (b.innerText && (b.innerText.toLowerCase().includes('generate') || b.innerText.toLowerCase().includes('submit'))) {
                                b.click(); return;
                            }
                        }
                    }
                """)

            # ── Iterate over all 3 prompts ─────────────────────────────────────
            for idx, prompt_text in enumerate(prompts):
                print(f"\n---> Generating Image {idx + 1} of {len(prompts)} <---")
                
                # Enter prompt
                print("Entering prompt...")
                prompt_box = page.locator("textarea, input[type='text'], [contenteditable='true']").first
                prompt_box.click(force=True)
                time.sleep(0.5)
                # Select all and delete previous prompt
                page.keyboard.press("Control+A")
                page.keyboard.press("Backspace")
                time.sleep(0.5)
                # clear robustly via JS
                page.evaluate("() => { const el = document.querySelector('textarea, input[type=\"text\"], [contenteditable=\"true\"]'); if(el) { if(el.value !== undefined) el.value = ''; else el.innerText = ''; } }")
                time.sleep(0.5)
                prompt_box.fill(prompt_text)
                time.sleep(1)

                # Set aspect ratio (only needed on the first prompt)
                if idx == 0:
                    print("Setting aspect ratio to 9:16 PORTRAIT...")
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
                    time.sleep(1)
                    try:
                        page.locator("text=9:16").click()
                        print("9:16 PORTRAIT selected!")
                    except Exception:
                        try:
                            page.locator("text=PORTRAIT").click()
                            print("PORTRAIT selected!")
                        except Exception:
                            pass
                    time.sleep(1)

                # Record blob count before generation
                imgs_before = page.locator("img[src^='blob:']").all()
                blobs_before = [img.get_attribute("src") for img in imgs_before if (img.get_attribute("src") or "").startswith("blob:")]

                # ── Click Generate (First Pass) ────────────────────────────────────
                print(f"Clicking Generate (First pass for Prompt {idx+1})...")
                click_generate()
                time.sleep(2)
                
                print("Waiting for FIRST generation completion (up to 90s)...")
                initial_blobs_this_run = []
                for _ in range(45):
                    time.sleep(2)
                    try:
                        imgs = page.locator("img[src^='blob:']").all()
                        current_blobs = [img.get_attribute("src") for img in imgs if (img.get_attribute("src") or "").startswith("blob:")]
                        
                        new_blobs = [b for b in current_blobs if b not in blobs_before]
                        if len(new_blobs) > 0:
                            print("First generation appeared! Waiting 10s...")
                            time.sleep(10)
                            imgs = page.locator("img[src^='blob:']").all()
                            initial_blobs_this_run = [img.get_attribute("src") for img in imgs if (img.get_attribute("src") or "").startswith("blob:")]
                            break
                    except Exception:
                        pass
                
                # ── Click Generate AGAIN for accurate face match ─────────────────
                print(f"Clicking Generate a SECOND time (for Prompt {idx+1}) to refine face match...")
                click_generate()
                time.sleep(2)
                
                print("Waiting for SECOND generation completion (up to 90s)...")
                newest_blob_url = None
                for _ in range(45):
                    time.sleep(2)
                    try:
                        imgs = page.locator("img[src^='blob:']").all()
                        current_blobs = [img.get_attribute("src") for img in imgs if (img.get_attribute("src") or "").startswith("blob:")]
                        
                        new_blobs_second_run = [b for b in current_blobs if b not in initial_blobs_this_run and b not in blobs_before]
                        
                        if len(initial_blobs_this_run) > 0 and len(new_blobs_second_run) > 0:
                            print(f"Second generation for Prompt {idx+1} appeared!")
                            time.sleep(10)  # wait for all variations to settle
                            imgs = page.locator("img[src^='blob:']").all()
                            current_blobs = [img.get_attribute("src") for img in imgs if (img.get_attribute("src") or "").startswith("blob:")]
                            newest_blob_url = current_blobs[-1]
                            break
                        elif len(initial_blobs_this_run) == 0 and len(new_blobs) > 0:
                            # fallback if first run failed to register
                            time.sleep(10)
                            imgs = page.locator("img[src^='blob:']").all()
                            current_blobs = [img.get_attribute("src") for img in imgs if (img.get_attribute("src") or "").startswith("blob:")]
                            newest_blob_url = current_blobs[-1]
                            break
                    except Exception:
                        pass

                if not newest_blob_url and len(initial_blobs_this_run) > 0:
                    newest_blob_url = initial_blobs_this_run[-1]
                
                if not newest_blob_url:
                    print(f"[WARNING] Blob not found for prompt {idx+1}. Skipping.")
                    continue

                # ── Save the finalized image ──────────────────────────────────────
                print(f"Saving finalized image {idx+1} from blob URL...")
                try:
                    img_data = page.evaluate("""
                        async (blobUrl) => {
                            const res = await fetch(blobUrl);
                            const blob = await res.blob();
                            const buf = await blob.arrayBuffer();
                            return Array.from(new Uint8Array(buf));
                        }
                    """, newest_blob_url)
                    
                    current_output_path = f"{abs_output_prefix}_{idx+1}.jpg"
                    with open(current_output_path, "wb") as f:
                        f.write(bytes(img_data))
                    size_kb = os.path.getsize(current_output_path) // 1024
                    print(f"Image {idx+1} saved: {current_output_path} ({size_kb} KB)")
                    
                    if size_kb > 1:
                        # ── Ensure exactly 9:16 portrait via PIL center-crop ─────────────
                        try:
                            from PIL import Image
                            img = Image.open(current_output_path)
                            w, h = img.size
                            target_ratio = 9 / 16
                            current_ratio = w / h
                            if abs(current_ratio - target_ratio) > 0.02:
                                if current_ratio > target_ratio:
                                    new_w = int(h * target_ratio)
                                    left = (w - new_w) // 2
                                    img = img.crop((left, 0, left + new_w, h))
                                else:
                                    new_h = int(w / target_ratio)
                                    top = (h - new_h) // 2
                                    img = img.crop((0, top, w, top + new_h))
                            img = img.resize((1080, 1920), Image.LANCZOS)
                            img.save(current_output_path, "JPEG", quality=95)
                            print(f"Image {idx+1} resized to exactly 9:16 (1080x1920)!")
                        except Exception as pil_err:
                            print(f"[WARNING] PIL resize failed for image {idx+1}: {pil_err}")
                        
                        saved_images.append(current_output_path)
                except Exception as e:
                    print(f"Blob save failed for image {idx+1}: {e}")

            if not saved_images:
                return _fallback_all(abs_ref_image, abs_output_prefix, len(prompts))

            print(f"Successfully generated {len(saved_images)} heavily unique images!")
            return saved_images

        except Exception as e:
            print(f"[ERROR] Whisk automation error during multi-prompt: {e}")
            return _fallback_all(abs_ref_image, abs_output_prefix, len(prompts))

        finally:
            print("Closing browser session...")
            try:
                context.close()
            except Exception:
                pass


def _fallback_all(ref_image: str, output_prefix: str, count: int) -> list[str]:
    """Copies the reference image multiple times as a fallback."""
    print(f"[FALLBACK] Using reference image to fill {count} slots.")
    paths = []
    for i in range(count):
        pth = f"{output_prefix}_{i+1}.jpg"
        shutil.copy(ref_image, pth)
        paths.append(pth)
    return paths

if __name__ == "__main__":
    test_prompts = [
        "A cinematic portrait of a person in a neon-lit futuristic city.",
        "A person sitting at an aesthetic cafe looking sideways, coffee mug."
    ]
    result = generate_images(test_prompts, "whisk_test_multi")
    print("Final exported images:", result)
