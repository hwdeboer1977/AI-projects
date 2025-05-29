import subprocess

def run_scripts(title, script_list):
    print(f"\n {title}...\n")
    for script in script_list:
        print(f"Running: {script}")
        result = subprocess.run(["python3", script], capture_output=True, text=True)
        if result.returncode != 0:
            print(f" Error in {script}:\n{result.stderr}")
            break
        else:
            print(f"Success: {script}\n{result.stdout}")
    print("All scripts completed for this section.\n")

# STEP 1: Scrape News Articles
run_scripts("Running News Article Scrapers", [
#     "src/Scraping/Bankless.py",   # Only few or no articles in 24hrs and scraping stopped working?
#     "src/Scraping/BeInCrypto.py", # 29-5-2025: Script is not scraping the articles anymore
#     "src/Scraping/Blockworks.py",
#     "src/Scraping/Coindesk.py",
#     "src/Scraping/Cointelegraph.py",
#     "src/Scraping/Decrypt.py",
#     "src/Scraping/Defiant.py", # 28-5-2025: Defiant added bot protection
#     "src/Scraping/Theblock.py" # Script is working but only with my own free, limited ScraperAPI
])

# # STEP 2: Scrape Twitter
# run_scripts("Running Twitter Scrapers", [
#    "src/Scraping/Twitter_agent_news.py",
#    "src/Scraping/Twitter_agent.py"
# ])

# STEP 3a: Market Colour Section
# run_scripts("Running Market Colour Pipeline", [
#     "src/Market/1_getPriceBTC_Chainlink.py",
#     "src/Market/2_SosoValueETHFlows.py",
#     "src/Market/3_fear_and_greed.py",
#     "src/Market/4_merge_market_info.py",
#     "src/Market/5_create_market_colour_text.py"
# ])

# # STEP 3b: Articles Section (top 10 Articles summaries)
# run_scripts("Running Article Newsletter Pipeline", [
#     "src/Articles_Summarize/1_summarize_agent.py",
#     "src/Articles_Summarize/2_overlap_agent.py",
#     "src/Articles_Summarize/3_twitter_engagement.py",
#     "src/Articles_Summarize/4_generate_JSON_newsletter.py",
#     "src/Articles_Summarize/5_generate_MD_newsletter.py",
#     "src/Articles_Summarize/6_convert_to_PDF_newsletter.py"
# ])

# STEP 3c: Twitter Section (top 10 Tweets)
# run_scripts("Running Twitter Newsletter Pipeline", [
#     "src/Twitter_summarize/1_aggregate_twitter.py",
#     "src/Twitter_summarize/2_select_twitter.py",
#     "src/Twitter_summarize/3_save_content_newsletter.py",
#     "src/Twitter_summarize/4_render_clean_JSON_newsletter.py",
#     "src/Twitter_summarize/5_render_HTML_newsletter.py",
#     "src/Twitter_summarize/6_render_MD_newsletter.py"
# ])

# # STEP 4: Create Final Newsletter in different Formats
# run_scripts("Rendering Final Newsletter Formats", [
#     "src/1_create_newsletter_JSON.py",
#     "src/2_create_newsletter_MD.py",
#     "src/3_create_newsletter_HTML.py"
# ])
