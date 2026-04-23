"""
Foreign Policy Blogs Email Sender
"""
import os
import sys
import re
import ssl
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

EMAIL_TO   = os.getenv("EMAIL_TO")   or ""
EMAIL_FROM = os.getenv("EMAIL_FROM") or ""
SMTP_HOST  = os.getenv("SMTP_HOST")  or ""
SMTP_PORT  = int(os.getenv("SMTP_PORT") or "465")
SMTP_USER  = os.getenv("SMTP_USER")  or ""
SMTP_PASS  = os.getenv("SMTP_PASS")  or ""

_missing = [k for k, v in {
    "EMAIL_TO": EMAIL_TO, "EMAIL_FROM": EMAIL_FROM,
    "SMTP_HOST": SMTP_HOST, "SMTP_USER": SMTP_USER, "SMTP_PASS": SMTP_PASS
}.items() if not v]
if _missing:
    print("ERROR: Missing env vars: " + ", ".join(_missing))
    sys.exit(1)

TRANSLATE_DIR = "translate"
BRAND_COLOR = "#8B0000"  # FP red


def format_html(content, date_str):
    try:
        import markdown
        html_body = markdown.markdown(content, extensions=["tables", "fenced_code"])
    except Exception:
        import html
        html_body = "<pre>" + html.escape(content) + "</pre>"

    try:
        date_fmt = datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y年%m月%d日")
    except Exception:
        date_fmt = date_str

    html = (
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">" +
        "<style>" +
        "body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,serif;"
        "line-height:1.8;color:#222;max-width:800px;margin:0 auto;padding:20px;"
        "background:#f5f5f0}" +
        ".container{background:#fff;padding:30px;border-radius:6px;"
        "box-shadow:0 2px 10px rgba(0,0,0,0.08)}" +
        ".header{border-bottom:2px solid " + BRAND_COLOR + ";"
        "padding-bottom:15px;margin-bottom:25px}" +
        "h1{color:" + BRAND_COLOR + ";margin:0;font-size:24px;font-family:Georgia,serif}" +
        ".date{color:#777;font-size:13px;margin-top:6px}" +
        "h2{color:#111;font-size:17px;border-top:1px solid #ddd;"
        "padding-top:18px;margin-top:25px;font-family:Georgia,serif}" +
        "a{color:#0066cc;text-decoration:none}" +
        "a:hover{text-decoration:underline}" +
        "p{margin:10px 0}" +
        ".footer{margin-top:40px;padding-top:20px;border-top:1px solid #eee;"
        "font-size:12px;color:#888;text-align:center}" +
        "</style></head><body>" +
        "<div class=\"container\">" +
        "<div class=\"header\">" +
        "<h1>Foreign Policy Blogs</h1>" +
        f"<div class=\"date\">{date_fmt} — 国际事务博客精选</div>" +
        "</div>" +
        "<div class=\"content\">" + html_body + "</div>" +
        "<div class=\"footer\">由 OpenClaw Agent 自动发送 | Foreign Policy Blogs</div>" +
        "</div></body></html>"
    )
    return html


def send_email(filepath):
    m = re.search(r"(\d{4}-\d{2}-\d{2})", filepath)
    date_str = m.group(1) if m else datetime.now().strftime("%Y-%m-%d")

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    if not content.strip():
        print("File is empty: " + filepath)
        return False

    html = format_html(content, date_str)
    msg = MIMEMultipart()
    msg["From"]    = EMAIL_FROM
    msg["To"]      = EMAIL_TO
    msg["Subject"] = f"Foreign Policy Blogs — {date_str}"

    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=ctx) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        print("Email sent: " + EMAIL_TO)
        return True
    except Exception as e:
        print("SMTP error: " + str(e))
        return False


def main(filepath=None):
    if filepath is None and len(sys.argv) > 1:
        filepath = sys.argv[1]
    if filepath:
        send_email(filepath)
    else:
        files = sorted(glob.glob(os.path.join(TRANSLATE_DIR, "*.md")),
                       key=os.path.getmtime, reverse=True)
        if files:
            send_email(files[0])
        else:
            print("No translate files found")


if __name__ == "__main__":
    main()