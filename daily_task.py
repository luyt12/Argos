"""
Argos Daily Task - Fetch, Translate, Send
"""
import os
import glob
import pytz
from datetime import datetime

tz_est = pytz.timezone("America/New_York")
today = datetime.now(tz_est).strftime("%Y-%m-%d")

print("=" * 50)
print(f"Argos Daily Task - {today}")
print("=" * 50)

# Step 1: Fetch articles
print("\n[1/3] Fetching articles...")
import rss_parser
links = rss_parser.fetch_rss()
if not links:
    print("No new articles, exiting")
    exit(0)

# Step 2: Translate
print("\n[2/3] Translating...")
import argos_translator

today_file = os.path.join("dailynews", today + ".md")
if not os.path.exists(today_file):
    files = sorted(glob.glob("dailynews/*.md"))
    if files:
        today_file = files[-1]
        print(f"Using latest: {today_file}")

if os.path.exists(today_file):
    success = argos_translator.translate_file(today_file)
    print("Translation " + ("OK" if success else "FAILED"))
else:
    print("No article file found")
    exit(1)

# Step 3: Send email
print("\n[3/3] Sending email...")
translate_path = os.path.join("translate", today + ".md")
if not os.path.exists(translate_path):
    files = sorted(glob.glob("translate/*.md"))
    if files:
        translate_path = files[-1]

if os.path.exists(translate_path):
    import send_email
    send_email.main(translate_path)
else:
    print("No translation file")
    exit(1)

print("\n" + "=" * 50)
print("Daily task completed!")
print("=" * 50)