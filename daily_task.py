"""
Argos Daily Task Entry
Fetch -> Translate (ArgosTranslate) -> Send Email
"""
import os
import glob
import pytz
from datetime import datetime

tz_est = pytz.timezone("America/New_York")
today = datetime.now(tz_est).strftime("%Y-%m-%d")

# Step 1: Fetch articles
print("Step 1: Fetch articles from Foreign Policy Blogs...")
import rss_parser
mode = os.getenv("MODE", "normal")
rss_parser.fetch_rss(force_backfill=(mode == "backfill"))

# Step 2: Translate
print("Step 2: Translate with ArgosTranslate...")
import argos_translator

today_file = os.path.join("dailynews", today + ".md")
if not os.path.exists(today_file):
    files = sorted(glob.glob("dailynews/*.md"))
    if files:
        today_file = files[-1]
        print(f"Using latest: {today_file}")
    else:
        print("No article files found, skip translation")
        today_file = None

if today_file:
    success = argos_translator.translate_file(today_file)
    print("Translation OK" if success else "Translation FAILED")

# Step 3: Send email
print("Step 3: Send email...")
translate_path = os.path.join("translate", today + ".md")
if not os.path.exists(translate_path):
    files = sorted(glob.glob("translate/*.md"))
    if files:
        translate_path = files[-1]
        print(f"Using latest translation: {translate_path}")

if os.path.exists(translate_path):
    import send_email
    send_email.main(translate_path)
else:
    print("No translation file, skip email")

print("Daily task completed")
