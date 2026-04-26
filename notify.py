"""notify.py — แจ้งเตือนทางอีเมล + LINE + Webhook"""
import os, smtplib, requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import streamlit as st


def _secret(k, default=""):
    try:
        return st.secrets.get(k, "") or os.environ.get(k, default)
    except Exception:
        return os.environ.get(k, default)


def send_email(to_email, subject, body_html):
    host = _secret("SMTP_HOST")
    if not host or not to_email:
        return False
    port = int(_secret("SMTP_PORT", "587"))
    user = _secret("SMTP_USERNAME")
    pwd = _secret("SMTP_PASSWORD")
    sender = _secret("SMTP_FROM", user)
    if not user or not pwd:
        return False
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = to_email
        msg.attach(MIMEText(body_html, 'html', 'utf-8'))
        with smtplib.SMTP(host, port, timeout=10) as s:
            s.starttls()
            s.login(user, pwd)
            s.send_message(msg)
        return True
    except Exception:
        return False


def send_line(token, message):
    if not token:
        return False
    try:
        r = requests.post("https://notify-api.line.me/api/notify",
                            headers={"Authorization": f"Bearer {token}"},
                            data={"message": message}, timeout=10)
        return r.status_code == 200
    except Exception:
        return False


def send_webhook(url, message):
    if not url:
        return False
    try:
        if "discord" in url:
            data = {"content": message}
        elif "slack" in url:
            data = {"text": message}
        else:
            data = {"text": message, "message": message}
        r = requests.post(url, json=data, timeout=10)
        return r.status_code in (200, 204)
    except Exception:
        return False


def notify_user(user, title, message, po_number=""):
    """แจ้งทุกช่องทางที่ตั้งค่าไว้"""
    body = f"""<html><body style="font-family:Arial,sans-serif;">
        <h2 style="color:#4A6FA5;">📦 Lab Parfumo PO</h2>
        <p>เรียน {user.get('full_name', '')},</p>
        <p><b>{title}</b></p>
        <p>{message}</p>
        {f'<p>PO: <b>{po_number}</b></p>' if po_number else ''}
        <p style="color:#888; font-size:12px;">— PO Pro System</p>
    </body></html>"""

    if user.get('email'):
        send_email(user['email'], title, body)

    line_token = _secret("LINE_NOTIFY_TOKEN")
    if line_token:
        msg = f"\n📦 {title}"
        if po_number:
            msg += f"\nPO: {po_number}"
        if message:
            msg += f"\n{message[:200]}"
        send_line(line_token, msg)

    webhook = _secret("NOTIFICATION_WEBHOOK")
    if webhook:
        msg = f"📦 **{title}**"
        if po_number:
            msg += f" (PO: {po_number})"
        if message:
            msg += f"\n{message[:300]}"
        send_webhook(webhook, msg)
