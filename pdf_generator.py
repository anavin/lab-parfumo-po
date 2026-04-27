"""pdf_generator.py — PDF generator (PO + GRN + Period Reports)

⭐ MAJOR UPDATES:
- C1 — All user input HTML-escaped (anti-XSS)
- F2 — generate_period_report_pdf() for monthly/yearly reports
"""
import html as _html
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

from weasyprint import HTML, CSS


# ----- Paths -----
HERE = Path(__file__).parent
FONT_REGULAR = HERE / "fonts" / "Sarabun-Regular.ttf"
FONT_BOLD = HERE / "fonts" / "Sarabun-Bold.ttf"


# ----- Brand & Company -----
BRAND_PRIMARY = "#4A6FA5"
BRAND_DARK = "#2E4D78"
BRAND_LIGHT = "#F4F7FB"
BRAND_BORDER = "#A8C0E0"

COMPANY_INFO_DEFAULT = {
    'name': 'Lab Parfumo',
    'name_th': 'บริษัท ทัช ไดเวอร์เจนซ์ จำกัด',
    'address': '',
    'phone': '',
    'email': '',
    'tax_id': '0115564002651',
    'website': 'www.labparfumo.com',
}


def _get_company_info():
    """ดึงข้อมูลบริษัทจาก DB — fallback เป็น default"""
    try:
        import database as db
        info = db.get_company_settings()
        return {**COMPANY_INFO_DEFAULT, **info}
    except Exception:
        return COMPANY_INFO_DEFAULT


# Backward compat
COMPANY_INFO = COMPANY_INFO_DEFAULT


# ==================================================================
# HTML escape — IMPORTANT (anti-XSS in PDF)
# ==================================================================
def esc(s):
    """Escape user input ก่อนใส่ใน HTML"""
    if s is None:
        return ""
    return _html.escape(str(s), quote=True)


def _fmt_date(d):
    if not d:
        return "-"
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d.split('T')[0]).strftime('%d/%m/%Y')
        except Exception:
            return esc(d)
    return d.strftime('%d/%m/%Y')


def _fmt_money(amount):
    """Format ตัวเลขเงิน"""
    try:
        return f"{float(amount):,.2f}"
    except (TypeError, ValueError):
        return "0.00"


def _font_face_css():
    css = ""
    if FONT_REGULAR.exists():
        css += f"""
        @font-face {{
            font-family: 'Sarabun';
            font-weight: normal;
            src: url('file://{FONT_REGULAR.absolute()}');
        }}"""
    if FONT_BOLD.exists():
        css += f"""
        @font-face {{
            font-family: 'Sarabun';
            font-weight: bold;
            src: url('file://{FONT_BOLD.absolute()}');
        }}"""
    return css


def _base_css():
    return _font_face_css() + f"""
    * {{ box-sizing: border-box; }}
    body {{
        font-family: 'Sarabun', 'TH Sarabun New', sans-serif;
        font-size: 10pt;
        line-height: 1.4;
        color: #1F2937;
        margin: 0;
        padding: 0;
    }}
    
    .header-table {{
        width: 100%;
        border-collapse: collapse;
        margin-bottom: 6px;
    }}
    .header-table .left-col {{ width: 60%; vertical-align: top; padding-right: 16px; }}
    .header-table .right-col {{ width: 40%; vertical-align: top; text-align: right; }}
    
    .doc-title {{
        font-size: 24pt;
        font-weight: bold;
        color: {BRAND_PRIMARY};
        margin: 0;
    }}
    .doc-info {{
        font-size: 10pt;
        color: #555;
        margin: 2px 0;
    }}
    
    .small {{ font-size: 9pt; color: #666; }}
    .red {{ color: #DC2626; font-weight: bold; }}
    .green {{ color: #059669; font-weight: bold; }}
    .center {{ text-align: center; }}
    .num {{ text-align: right; }}
    
    .header-divider {{
        border: none;
        border-top: 2px solid {BRAND_PRIMARY};
        margin: 8px 0 14px;
    }}
    
    .info-box {{
        background: {BRAND_LIGHT};
        border: 1px solid {BRAND_BORDER};
        border-radius: 6px;
        padding: 10px 14px;
        margin: 10px 0;
    }}
    .info-box table {{ width: 100%; }}
    .info-box .label {{
        color: #666;
        font-size: 9pt;
        width: 30%;
        vertical-align: top;
    }}
    
    h1 {{
        font-size: 16pt;
        color: {BRAND_DARK};
        margin: 0 0 6px;
    }}
    h2 {{
        font-size: 13pt;
        color: {BRAND_DARK};
        margin: 14px 0 6px;
    }}
    h3 {{
        font-size: 11pt;
        color: {BRAND_DARK};
        margin: 10px 0 4px;
        padding-bottom: 4px;
        border-bottom: 1px solid {BRAND_BORDER};
    }}
    
    table.items {{
        width: 100%;
        border-collapse: collapse;
        margin: 6px 0;
        font-size: 9.5pt;
    }}
    table.items th {{
        background: {BRAND_PRIMARY};
        color: white;
        padding: 6px 8px;
        font-weight: bold;
        text-align: left;
        font-size: 9.5pt;
    }}
    table.items td {{
        padding: 6px 8px;
        border-bottom: 1px solid #E2E8F0;
    }}
    table.items tr:nth-child(even) td {{ background: #F8FAFC; }}
    
    table.summary {{
        margin-left: auto;
        margin-top: 10px;
        font-size: 10pt;
        width: 280px;
    }}
    table.summary .label {{
        text-align: right;
        padding: 3px 10px;
        color: #555;
    }}
    table.summary .value {{
        text-align: right;
        padding: 3px 0;
        font-weight: 500;
        width: 110px;
    }}
    table.summary tr.total .label,
    table.summary tr.total .value {{
        font-weight: bold;
        font-size: 12pt;
        color: {BRAND_PRIMARY};
        border-top: 2px solid {BRAND_PRIMARY};
        padding-top: 6px;
    }}
    
    .notes {{
        margin: 12px 0;
        padding: 10px 14px;
        background: #FFFBEB;
        border-left: 3px solid #D97706;
        border-radius: 4px;
        font-size: 9.5pt;
    }}
    
    table.signatures {{
        width: 100%;
        margin-top: 50px;
    }}
    table.signatures td {{
        text-align: center;
        padding: 8px;
        vertical-align: top;
    }}
    table.signatures .label {{
        font-size: 9pt;
        color: #555;
        margin-bottom: 35px;
    }}
    table.signatures .line {{
        border-top: 1px dashed #888;
        width: 80%;
        margin: 0 auto 4px;
    }}
    
    .clearfix {{ clear: both; }}
    
    .footer {{
        margin-top: 28px;
        padding-top: 8px;
        border-top: 1px solid #E2E8F0;
        text-align: center;
        font-size: 9pt;
        color: #666;
    }}
    .footer-meta {{
        text-align: right;
        font-size: 8pt;
        color: #999;
        margin-top: 2px;
    }}
    
    /* === Period report === */
    .kpi-grid {{
        display: table;
        width: 100%;
        border-spacing: 8px;
        margin: 10px 0 18px;
    }}
    .kpi-cell {{
        display: table-cell;
        background: {BRAND_LIGHT};
        border: 1px solid {BRAND_BORDER};
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }}
    .kpi-label {{
        font-size: 9pt;
        color: #555;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 4px;
    }}
    .kpi-value {{
        font-size: 16pt;
        font-weight: bold;
        color: {BRAND_DARK};
    }}
    
    .budget-bar-bg {{
        background: #E2E8F0;
        height: 16px;
        border-radius: 8px;
        overflow: hidden;
        margin: 4px 0;
    }}
    .budget-bar {{
        height: 100%;
        background: {BRAND_PRIMARY};
        transition: width 0.3s;
    }}
    .budget-bar.warning {{ background: #D97706; }}
    .budget-bar.danger {{ background: #DC2626; }}
    
    @page {{
        size: A4;
        margin: 1.5cm 1.5cm 1.5cm 1.5cm;
    }}
    """


def _company_header_html():
    info = _get_company_info()
    name = esc(info.get('name', 'Lab Parfumo'))
    name_th = esc(info.get('name_th', ''))
    address = esc(info.get('address', '')).replace('\n', '<br/>') or ""
    phone = esc(info.get('phone', ''))
    email = esc(info.get('email', ''))
    tax_id = esc(info.get('tax_id', ''))
    website = esc(info.get('website', ''))
    
    contact = []
    if phone:
        contact.append(f"โทร: {phone}")
    if email:
        contact.append(f"อีเมล: {email}")
    contact_html = " | ".join(contact)
    
    return f"""
    <h1 style="margin:0; color:{BRAND_DARK}; font-size:18pt;">{name}</h1>
    {f'<div class="small">{name_th}</div>' if name_th else ''}
    {f'<div class="small">{address}</div>' if address else ''}
    {f'<div class="small">{contact_html}</div>' if contact_html else ''}
    {f'<div class="small">เลขผู้เสียภาษี: {tax_id}</div>' if tax_id else ''}
    {f'<div class="small">{website}</div>' if website else ''}
    """


# ==================================================================
# PO PDF
# ==================================================================
def generate_po_pdf(po: dict, role: str = "admin") -> bytes:
    """สร้าง PDF ใบ PO ส่ง supplier
    role: 'admin' = เห็นราคา/supplier ครบ, 'requester' = ซ่อนราคา/supplier
    
    ⭐ All user input HTML-escaped via esc()
    """
    is_requester = role == "requester"

    # Items rows — ⭐ ESCAPED
    items_rows = ""
    for i, item in enumerate(po.get('items', []), 1):
        name = esc(item.get('name', ''))
        unit = esc(item.get('unit', ''))
        try:
            qty = float(item.get('qty', 0))
        except (TypeError, ValueError):
            qty = 0
        if is_requester:
            items_rows += f"""
        <tr>
            <td class="center">{i}</td>
            <td>{name}</td>
            <td class="num">{qty:,.0f}</td>
            <td class="center">{unit}</td>
        </tr>"""
        else:
            try:
                unit_price = float(item.get('unit_price', 0))
                subtotal = float(item.get('subtotal', 0))
            except (TypeError, ValueError):
                unit_price = subtotal = 0
            items_rows += f"""
        <tr>
            <td class="center">{i}</td>
            <td>{name}</td>
            <td class="num">{qty:,.0f}</td>
            <td class="center">{unit}</td>
            <td class="num">{unit_price:,.2f}</td>
            <td class="num">{subtotal:,.2f}</td>
        </tr>"""

    # Summary
    try:
        sub = float(po.get('subtotal', 0))
        disc = float(po.get('discount', 0))
        ship = float(po.get('shipping_fee', 0))
        vat = float(po.get('vat', 0))
        total = float(po.get('total', 0))
    except (TypeError, ValueError):
        sub = disc = ship = vat = total = 0

    summary_rows = f"""
    <tr><td class="label">ยอดรวม:</td><td class="value">{sub:,.2f} บาท</td></tr>
    """
    if disc > 0:
        summary_rows += f"""
    <tr><td class="label">ส่วนลด:</td><td class="value green">-{disc:,.2f} บาท</td></tr>"""
    if ship > 0:
        summary_rows += f"""
    <tr><td class="label">ค่าจัดส่ง:</td><td class="value">{ship:,.2f} บาท</td></tr>"""
    if vat > 0:
        summary_rows += f"""
    <tr><td class="label">VAT 7%:</td><td class="value">{vat:,.2f} บาท</td></tr>"""
    summary_rows += f"""
    <tr class="total"><td class="label">รวมสุทธิ:</td><td class="value">{total:,.2f} บาท</td></tr>
    """

    # ⭐ ESCAPED user input
    supplier_name = esc(po.get('supplier_name', '-'))
    supplier_contact = esc(po.get('supplier_contact', '')).replace('\n', '<br/>')

    notes_html = ""
    if po.get('notes') or po.get('procurement_notes'):
        notes_html = '<div class="notes">'
        if po.get('notes'):
            notes_html += f"<b>หมายเหตุ:</b> {esc(po['notes'])}<br/>"
        if po.get('procurement_notes'):
            notes_html += f"<b>โน้ตจัดซื้อ:</b> <i>{esc(po['procurement_notes'])}</i>"
        notes_html += '</div>'

    exp_date_html = ""
    if po.get('expected_date'):
        exp_date_html = f"<p><b>กำหนดส่ง:</b> {_fmt_date(po['expected_date'])}</p>"

    po_number = esc(po.get('po_number', '-'))
    
    # info box
    info_box_html = ""
    if not is_requester:
        info_box_html = f"""
    <div class="info-box">
        <table>
            <tr>
                <td class="label">สั่งจาก / Supplier:</td>
                <td><b>{supplier_name}</b></td>
            </tr>
            {f'<tr><td></td><td>{supplier_contact}</td></tr>' if supplier_contact else ''}
        </table>
    </div>"""

    # items table
    if is_requester:
        items_table = f"""<table class="items">
        <tr>
            <th style="width:8%">#</th>
            <th style="width:62%">รายการ</th>
            <th style="width:15%">จำนวน</th>
            <th style="width:15%">หน่วย</th>
        </tr>
        {items_rows}
    </table>"""
    else:
        items_table = f"""<table class="items">
        <tr>
            <th style="width:6%">#</th>
            <th style="width:42%">รายการ</th>
            <th style="width:12%">จำนวน</th>
            <th style="width:10%">หน่วย</th>
            <th style="width:15%">ราคา/หน่วย</th>
            <th style="width:15%">รวม</th>
        </tr>
        {items_rows}
    </table>"""

    summary_html = ""
    if not is_requester:
        summary_html = f"""<table class="summary">
        {summary_rows}
    </table>
    <div class="clearfix"></div>"""

    info = _get_company_info()
    company_name_disp = esc(info.get('name', 'Lab Parfumo'))
    company_website_disp = esc(info.get('website', ''))

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>{_base_css()}</style></head>
    <body>

    <table class="header-table">
        <tr>
            <td class="left-col">{_company_header_html()}</td>
            <td class="right-col">
                <p class="doc-title">ใบสั่งซื้อ</p>
                <div class="small">PURCHASE ORDER</div>
                <div class="doc-info"><b>เลขที่:</b> {po_number}</div>
                <div class="doc-info"><b>วันที่:</b> {_fmt_date(po.get('ordered_date') or po.get('created_at'))}</div>
            </td>
        </tr>
    </table>
    <hr class="header-divider"/>

    {info_box_html}
    {exp_date_html}

    <h3>รายการสั่งซื้อ</h3>
    {items_table}
    {summary_html}
    {notes_html}

    <table class="signatures">
        <tr>
            <td><div class="label">ผู้สั่งซื้อ / Buyer</div></td>
            <td style="width:30%"></td>
            <td><div class="label">ผู้ขาย / Supplier</div></td>
        </tr>
        <tr>
            <td><div class="line"></div><div class="small">{company_name_disp}</div></td>
            <td></td>
            <td><div class="line"></div><div class="small">(____________________)</div></td>
        </tr>
        <tr>
            <td><div class="small">วันที่ ____/____/______</div></td>
            <td></td>
            <td><div class="small">วันที่ ____/____/______</div></td>
        </tr>
    </table>

    <div class="footer">{company_name_disp}{f' | {company_website_disp}' if company_website_disp else ''}</div>
    <div class="footer-meta">พิมพ์เมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

    </body></html>
    """

    return HTML(string=html).write_pdf()


# ==================================================================
# GRN PDF (ใบรับของ)
# ==================================================================
def generate_grn_pdf(po: dict, delivery: dict) -> bytes:
    """สร้าง PDF ใบรับของ
    
    ⭐ All user input HTML-escaped"""
    grn_no = esc(f"GRN-{po.get('po_number', '-')}-{delivery.get('delivery_no', 1):02d}")

    # Items rows
    items_rows = ""
    for i, item in enumerate(delivery.get('items_received', []), 1):
        try:
            damaged = int(float(item.get('qty_damaged', 0) or 0))
            ordered = float(item.get('qty_ordered', 0))
            received = float(item.get('qty_received', 0))
        except (TypeError, ValueError):
            damaged = ordered = received = 0
        damage_html = f'<span class="red">{damaged}</span>' if damaged > 0 else "0"
        items_rows += f"""
        <tr>
            <td class="center">{i}</td>
            <td>{esc(item.get('name', ''))}</td>
            <td class="num">{ordered:,.0f}</td>
            <td class="num">{received:,.0f}</td>
            <td class="num">{damage_html}</td>
            <td>{esc(item.get('notes') or item.get('item_notes', ''))}</td>
        </tr>"""

    # Issue
    issue_html = ""
    if delivery.get('issue_description'):
        issue_html = (
            f"<p><b>ปัญหา:</b> "
            f"<span class='red'>{esc(delivery['issue_description'])}</span></p>"
        )

    info = _get_company_info()
    po_number = esc(po.get('po_number', '-'))
    supplier = esc(po.get('supplier_name', '-'))
    received_date = _fmt_date(delivery.get('received_date'))
    received_by = esc(delivery.get('received_by_name', '-'))
    overall_cond = esc(delivery.get('overall_condition', 'ปกติ'))
    company_name_disp = esc(info.get('name', 'Lab Parfumo'))

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>{_base_css()}</style></head>
    <body>

    <table class="header-table">
        <tr>
            <td class="left-col">{_company_header_html()}</td>
            <td class="right-col">
                <p class="doc-title">ใบรับของ</p>
                <div class="small">GOODS RECEIPT NOTE</div>
                <div class="doc-info"><b>เลขที่:</b> {grn_no}</div>
                <div class="doc-info"><b>วันรับ:</b> {received_date}</div>
            </td>
        </tr>
    </table>
    <hr class="header-divider"/>

    <div class="info-box">
        <table>
            <tr>
                <td class="label">PO อ้างอิง:</td>
                <td><b>{po_number}</b></td>
            </tr>
            <tr>
                <td class="label">Supplier:</td>
                <td>{supplier}</td>
            </tr>
            <tr>
                <td class="label">ผู้รับของ:</td>
                <td>{received_by}</td>
            </tr>
            <tr>
                <td class="label">สภาพรวม:</td>
                <td><b>{overall_cond}</b></td>
            </tr>
        </table>
    </div>

    {issue_html}

    <h3>รายการที่รับ</h3>
    <table class="items">
        <tr>
            <th style="width:6%">#</th>
            <th style="width:38%">รายการ</th>
            <th style="width:12%">สั่ง</th>
            <th style="width:12%">รับ</th>
            <th style="width:12%">เสีย</th>
            <th style="width:20%">หมายเหตุ</th>
        </tr>
        {items_rows}
    </table>

    {f'<div class="notes">{esc(delivery.get("notes", ""))}</div>' if delivery.get('notes') else ''}

    <table class="signatures">
        <tr>
            <td><div class="label">ผู้ส่งของ</div></td>
            <td style="width:30%"></td>
            <td><div class="label">ผู้รับของ</div></td>
        </tr>
        <tr>
            <td><div class="line"></div><div class="small">(____________________)</div></td>
            <td></td>
            <td><div class="line"></div><div class="small">{received_by}</div></td>
        </tr>
        <tr>
            <td><div class="small">วันที่ ____/____/______</div></td>
            <td></td>
            <td><div class="small">วันที่ {received_date}</div></td>
        </tr>
    </table>

    <div class="footer">{company_name_disp} — Goods Receipt Note</div>
    <div class="footer-meta">พิมพ์เมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

    </body></html>
    """

    return HTML(string=html).write_pdf()


# ==================================================================
# 📊 Period Report PDF (NEW FEATURE F2)
# ==================================================================
def generate_period_report_pdf(
    period_label: str,
    start_date: date,
    end_date: date,
    pos: list,
    budgets: Optional[list] = None,
    generated_by: str = "",
) -> bytes:
    """สร้าง PDF รายงานสรุประยะเวลา (เดือน / ไตรมาส / ปี)
    
    Args:
        period_label: เช่น 'เมษายน 2026' หรือ 'ไตรมาส 1/2026'
        start_date, end_date: ช่วงเวลา
        pos: list of PO dicts (filtered to period)
        budgets: optional list of budget status dicts (from get_budget_status_for_dashboard)
        generated_by: ชื่อผู้สั่งพิมพ์
    
    ⭐ All user input HTML-escaped"""
    info = _get_company_info()

    # Filter valid POs (exclude cancelled)
    valid = [p for p in pos if p.get('status') != 'ยกเลิก']
    completed = [p for p in valid if p.get('status') == 'เสร็จสมบูรณ์']

    n_total = len(pos)
    n_valid = len(valid)
    n_completed = len(completed)
    total_spend = sum(float(p.get('total', 0) or 0) for p in valid)
    avg_per_po = (total_spend / n_valid) if n_valid else 0

    # Top suppliers
    sup_data = {}
    for p in valid:
        s = p.get('supplier_name') or '-'
        if s not in sup_data:
            sup_data[s] = {'count': 0, 'total': 0}
        sup_data[s]['count'] += 1
        sup_data[s]['total'] += float(p.get('total', 0) or 0)
    top_suppliers = sorted(sup_data.items(), key=lambda x: -x[1]['total'])[:10]

    # Top items
    item_data = {}
    for p in valid:
        for it in p.get('items', []):
            n = it.get('name', '-')
            if n not in item_data:
                item_data[n] = {'qty': 0, 'total': 0}
            try:
                item_data[n]['qty'] += float(it.get('qty', 0) or 0)
                item_data[n]['total'] += float(it.get('subtotal', 0) or 0)
            except (TypeError, ValueError):
                pass
    top_items = sorted(item_data.items(), key=lambda x: -x[1]['total'])[:15]

    # Status breakdown
    status_breakdown = {}
    for p in pos:
        s = p.get('status', '-')
        status_breakdown[s] = status_breakdown.get(s, 0) + 1

    # KPI section
    kpi_html = f"""
    <div class="kpi-grid">
        <div class="kpi-cell">
            <div class="kpi-label">PO ทั้งหมด</div>
            <div class="kpi-value">{n_total}</div>
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">เสร็จสมบูรณ์</div>
            <div class="kpi-value">{n_completed}</div>
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">ใช้จ่ายรวม</div>
            <div class="kpi-value">฿{total_spend:,.0f}</div>
        </div>
        <div class="kpi-cell">
            <div class="kpi-label">เฉลี่ย/ใบ</div>
            <div class="kpi-value">฿{avg_per_po:,.0f}</div>
        </div>
    </div>
    """

    # Budget section
    budget_html = ""
    if budgets:
        rows = ""
        for b in budgets:
            cat = esc(b.get('category', '-'))
            budget = float(b.get('budget', 0))
            actual = float(b.get('actual', 0))
            pct = float(b.get('percent', 0))
            status = b.get('status', 'ok')
            
            bar_class = ""
            if status == 'over' or status == 'critical':
                bar_class = "danger"
            elif status == 'warning':
                bar_class = "warning"
            
            rows += f"""
            <tr>
                <td>{cat}</td>
                <td class="num">฿{budget:,.0f}</td>
                <td class="num">฿{actual:,.0f}</td>
                <td>
                    <div class="budget-bar-bg">
                        <div class="budget-bar {bar_class}" style="width:{min(pct, 100):.0f}%;"></div>
                    </div>
                </td>
                <td class="num"><b>{pct:.1f}%</b></td>
            </tr>"""
        budget_html = f"""
        <h2>💰 สถานะงบประมาณ</h2>
        <table class="items">
            <tr>
                <th>หมวด</th>
                <th class="num">งบประมาณ</th>
                <th class="num">ใช้จริง</th>
                <th>ความคืบหน้า</th>
                <th class="num">% ที่ใช้</th>
            </tr>
            {rows}
        </table>
        """

    # Top suppliers table
    supp_rows = ""
    for s_name, data in top_suppliers:
        supp_rows += f"""
        <tr>
            <td>{esc(s_name)}</td>
            <td class="num">{data['count']}</td>
            <td class="num">฿{data['total']:,.2f}</td>
        </tr>"""
    if not supp_rows:
        supp_rows = '<tr><td colspan="3" class="center">-</td></tr>'

    # Top items table
    item_rows = ""
    for i_name, data in top_items:
        item_rows += f"""
        <tr>
            <td>{esc(i_name)}</td>
            <td class="num">{data['qty']:,.0f}</td>
            <td class="num">฿{data['total']:,.2f}</td>
        </tr>"""
    if not item_rows:
        item_rows = '<tr><td colspan="3" class="center">-</td></tr>'

    # Status breakdown
    status_rows = ""
    for s_name, count in sorted(status_breakdown.items(), key=lambda x: -x[1]):
        status_rows += f"""
        <tr>
            <td>{esc(s_name)}</td>
            <td class="num">{count}</td>
            <td class="num">{count/n_total*100 if n_total else 0:.1f}%</td>
        </tr>"""

    company_name_disp = esc(info.get('name', 'Lab Parfumo'))

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>{_base_css()}</style></head>
    <body>

    <table class="header-table">
        <tr>
            <td class="left-col">{_company_header_html()}</td>
            <td class="right-col">
                <p class="doc-title">รายงาน</p>
                <div class="small">PURCHASE REPORT</div>
                <div class="doc-info"><b>ระยะเวลา:</b> {esc(period_label)}</div>
                <div class="doc-info"><b>ระหว่าง:</b> {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}</div>
            </td>
        </tr>
    </table>
    <hr class="header-divider"/>

    <h2>📊 สรุปภาพรวม</h2>
    {kpi_html}

    {budget_html}

    <h2>📋 สถานะ PO</h2>
    <table class="items">
        <tr>
            <th>สถานะ</th>
            <th class="num">จำนวน</th>
            <th class="num">สัดส่วน</th>
        </tr>
        {status_rows}
    </table>

    <h2>🏭 Top Suppliers (10 อันดับ)</h2>
    <table class="items">
        <tr>
            <th>Supplier</th>
            <th class="num">จำนวน PO</th>
            <th class="num">ยอดรวม</th>
        </tr>
        {supp_rows}
    </table>

    <h2>📦 Top Items (15 อันดับ)</h2>
    <table class="items">
        <tr>
            <th>รายการ</th>
            <th class="num">จำนวน</th>
            <th class="num">มูลค่า</th>
        </tr>
        {item_rows}
    </table>

    <div class="footer">{company_name_disp} — Period Report</div>
    <div class="footer-meta">
        จัดทำโดย: {esc(generated_by) if generated_by else '-'} • 
        พิมพ์เมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>

    </body></html>
    """

    return HTML(string=html).write_pdf()
