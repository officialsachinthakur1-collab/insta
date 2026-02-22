import time
import schedule
from datetime import datetime
from prompt_generator import generate_prompt_and_caption
from whisk_automator import generate_images
from ig_poster import post_to_instagram

def daily_job():
    print(f"\n=== Starting Daily AI Instagram Post Automation at {datetime.now()} ===")
    
    # Step 1: Generate Prompts and Caption
    print("\n--- Step 1: Generating Prompts & Caption ---")
    prompts, caption = generate_prompt_and_caption()
    print(f"Generated Caption Preview:\n{caption[:100]}...")
    print(f"Generated {len(prompts)} unique prompts for today's carousel.")
    
    # Step 2: Generate Images via Whisk AI
    print("\n--- Step 2: Generating Images ---")
    output_prefix = "generated_daily_post"
    saved_images = generate_images(prompts, output_prefix)
    
    if not saved_images:
        print("Failed to generate images. Aborting today's post.")
        return
        
    # Step 3: Post to Instagram
    print("\n--- Step 3: Posting to Instagram ---")
    post_success = post_to_instagram(saved_images, caption)
    
    if post_success:
        print("\n[SUCCESS] Daily job completed successfully!")
    else:
        print("\n[ERROR] Failed to post to Instagram. Please check the logs.")

import sys
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Influencer Auto-Posting System")
    parser.add_argument("--now", action="store_true", help="Run the job immediately")
    parser.add_argument("--schedule", type=str, help="Schedule the job daily at HH:MM (e.g. 11:30)")
    args = parser.parse_args()

    if args.now:
        print("\nExecuting immediately via command line...")
        daily_job()
    elif args.schedule:
        print(f"\nScheduler started. Will post every day at {args.schedule}")
        schedule.every().day.at(args.schedule).do(daily_job)
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
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
