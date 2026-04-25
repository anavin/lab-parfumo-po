"""pdf_generator.py — สร้าง PDF ใบ PO + ใบรับของ ใช้ WeasyPrint (รองรับภาษาไทยเต็มที่)"""
import os
from datetime import datetime
from pathlib import Path

from weasyprint import HTML, CSS


# ----- Paths -----
HERE = Path(__file__).parent
FONT_REGULAR = HERE / "fonts" / "Sarabun-Regular.ttf"
FONT_BOLD = HERE / "fonts" / "Sarabun-Bold.ttf"


# ----- Brand & Company -----
BRAND_GOLD = "#C8A47E"
BRAND_DARK = "#3D3530"
BRAND_LIGHT = "#F8F4EE"
BRAND_BORDER = "#E8DDD0"

COMPANY_INFO = {
    'name': 'Lab Parfumo',
    'name_th': 'แล็บ พาฟูโม่',
    'address': '123 ถนนสุขุมวิท แขวงคลองตัน เขตวัฒนา กรุงเทพฯ 10110',
    'phone': '02-xxx-xxxx',
    'email': 'contact@labparfumo.com',
    'tax_id': '0-1055-64xxx-xx-x',
    'website': 'www.labparfumo.com',
}


def _fmt_date(d):
    if not d:
        return "-"
    if isinstance(d, str):
        try:
            return datetime.fromisoformat(d.split('T')[0]).strftime('%d/%m/%Y')
        except Exception:
            return d
    return d.strftime('%d/%m/%Y')


def _font_face_css():
    """สร้าง @font-face CSS สำหรับ Sarabun"""
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
    """CSS base ใช้ทุก document"""
    return _font_face_css() + f"""
        @page {{
            size: A4;
            margin: 15mm;
        }}
        body {{
            font-family: 'Sarabun', 'Garuda', 'Norasi', sans-serif;
            font-size: 10pt;
            color: {BRAND_DARK};
            margin: 0;
            padding: 0;
        }}
        h1 {{
            color: {BRAND_GOLD};
            font-size: 22pt;
            margin: 0 0 4px 0;
            font-weight: bold;
        }}
        h2 {{
            color: {BRAND_DARK};
            font-size: 14pt;
            margin: 12px 0 6px 0;
        }}
        h3 {{
            color: {BRAND_DARK};
            font-size: 11pt;
            margin: 10px 0 4px 0;
        }}
        .small {{ font-size: 8pt; color: #666; }}
        .right {{ text-align: right; }}
        .center {{ text-align: center; }}
        .header-divider {{
            border: none;
            border-top: 2px solid {BRAND_GOLD};
            margin: 8px 0;
        }}
        .header-table {{
            width: 100%;
            margin-bottom: 4px;
        }}
        .header-table td {{
            vertical-align: top;
        }}
        .header-table .left-col {{ width: 60%; }}
        .header-table .right-col {{ width: 40%; text-align: right; }}
        .doc-title {{
            font-size: 20pt;
            font-weight: bold;
            color: {BRAND_DARK};
            margin: 0;
        }}
        .doc-info {{
            margin-top: 6px;
            font-size: 10pt;
        }}
        .info-box {{
            background: {BRAND_LIGHT};
            border: 1px solid {BRAND_BORDER};
            padding: 10px 14px;
            margin: 8px 0;
        }}
        .info-box table {{
            width: 100%;
            border-collapse: collapse;
        }}
        .info-box td {{
            padding: 2px 0;
            vertical-align: top;
        }}
        .info-box td.label {{
            width: 25%;
            font-weight: bold;
        }}
        table.items {{
            width: 100%;
            border-collapse: collapse;
            margin: 6px 0;
        }}
        table.items th {{
            background: {BRAND_GOLD};
            color: white;
            padding: 7px 8px;
            text-align: left;
            font-weight: bold;
            font-size: 10pt;
        }}
        table.items td {{
            border: 1px solid {BRAND_BORDER};
            padding: 6px 8px;
            font-size: 10pt;
        }}
        table.items td.num {{ text-align: right; }}
        table.items td.center {{ text-align: center; }}
        table.summary {{
            float: right;
            margin: 8px 0 16px 0;
            border-collapse: collapse;
        }}
        table.summary td {{
            padding: 6px 14px;
            border-bottom: 1px solid {BRAND_BORDER};
            font-size: 10pt;
        }}
        table.summary td.label {{ text-align: right; }}
        table.summary td.value {{ text-align: right; min-width: 100px; }}
        table.summary tr.total td {{
            background: {BRAND_GOLD};
            color: white;
            font-weight: bold;
            font-size: 13pt;
            border: none;
        }}
        .clearfix::after {{
            content: "";
            display: table;
            clear: both;
        }}
        .notes {{
            margin: 12px 0;
            padding: 8px 12px;
            background: #FAFAF8;
            border-left: 3px solid {BRAND_GOLD};
        }}
        .notes b {{ color: {BRAND_DARK}; }}
        .signatures {{
            margin-top: 20px;
            width: 100%;
            border-collapse: collapse;
        }}
        .signatures td {{
            text-align: center;
            padding: 0 10px;
            vertical-align: top;
        }}
        .signatures .label {{ font-size: 8pt; color: #666; }}
        .signatures .line {{
            border-top: 1px solid #999;
            margin: 28px 12px 4px 12px;
        }}
        .footer {{
            text-align: center;
            margin-top: 16px;
            color: {BRAND_GOLD};
            font-weight: bold;
            font-size: 10pt;
        }}
        .footer-meta {{
            text-align: center;
            margin-top: 4px;
            font-size: 8pt;
            color: #666;
        }}
        .green {{ color: #1D9E75; }}
        .red {{ color: #A32D2D; }}
        .progress {{
            display: flex;
            gap: 4px;
            margin: 10px 0;
            font-size: 9pt;
        }}
        .progress div {{
            flex: 1;
            padding: 4px;
            text-align: center;
            border-radius: 3px;
        }}
        .image-grid {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 8px 0;
        }}
        .image-grid img {{
            width: 30%;
            max-height: 150px;
            object-fit: cover;
            border: 1px solid {BRAND_BORDER};
        }}
        .badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 9pt;
            font-weight: bold;
        }}
        .badge-ok {{ background: #E1F5EE; color: #0F6E56; }}
        .badge-warn {{ background: #FAEEDA; color: #BA7517; }}
        .badge-error {{ background: #FCEBEB; color: #A32D2D; }}
    """


def _company_header_html():
    return f"""
    <div>
        <h1>{COMPANY_INFO['name']}</h1>
        <div class="small">{COMPANY_INFO['name_th']}</div>
        <div class="small" style="margin-top:4px;">{COMPANY_INFO['address']}</div>
        <div class="small">โทร: {COMPANY_INFO['phone']} | อีเมล: {COMPANY_INFO['email']}</div>
        <div class="small">เลขผู้เสียภาษี: {COMPANY_INFO['tax_id']}</div>
    </div>
    """


# ==================================================================
# PO PDF
# ==================================================================

def generate_po_pdf(po: dict) -> bytes:
    """สร้าง PDF ใบ PO ส่ง supplier"""

    # Items rows
    items_rows = ""
    for i, item in enumerate(po.get('items', []), 1):
        items_rows += f"""
        <tr>
            <td class="center">{i}</td>
            <td>{item.get('name', '')}</td>
            <td class="num">{item.get('qty', 0):,.0f}</td>
            <td class="center">{item.get('unit', '')}</td>
            <td class="num">{item.get('unit_price', 0):,.2f}</td>
            <td class="num">{item.get('subtotal', 0):,.2f}</td>
        </tr>"""

    # Summary
    summary_rows = f"""
    <tr><td class="label">ยอดรวม:</td><td class="value">{po.get('subtotal', 0):,.2f} บาท</td></tr>
    """
    if po.get('discount', 0) > 0:
        summary_rows += f"""
    <tr><td class="label">ส่วนลด:</td><td class="value green">-{po['discount']:,.2f} บาท</td></tr>"""
    if po.get('shipping_fee', 0) > 0:
        summary_rows += f"""
    <tr><td class="label">ค่าจัดส่ง:</td><td class="value">{po['shipping_fee']:,.2f} บาท</td></tr>"""
    if po.get('vat', 0) > 0:
        summary_rows += f"""
    <tr><td class="label">VAT 7%:</td><td class="value">{po['vat']:,.2f} บาท</td></tr>"""
    summary_rows += f"""
    <tr class="total"><td class="label">รวมสุทธิ:</td><td class="value">{po.get('total', 0):,.2f} บาท</td></tr>
    """

    # Supplier contact (multiline)
    supplier_contact = (po.get('supplier_contact') or '').replace('\n', '<br/>')

    # Notes section
    notes_html = ""
    if po.get('notes') or po.get('procurement_notes'):
        notes_html = '<div class="notes">'
        if po.get('notes'):
            notes_html += f"<b>หมายเหตุ:</b> {po['notes']}<br/>"
        if po.get('procurement_notes'):
            notes_html += f"<b>โน้ตจัดซื้อ:</b> <i>{po['procurement_notes']}</i>"
        notes_html += '</div>'

    # Expected date
    exp_date_html = ""
    if po.get('expected_date'):
        exp_date_html = f"<p><b>กำหนดส่ง:</b> {_fmt_date(po['expected_date'])}</p>"

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
                <div class="doc-info"><b>เลขที่:</b> {po.get('po_number', '-')}</div>
                <div class="doc-info"><b>วันที่:</b> {_fmt_date(po.get('ordered_date') or po.get('created_at'))}</div>
            </td>
        </tr>
    </table>
    <hr class="header-divider"/>

    <div class="info-box">
        <table>
            <tr>
                <td class="label">สั่งจาก / Supplier:</td>
                <td><b>{po.get('supplier_name', '-')}</b></td>
            </tr>
            {f'<tr><td></td><td>{supplier_contact}</td></tr>' if supplier_contact else ''}
        </table>
    </div>

    {exp_date_html}

    <h3>รายการสั่งซื้อ</h3>
    <table class="items">
        <tr>
            <th style="width:6%">#</th>
            <th style="width:42%">รายการ</th>
            <th style="width:12%">จำนวน</th>
            <th style="width:10%">หน่วย</th>
            <th style="width:15%">ราคา/หน่วย</th>
            <th style="width:15%">รวม</th>
        </tr>
        {items_rows}
    </table>

    <table class="summary">
        {summary_rows}
    </table>
    <div class="clearfix"></div>

    {notes_html}

    <table class="signatures">
        <tr>
            <td><div class="label">ผู้สั่งซื้อ / Buyer</div></td>
            <td style="width:30%"></td>
            <td><div class="label">ผู้ขาย / Supplier</div></td>
        </tr>
        <tr>
            <td><div class="line"></div><div class="small">Lab Parfumo</div></td>
            <td></td>
            <td><div class="line"></div><div class="small">(____________________)</div></td>
        </tr>
        <tr>
            <td><div class="small">วันที่ ____/____/______</div></td>
            <td></td>
            <td><div class="small">วันที่ ____/____/______</div></td>
        </tr>
    </table>

    <div class="footer">Lab Parfumo | {COMPANY_INFO['website']}</div>
    <div class="footer-meta">พิมพ์เมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

    </body></html>
    """

    return HTML(string=html).write_pdf()


# ==================================================================
# GRN PDF (ใบรับของ)
# ==================================================================

def generate_grn_pdf(po: dict, delivery: dict) -> bytes:
    """สร้าง PDF ใบรับของ"""

    grn_no = f"GRN-{po.get('po_number', '-')}-{delivery.get('delivery_no', 1):02d}"

    # Items rows
    items_rows = ""
    for i, item in enumerate(delivery.get('items_received', []), 1):
        damaged = int(item.get('qty_damaged', 0) or 0)
        damage_html = f'<span class="red">{damaged}</span>' if damaged > 0 else "0"
        items_rows += f"""
        <tr>
            <td class="center">{i}</td>
            <td>{item.get('name', '')}</td>
            <td class="num">{item.get('qty_ordered', 0):,.0f}</td>
            <td class="num">{item.get('qty_received', 0):,.0f}</td>
            <td class="num">{damage_html}</td>
            <td class="center">{item.get('unit', '')}</td>
            <td>{item.get('condition_notes', '') or '-'}</td>
        </tr>"""

    # Condition badge
    cond = delivery.get('overall_condition', 'ปกติ')
    if cond == 'ปกติ':
        cond_class = "badge-ok"
    elif cond == 'มีปัญหาบางส่วน':
        cond_class = "badge-warn"
    else:
        cond_class = "badge-error"

    # Issue
    issue_html = ""
    if delivery.get('issue_description'):
        issue_html = f"<p><b>ปัญหา:</b> <span class='red'>{delivery['issue_description']}</span></p>"

    # Notes
    notes_html = ""
    if delivery.get('notes'):
        notes_html = f'<div class="notes"><b>หมายเหตุ:</b> {delivery["notes"]}</div>'

    # Images
    images_html = ""
    image_urls = delivery.get('image_urls') or []
    if image_urls:
        images_html = f'<h3>รูปภาพ ({len(image_urls)} รูป)</h3><div class="image-grid">'
        for url in image_urls[:9]:
            images_html += f'<img src="{url}" />'
        images_html += '</div>'

    html = f"""
    <!DOCTYPE html>
    <html><head><meta charset="utf-8"><style>{_base_css()}</style></head>
    <body>

    <table class="header-table">
        <tr>
            <td class="left-col">{_company_header_html()}</td>
            <td class="right-col">
                <p class="doc-title">ใบรับของ</p>
                <div class="small">GOODS RECEIVED NOTE</div>
                <div class="doc-info"><b>เลขที่:</b> {grn_no}</div>
                <div class="doc-info"><b>วันที่:</b> {_fmt_date(delivery.get('received_date'))}</div>
            </td>
        </tr>
    </table>
    <hr class="header-divider"/>

    <div class="info-box">
        <table>
            <tr><td class="label">อ้างอิง PO:</td><td>{po.get('po_number', '-')}</td></tr>
            <tr><td class="label">Supplier:</td><td>{po.get('supplier_name', '-')}</td></tr>
            <tr><td class="label">ผู้รับของ:</td><td>{delivery.get('received_by_name', '-')}</td></tr>
            <tr><td class="label">วันที่รับ:</td><td>{_fmt_date(delivery.get('received_date'))}</td></tr>
        </table>
    </div>

    <p><b>สภาพรวม:</b> <span class="badge {cond_class}">{cond}</span></p>
    {issue_html}

    <h3>รายการที่รับ</h3>
    <table class="items">
        <tr>
            <th style="width:5%">#</th>
            <th style="width:32%">รายการ</th>
            <th style="width:11%">สั่ง</th>
            <th style="width:11%">รับจริง</th>
            <th style="width:11%">เสียหาย</th>
            <th style="width:10%">หน่วย</th>
            <th style="width:20%">หมายเหตุ</th>
        </tr>
        {items_rows}
    </table>

    {notes_html}

    {images_html}

    <table class="signatures">
        <tr>
            <td><div class="label">ผู้รับของ</div></td>
            <td style="width:30%"></td>
            <td><div class="label">ผู้ตรวจสอบ</div></td>
        </tr>
        <tr>
            <td>
                <div class="line"></div>
                <div class="small">({delivery.get('received_by_name', '')})</div>
            </td>
            <td></td>
            <td>
                <div class="line"></div>
                <div class="small">(____________________)</div>
            </td>
        </tr>
    </table>

    <div class="footer">Lab Parfumo | {COMPANY_INFO['website']}</div>
    <div class="footer-meta">พิมพ์เมื่อ: {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>

    </body></html>
    """

    return HTML(string=html).write_pdf()
