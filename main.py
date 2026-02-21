import time
import schedule
from datetime import datetime
from prompt_generator import generate_prompt_and_caption
from whisk_automator import generate_image
from ig_poster import post_to_instagram

def daily_job():
    print(f"\n=== Starting Daily AI Instagram Post Automation at {datetime.now()} ===")
    
    # Step 1: Generate Prompt and Caption
    print("\n--- Step 1: Generating Prompt & Caption ---")
    prompt, caption = generate_prompt_and_caption()
    print(f"Generated Caption Preview:\n{caption[:100]}...")
    
    # Step 2: Generate Image via Whisk AI
    print("\n--- Step 2: Generating Image ---")
    output_image = "generated_daily_post.jpg"
    success = generate_image(prompt, output_image)
    
    if not success:
        print("Failed to generate image. Aborting today's post.")
        return
        
    # Step 3: Post to Instagram
    print("\n--- Step 3: Posting to Instagram ---")
    post_success = post_to_instagram(output_image, caption)
    
    if post_success:
        print("\n[SUCCESS] Daily job completed successfully!")
    else:
        print("\n[ERROR] Failed to post to Instagram. Please check the logs.")

if __name__ == "__main__":
    print("Welcome to the AI Influencer Auto-Posting System!")
    print("Do you want to run the job NOW or SCHEDULE it for daily execution?")
    choice = input("Enter '1' for NOW, '2' for SCHEDULE: ").strip()
    
    if choice == '1':
        print("\nExecuting immediately...")
        daily_job()
    elif choice == '2':
        post_time = input("Enter time to post daily (e.g., 11:30): ").strip()
        print(f"\nScheduler started. Will post every day at {post_time}")
        schedule.every().day.at(post_time).do(daily_job)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        print("Invalid choice. Exiting.")
