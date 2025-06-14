# Script to clean notion, get correct image size and upload to notion


from datetime import datetime
import subprocess

subprocess.run(["python3", "src/Notion/0_remove_all_Notion.py"], check=True)



# List of dates
dates = [
    #"06_04_2025",
    #"06_05_2025",  # Add more here later!
    #"06_12_2025"
]
date = datetime.now().strftime("%m_%d_%Y")
#date = "06_12_2025"


# for date in dates:
# Build your filename for each date
# file_name = f"Output_Market_{date}/fear_and_greed_index_{date}.png"
# print("Processing chart:", file_name)
# subprocess.run(["python3", "src/Notion/1_resize_image.py", file_name], check=True)


subprocess.run(["python3", "src/Notion/2_upload_newsletter_Notion.py"], check=True)

subprocess.run(["python3", "src/Notion/2_upload_newsletter_Notion_v2.py"], check=True)