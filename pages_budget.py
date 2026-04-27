"""pages_budget.py — Budget Tracking + Alerts + Period Reports (NEW FEATURE)

⭐ Features:
- Tab 1: ตั้ง/แก้ไข budget (รายเดือน/ไตรมาส/ปี)
- Tab 2: Dashboard สถานะ budget vs actual + alerts (>80% / >95% / >100%)
- Tab 3: ส่งออก PDF รายงาน
"""
from datetime import date, datetime
from typing import Optional

import streamlit as st

import database as db
from helpers import (
    is_admin, uname, esc,
    fmt_money, safe_float, safe_int,
    log,
)


THAI_MONTHS = [
    "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน",
    "พฤษภาคม", "มิถุนายน", "กรกฎาคม", "สิงหาคม",
    "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def render_budget():
    """หน้าหลัก: Budget tracking"""
    if not is_admin():
        st.error("❌ เฉพาะแอดมิน")
        return

    st.markdown("""
    <div class="page-title-block">
        <div class="page-title-text">💰 งบประมาณ + รายงาน</div>
        <div class="page-title-sub">ตั้งงบ ติดตามการใช้จ่าย และส่งออกรายงาน PDF</div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "✏️ ตั้งงบประมาณ", "📄 รายงาน PDF"])

    with tab1:
        _render_budget_dashboard()
    with tab2:
        _render_budget_form()
    with tab3:
        _render_period_report()


# ==================================================================
# TAB 1: Dashboard — สถานะ Budget vs Actual
# ==================================================================
def _render_budget_dashboard():
    today = date.today()
    
    c1, c2 = st.columns([1, 1])
    with c1:
        year = st.selectbox(
            "ปี",
            options=list(range(today.year - 2, today.year + 2)),
            index=2,  # default = ปีปัจจุบัน
            key="budget_dash_year",
        )
    with c2:
        month_idx = st.selectbox(
            "เดือน",
            options=list(range(1, 13)),
            index=today.month - 1,
            format_func=lambda m: f"{m:02d} - {THAI_MONTHS[m-1]}",
            key="budget_dash_month",
        )

    statuses = db.get_budget_status_for_dashboard(year=year, month=month_idx)

    if not statuses:
        st.info(
            f"💡 ยังไม่มีงบประมาณสำหรับ **{THAI_MONTHS[month_idx-1]} {year}** — "
            "ตั้งใน tab \"ตั้งงบประมาณ\""
        )
        return

    # ===== Alerts =====
    over_count = sum(1 for s in statuses if s['status'] == 'over')
    critical_count = sum(1 for s in statuses if s['status'] == 'critical')
    warning_count = sum(1 for s in statuses if s['status'] == 'warning')

    if over_count > 0:
        st.error(
            f"🚨 **เกินงบประมาณ {over_count} รายการ** — "
            "กรุณาตรวจสอบและพิจารณาจัดสรรเพิ่ม"
        )
    if critical_count > 0:
        st.warning(
            f"⚠️ **ใกล้เต็มงบ {critical_count} รายการ** (ใช้ไป >95%)"
        )
    if warning_count > 0:
        st.info(
            f"ℹ️ {warning_count} รายการใช้งบเกิน 80% แล้ว"
        )

    st.divider()

    # ===== Summary KPI =====
    total_budget = sum(s['budget'] for s in statuses)
    total_actual = sum(s['actual'] for s in statuses)
    total_remaining = total_budget - total_actual

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 งบรวม", fmt_money(total_budget, 0))
    m2.metric("📊 ใช้ไป", fmt_money(total_actual, 0))
    m3.metric(
        "💵 คงเหลือ",
        fmt_money(total_remaining, 0),
        delta=None if total_remaining >= 0 else "เกินงบ",
    )
    pct = (total_actual / total_budget * 100) if total_budget else 0
    m4.metric("📈 % ที่ใช้", f"{pct:.1f}%")

    st.divider()

    # ===== List of budgets with progress bars =====
    st.markdown("#### 📋 รายละเอียด")

    for s in statuses:
        with st.container(border=True):
            cc1, cc2 = st.columns([3, 1])
            with cc1:
                # ⭐ ESCAPED — category may have user input
                cat = esc(s['category'])
                period = esc(s['period'])
                ptype_th = {
                    'monthly': '📅 รายเดือน',
                    'quarterly': '📆 รายไตรมาส',
                    'yearly': '🗓️ รายปี',
                }.get(s['type'], s['type'])
                st.markdown(
                    f"**{cat}** — {ptype_th} ({period})",
                )

                # Progress bar
                pct = min(s['percent'], 100)
                bar_color = {
                    'ok': '#1D9E75',
                    'warning': '#D97706',
                    'critical': '#DC2626',
                    'over': '#7F1D1D',
                }.get(s['status'], '#888')
                st.markdown(
                    f"""
                    <div style="background:#E2E8F0; border-radius:8px;
                                height:20px; overflow:hidden; margin:6px 0;">
                        <div style="background:{bar_color}; width:{pct}%;
                                    height:100%; transition: width 0.3s;"></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                cap_color = '#A32D2D' if s['status'] == 'over' else '#666'
                st.caption(
                    f"<span style='color:{cap_color};'>"
                    f"<b>{fmt_money(s['actual'], 0)}</b> / {fmt_money(s['budget'], 0)} "
                    f"({s['percent']:.1f}%)"
                    f"</span>",
                    unsafe_allow_html=True,
                )

            with cc2:
                if s['status'] == 'over':
                    st.error(f"🚨 เกิน")
                elif s['status'] == 'critical':
                    st.warning(f"⚠️ ใกล้เต็ม")
                elif s['status'] == 'warning':
                    st.info(f"📊 >80%")
                else:
                    st.success(f"✅ ปกติ")

                # ปุ่มแก้ไข
                if st.button("✏️", key=f"edit_b_{s['id']}",
                             use_container_width=True,
                             help="แก้ไขงบประมาณ"):
                    st.session_state['edit_budget_id'] = s['id']
                    st.session_state['active_budget_tab'] = 1
                    st.rerun()


# ==================================================================
# TAB 2: ตั้ง/แก้ไข Budget
# ==================================================================
def _render_budget_form():
    st.caption(
        "ตั้งงบประมาณรายเดือน รายไตรมาส หรือรายปี — "
        "ตั้งงบรวมทั้งบริษัท หรือแยกตามหมวดสินค้าได้"
    )

    today = date.today()

    # ===== List existing + Add new =====
    existing = db.list_budgets(year=today.year)
    
    if existing:
        st.markdown(f"#### 📋 งบประมาณปี {today.year}")
        for b in existing:
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                with c1:
                    period_disp = ""
                    if b['period_type'] == 'monthly':
                        m = b.get('period_month', 1)
                        period_disp = f"📅 {THAI_MONTHS[m-1]} {b['period_year']}"
                    elif b['period_type'] == 'quarterly':
                        m = b.get('period_month', 1)
                        q = (m - 1) // 3 + 1
                        period_disp = f"📆 ไตรมาส {q}/{b['period_year']}"
                    else:
                        period_disp = f"🗓️ ปี {b['period_year']}"
                    st.markdown(f"**{period_disp}**")
                    cat = b.get('category') or '🌐 รวมทั้งหมด'
                    st.caption(f"📂 {esc(cat)}")
                with c2:
                    st.markdown(f"### {fmt_money(b['amount'], 0)}")
                with c3:
                    if b.get('notes'):
                        st.caption(f"📝 {esc(b['notes'])}")
                    if b.get('created_by_name'):
                        st.caption(f"👤 {esc(b['created_by_name'])}")
                with c4:
                    del_key = f"del_budget_{b['id']}"
                    if st.session_state.get(del_key):
                        if st.button("⚠️ ยืนยัน",
                                     key=f"cd_{b['id']}",
                                     use_container_width=True,
                                     type="primary"):
                            if db.delete_budget(b['id']):
                                st.session_state.pop(del_key, None)
                                st.success("ลบแล้ว")
                                st.rerun()
                    else:
                        if st.button("🗑️", key=f"d_{b['id']}",
                                     use_container_width=True):
                            st.session_state[del_key] = True
                            st.rerun()
        st.divider()

    # ===== Add/Edit form =====
    edit_id = st.session_state.get('edit_budget_id')
    edit_b = None
    if edit_id:
        edit_b = next((b for b in existing if b['id'] == edit_id), None)

    title = "✏️ แก้ไขงบประมาณ" if edit_b else "➕ ตั้งงบประมาณใหม่"
    st.markdown(f"#### {title}")

    with st.form("budget_form"):
        c1, c2 = st.columns(2)
        with c1:
            period_type = st.selectbox(
                "ประเภท",
                options=['monthly', 'quarterly', 'yearly'],
                format_func=lambda x: {
                    'monthly': '📅 รายเดือน',
                    'quarterly': '📆 รายไตรมาส',
                    'yearly': '🗓️ รายปี',
                }[x],
                index=(['monthly', 'quarterly', 'yearly'].index(edit_b['period_type'])
                       if edit_b else 0),
            )
        with c2:
            year = st.number_input(
                "ปี",
                min_value=today.year - 2,
                max_value=today.year + 5,
                value=edit_b['period_year'] if edit_b else today.year,
                step=1,
            )

        if period_type == 'monthly':
            month = st.selectbox(
                "เดือน",
                options=list(range(1, 13)),
                format_func=lambda m: f"{m:02d} - {THAI_MONTHS[m-1]}",
                index=(edit_b['period_month'] - 1
                       if edit_b and edit_b.get('period_month')
                       else today.month - 1),
            )
        elif period_type == 'quarterly':
            q = st.selectbox(
                "ไตรมาส",
                options=[1, 2, 3, 4],
                format_func=lambda q: f"Q{q} (เดือน {(q-1)*3+1}-{q*3})",
                index=((edit_b['period_month'] - 1) // 3
                       if edit_b and edit_b.get('period_month')
                       else (today.month - 1) // 3),
            )
            month = (q - 1) * 3 + 1
        else:
            month = None

        # Category — รวมหรือแยกหมวด
        categories = ['🌐 รวมทั้งหมด'] + db.get_categories()
        cur_cat = edit_b.get('category') if edit_b else None
        cat_idx = (categories.index(cur_cat) if cur_cat in categories else 0)
        cat_label = st.selectbox(
            "หมวดสินค้า",
            options=categories,
            index=cat_idx,
            help="เลือก 'รวมทั้งหมด' = งบครอบคลุมทุกหมวด",
        )
        category = None if cat_label == '🌐 รวมทั้งหมด' else cat_label

        amount = st.number_input(
            "จำนวนเงิน (บาท) *",
            min_value=0.0,
            value=safe_float(edit_b['amount'] if edit_b else 100000.0),
            step=10000.0,
            format="%.2f",
        )

        notes = st.text_area(
            "บันทึก (ถ้ามี)",
            value=edit_b.get('notes', '') if edit_b else '',
            height=68,
        )

        sc1, sc2 = st.columns(2)
        with sc1:
            submitted = st.form_submit_button(
                "💾 บันทึก", type="primary",
                use_container_width=True,
            )
        with sc2:
            if edit_b:
                cancelled = st.form_submit_button(
                    "❌ ยกเลิก", use_container_width=True,
                )
            else:
                cancelled = False

        if submitted:
            if amount <= 0:
                st.error("กรุณากรอกจำนวนเงินมากกว่า 0")
            else:
                ok = db.upsert_budget(
                    period_type=period_type,
                    year=year,
                    amount=amount,
                    month=month,
                    category=category,
                    notes=notes,
                    created_by_name=uname(),
                )
                if ok:
                    st.success("✅ บันทึกแล้ว")
                    st.session_state.pop('edit_budget_id', None)
                    st.rerun()
                else:
                    st.error("⚠️ บันทึกไม่สำเร็จ — อาจมีงบนี้อยู่แล้ว")

        if cancelled:
            st.session_state.pop('edit_budget_id', None)
            st.rerun()


# ==================================================================
# TAB 3: Period PDF Report
# ==================================================================
def _render_period_report():
    st.caption(
        "ส่งออกรายงาน PDF สำหรับช่วงเวลาที่เลือก — "
        "รวม KPI, top supplier, top items, สถานะ และงบประมาณ"
    )

    today = date.today()

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        report_type = st.selectbox(
            "ประเภทรายงาน",
            options=['monthly', 'quarterly', 'yearly', 'custom'],
            format_func=lambda x: {
                'monthly': '📅 รายเดือน',
                'quarterly': '📆 รายไตรมาส',
                'yearly': '🗓️ รายปี',
                'custom': '🎯 กำหนดเอง',
            }[x],
        )
    with c2:
        year = st.number_input(
            "ปี",
            min_value=today.year - 5,
            max_value=today.year,
            value=today.year,
            step=1,
        )

    period_label = ""
    start_date = end_date = None

    if report_type == 'monthly':
        with c3:
            month = st.selectbox(
                "เดือน",
                options=list(range(1, 13)),
                format_func=lambda m: f"{m:02d}",
                index=today.month - 1,
            )
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, month + 1, 1) - __import__('datetime').timedelta(days=1)
        period_label = f"{THAI_MONTHS[month-1]} {year}"

    elif report_type == 'quarterly':
        with c3:
            q = st.selectbox(
                "ไตรมาส",
                options=[1, 2, 3, 4],
                format_func=lambda q: f"Q{q}",
            )
        start_month = (q - 1) * 3 + 1
        end_month = q * 3
        start_date = date(year, start_month, 1)
        if end_month == 12:
            end_date = date(year, 12, 31)
        else:
            end_date = date(year, end_month + 1, 1) - __import__('datetime').timedelta(days=1)
        period_label = f"ไตรมาส {q}/{year} ({THAI_MONTHS[start_month-1][:3]}-{THAI_MONTHS[end_month-1][:3]})"

    elif report_type == 'yearly':
        start_date = date(year, 1, 1)
        end_date = date(year, 12, 31)
        period_label = f"ปี {year}"

    elif report_type == 'custom':
        cc1, cc2 = st.columns(2)
        with cc1:
            start_date = st.date_input("ตั้งแต่", value=today.replace(day=1))
        with cc2:
            end_date = st.date_input("ถึง", value=today)
        period_label = f"{start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}"

    if not (start_date and end_date):
        return

    if start_date > end_date:
        st.error("⚠️ วันเริ่มต้นต้องน้อยกว่าหรือเท่ากับวันสุดท้าย")
        return

    st.divider()

    # Preview
    pos = db.get_purchase_orders(role='admin', limit=1000)
    filtered = [p for p in pos
                if start_date.isoformat() <= p.get('created_at', '')[:10] <= end_date.isoformat()]

    n = len(filtered)
    valid = [p for p in filtered if p.get('status') != 'ยกเลิก']
    total = sum(safe_float(p.get('total', 0)) for p in valid)

    pc1, pc2, pc3 = st.columns(3)
    pc1.metric("PO ในช่วงนี้", n)
    pc2.metric("ยอดรวม", fmt_money(total, 0))
    pc3.metric("เฉลี่ย/ใบ", fmt_money((total/len(valid)) if valid else 0, 0))

    if n == 0:
        st.info("ไม่มี PO ในช่วงเวลานี้ — เปลี่ยนช่วงและลองใหม่")
        return

    # Get budgets for this period (if monthly only)
    budgets = None
    if report_type == 'monthly':
        budgets = db.get_budget_status_for_dashboard(
            year=year, month=start_date.month
        )

    include_budgets = st.checkbox(
        "📊 รวมข้อมูลงบประมาณในรายงาน",
        value=bool(budgets),
        disabled=not budgets,
        help="ทำงานได้กับรายเดือนเท่านั้น" if not budgets else None,
    )

    # Generate PDF button
    if st.button("📥 สร้าง PDF Report", type="primary",
                 use_container_width=True):
        try:
            from pdf_generator import generate_period_report_pdf
            with st.spinner("กำลังสร้าง PDF..."):
                pdf_bytes = generate_period_report_pdf(
                    period_label=period_label,
                    start_date=start_date,
                    end_date=end_date,
                    pos=filtered,
                    budgets=budgets if include_budgets else None,
                    generated_by=uname(),
                )
            
            filename = f"report_{period_label.replace('/', '-').replace(' ', '_')}.pdf"
            st.download_button(
                "⬇️ ดาวน์โหลด",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
            st.success(f"✅ สร้างรายงานสำเร็จ ({len(pdf_bytes):,} bytes)")
        except Exception as e:
            log.exception("generate_period_report_pdf failed")
            st.error(f"⚠️ สร้าง PDF ไม่สำเร็จ: {esc(str(e))}")
