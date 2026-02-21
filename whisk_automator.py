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


def generate_image(prompt: str, output_path: str = "generated_daily_post.jpg"):
    """
    Automates Whisk AI to generate an image based on the prompt.
    Falls back to using the reference image if Whisk automation fails.
    """
    print("Starting Whisk AI Automation...")
    
    if not os.path.exists(REFERENCE_IMAGE_PATH):
        print(f"[ERROR] Reference image not found: {REFERENCE_IMAGE_PATH}")
        return False

    abs_ref_image = os.path.abspath(REFERENCE_IMAGE_PATH)
    abs_output_path = os.path.abspath(output_path)

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
            return _fallback(abs_ref_image, abs_output_path)

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

            # ── Expand upload panel and upload face (Subject slot) ───────────────
            print(f"Uploading reference face image: {abs_ref_image}")

            # Step 1: Click ADD IMAGES to expand the SUBJECT/SCENE/STYLE panel
            page.locator("button:has-text('ADD IMAGES')").click()
            time.sleep(2)

            # Step 2: After ADD IMAGES is clicked, 3 file inputs appear (image/*)
            # The first one is SUBJECT (face reference)
            # Use set_input_files directly — no need to wait for file chooser dialog
            face_uploaded = False
            try:
                file_inputs = page.locator("input[type='file'][accept='image/*']").all()
                if file_inputs:
                    # First input = SUBJECT slot (face)
                    file_inputs[0].set_input_files(abs_ref_image)
                    print("Face image uploaded to SUBJECT slot via file input!")
                    face_uploaded = True
                    time.sleep(3)
                else:
                    print("[WARNING] No file inputs found after ADD IMAGES click.")
            except Exception as e:
                print(f"[WARNING] Direct file input failed: {e}")

            if not face_uploaded:
                # Fallback: try clicking the + (control_point) button for SUBJECT
                try:
                    with page.expect_file_chooser(timeout=8000) as fc_info:
                        # Click the first + circle button (Subject slot)
                        page.locator("button:has-text('control_point')").first.click()
                    file_chooser = fc_info.value
                    file_chooser.set_files(abs_ref_image)
                    print("Face uploaded via control_point button!")
                    time.sleep(3)
                except Exception as e2:
                    print(f"[WARNING] All face upload attempts failed: {e2}. Proceeding without face reference.")



            # ── Wait for Whisk to finish analyzing the uploaded face image ────────
            print("Waiting for Whisk to analyze the face image...")
            for i in range(30):  # Wait up to 30 seconds
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
            time.sleep(2)  # Extra buffer after analysis

            # ── Enter the text prompt ───────────────────────────────────────────
            print("Entering prompt...")
            prompt_box = page.locator("textarea, input[type='text'], [contenteditable='true']").first
            prompt_box.click(force=True)
            time.sleep(0.5)
            prompt_box.fill(prompt)
            time.sleep(1)

            # ── Set 9:16 PORTRAIT aspect ratio ─────────────────────────────────
            print("Setting aspect ratio to 9:16 PORTRAIT...")
            # Click the aspect_ratio button to open the picker
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
            # Click '9:16' PORTRAIT option
            try:
                page.locator("text=9:16").click()
                print("9:16 PORTRAIT selected!")
            except Exception:
                try:
                    page.locator("text=PORTRAIT").click()
                    print("PORTRAIT selected!")
                except Exception as e:
                    print(f"[WARNING] Could not set aspect ratio: {e}")
            time.sleep(1)

            # ── Click Generate (arrow_forward button) ──────────────────────────
            print("Clicking Generate...")
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
            time.sleep(2)

            # ── Wait for generation to complete ────────────────────────────────
            print("Waiting for image generation (up to 90 seconds)...")
            result_blob_url = None

            for _ in range(45):  # Check every 2s for up to 90s
                time.sleep(2)
                try:
                    # Find blob images that have no alt text (generated results)
                    # The uploaded subject image has alt='Uploaded Image', result ones have alt=''
                    imgs = page.locator("img[src^='blob:']").all()
                    for img in imgs:
                        alt = img.get_attribute("alt") or ""
                        src = img.get_attribute("src") or ""
                        # Skip the uploaded reference image
                        if alt == "" and src.startswith("blob:"):
                            result_blob_url = src
                            break
                    if result_blob_url:
                        break
                except Exception:
                    pass

            if not result_blob_url:
                print("[WARNING] Generation timed out. Falling back to reference image.")
                return _fallback(abs_ref_image, abs_output_path)

            # ── Save the generated image via JS blob fetch ─────────────────────
            print(f"Saving generated image from blob URL...")
            try:
                img_data = page.evaluate("""
                    async (blobUrl) => {
                        const res = await fetch(blobUrl);
                        const blob = await res.blob();
                        const buf = await blob.arrayBuffer();
                        return Array.from(new Uint8Array(buf));
                    }
                """, result_blob_url)
                with open(abs_output_path, "wb") as f:
                    f.write(bytes(img_data))
                size_kb = os.path.getsize(abs_output_path) // 1024
                print(f"Image saved: {abs_output_path} ({size_kb} KB)")
                if size_kb < 1:
                    print("[WARNING] Saved image is too small. Falling back.")
                    return _fallback(abs_ref_image, abs_output_path)

                # ── Ensure exactly 9:16 portrait via PIL center-crop ─────────────
                try:
                    from PIL import Image
                    img = Image.open(abs_output_path)
                    w, h = img.size
                    target_ratio = 9 / 16
                    current_ratio = w / h
                    if abs(current_ratio - target_ratio) > 0.02:  # Not already 9:16
                        if current_ratio > target_ratio:
                            # Too wide → crop left/right
                            new_w = int(h * target_ratio)
                            left = (w - new_w) // 2
                            img = img.crop((left, 0, left + new_w, h))
                        else:
                            # Too tall → crop top/bottom
                            new_h = int(w / target_ratio)
                            top = (h - new_h) // 2
                            img = img.crop((0, top, w, top + new_h))
                    # Resize to Instagram portrait standard 1080x1920
                    img = img.resize((1080, 1920), Image.LANCZOS)
                    img.save(abs_output_path, "JPEG", quality=95)
                    print(f"Image resized to 9:16 (1080x1920) portrait!")
                except Exception as pil_err:
                    print(f"[WARNING] PIL resize failed (image still saved): {pil_err}")

            except Exception as e:
                print(f"Blob save failed: {e}. Using fallback.")
                return _fallback(abs_ref_image, abs_output_path)

                return _fallback(abs_ref_image, abs_output_path)

            print(f"Image ready at: {abs_output_path}")
            return True

        except Exception as e:
            print(f"[ERROR] Whisk automation error: {e}")
            return _fallback(abs_ref_image, abs_output_path)

        finally:
            print("Closing browser session...")
            try:
                context.close()
            except Exception:
                pass


def _fallback(ref_image: str, output_path: str) -> bool:
    """Copies the reference image as a fallback when Whisk generation fails."""
    print(f"[FALLBACK] Using reference image as output: {output_path}")
    shutil.copy(ref_image, output_path)
    return True


if __name__ == "__main__":
    test_prompt = "A beautiful young woman in a trendy outfit standing in a sunny city street, golden hour lighting, cinematic, hyper-realistic"
    result = generate_image(test_prompt, "whisk_test_output.jpg")
    print("Result:", result)
