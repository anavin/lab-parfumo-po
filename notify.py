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


def send_welcome_email(user_email, user_name, username, password,
                         role_label="ผู้ใช้", company_name="Lab Parfumo",
                         app_url=""):
    """ส่งอีเมลต้อนรับผู้ใช้ใหม่ — มีรหัสผ่านชั่วคราว + คำแนะนำ login"""
    if not user_email:
        return False, "ไม่มีอีเมลของผู้ใช้"

    # ถ้าไม่ระบุ URL → พยายามดึงจาก secrets
    if not app_url:
        app_url = _secret("APP_URL", "")

    login_section = ""
    if app_url:
        login_section = f"""
        <p style="text-align:center; margin: 28px 0;">
            <a href="{app_url}" style="background:#4A6FA5; color:white;
                padding:12px 32px; text-decoration:none; border-radius:8px;
                font-weight:600; font-size:14px; display:inline-block;
                box-shadow:0 2px 8px rgba(74,111,165,0.25);">
                🔐 เข้าสู่ระบบ →
            </a>
        </p>
        """

    body = f"""<html>
    <body style="font-family:'Sarabun','Segoe UI',Arial,sans-serif;
                  background:#F8FAFC; padding:32px; color:#1F2937;">
    <div style="max-width:560px; margin:0 auto; background:white;
                border-radius:16px; padding:32px;
                box-shadow:0 4px 12px rgba(15,23,42,0.08);
                border:1px solid #E2E8F0;">
        <div style="text-align:center; margin-bottom:24px;">
            <div style="display:inline-block; width:64px; height:64px;
                        background:linear-gradient(135deg, #4A6FA5, #2E4D78);
                        border-radius:16px; line-height:64px; font-size:32px;
                        color:white;">📦</div>
            <h1 style="color:#1F2937; font-size:22px; margin:14px 0 4px;">
                ยินดีต้อนรับสู่ {company_name}
            </h1>
            <div style="color:#64748B; font-size:13px;">
                Purchase Order Management System
            </div>
        </div>

        <div style="border-top:1px solid #E2E8F0; padding-top:20px;
                     margin-bottom:18px;">
            <p style="margin:0 0 12px;">เรียน <b>คุณ {user_name}</b>,</p>
            <p style="margin:0 0 16px; line-height:1.6;">
                ผู้ดูแลระบบได้เพิ่มบัญชีของคุณในระบบ
                <b>{company_name} PO Pro</b> แล้ว
                — กรุณาใช้ข้อมูลด้านล่างเข้าสู่ระบบครั้งแรก
            </p>
        </div>

        <div style="background:#F4F7FB; border:1px solid #A8C0E0;
                     border-radius:10px; padding:18px; margin-bottom:20px;">
            <div style="font-size:11px; font-weight:700; color:#3A5A8C;
                         text-transform:uppercase; letter-spacing:0.6px;
                         margin-bottom:10px;">
                🔑 ข้อมูลเข้าสู่ระบบ
            </div>
            <table style="width:100%; font-size:13px; border-collapse:collapse;">
                <tr>
                    <td style="padding:6px 0; color:#64748B; width:35%;">Username</td>
                    <td style="padding:6px 0; font-weight:700; font-family:monospace;
                                color:#1F2937;">{username}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; color:#64748B;">รหัสผ่านชั่วคราว</td>
                    <td style="padding:6px 0; font-weight:700; font-family:monospace;
                                color:#DC2626;">{password}</td>
                </tr>
                <tr>
                    <td style="padding:6px 0; color:#64748B;">สิทธิ์</td>
                    <td style="padding:6px 0; font-weight:600;">{role_label}</td>
                </tr>
            </table>
        </div>

        <div style="background:#FFFBEB; border:1px solid rgba(217,119,6,0.2);
                     border-radius:10px; padding:14px 16px; margin-bottom:20px;
                     font-size:12px; color:#92400E;">
            ⚠️ <b>สำคัญ:</b> ระบบจะบังคับให้ตั้งรหัสผ่านใหม่ของตัวเองเมื่อ login ครั้งแรก
            กรุณาเก็บรหัสผ่านนี้เป็นความลับและเปลี่ยนทันที
        </div>

        {login_section}

        <div style="border-top:1px solid #E2E8F0; padding-top:18px; margin-top:24px;
                     font-size:11px; color:#94A3B8; text-align:center;">
            <p style="margin:0 0 4px;">
                หากไม่ได้ร้องขอบัญชีนี้ กรุณาเพิกเฉยหรือแจ้งผู้ดูแลระบบ
            </p>
            <p style="margin:0;">
                © {company_name} • PO Pro System
            </p>
        </div>
    </div>
    </body></html>"""

    subject = f"🎉 ยินดีต้อนรับสู่ {company_name} PO Pro — บัญชีของคุณพร้อมใช้งาน"

    sent = send_email(user_email, subject, body)
    if sent:
        return True, "ส่งอีเมลสำเร็จ"
    else:
        return False, "ไม่สามารถส่งอีเมลได้ — ตรวจสอบการตั้งค่า SMTP"


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
