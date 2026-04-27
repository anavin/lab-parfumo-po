"""pages_po.py - List, Create, View PO"""
from datetime import date, datetime, timedelta

import streamlit as st
import pandas as pd

import database as db
from helpers import (current_user, is_admin, uid, uname, urole,
                      fmt_date, fmt_dt,
                      show_status_badge, show_status_pill, status_pill_html,
                      days_indicator,
                      show_empty_state)


# ==================================================================
# PO List
# ==================================================================

def render_pending_receipt():
    """หน้า PO ที่รอรับของ — staff ทุกคนเห็น"""
    user = current_user()

    pos = db.get_pos_pending_receipt()

    st.markdown(f"""
    <div class="page-title-block">
        <div class="page-title-text">รอรับของ</div>
        <div class="page-title-sub">{len(pos)} ใบที่กำลังจะมาถึง • ตรวจรับเมื่อของถึง</div>
    </div>
    """, unsafe_allow_html=True)

    if not pos:
        show_empty_state(
            "🎉",
            "ไม่มี PO รอรับของ",
            "ทุกอย่างเสร็จเรียบร้อยแล้ว! ถ้ามี PO ใหม่ที่กำลังขนส่ง จะปรากฏที่นี่",
        )
        return

    # ----- Filter -----
    today = date.today()
    overdue = []
    today_due = []
    upcoming = []
    later = []
    no_date = []

    for p in pos:
        ed = p.get('expected_date')
        if not ed:
            no_date.append(p)
            continue
        try:
            ed_date = date.fromisoformat(ed)
            days = (ed_date - today).days
            if days < 0:
                overdue.append(p)
            elif days == 0:
                today_due.append(p)
            elif days <= 3:
                upcoming.append(p)
            else:
                later.append(p)
        except Exception:
            no_date.append(p)

    # ----- KPI -----
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("⚠️ เลยกำหนด", len(overdue))
    m2.metric("📅 วันนี้", len(today_due))
    m3.metric("⏰ ใน 3 วัน", len(upcoming))
    m4.metric("📦 ทั้งหมด", len(pos))

    st.divider()

    # ----- Search -----
    col1, col2 = st.columns([2, 1])
    with col1:
        search = st.text_input(
            "🔍 ค้นหา",
            placeholder="เลข PO / Supplier / ชื่อสินค้า",
            key="pr_search",
        ).strip().lower()
    with col2:
        sort_by = st.selectbox(
            "เรียงตาม",
            ["ใกล้ครบกำหนด", "PO ใหม่สุด", "PO เก่าสุด"],
            key="pr_sort",
        )

    # apply search
    filtered = pos
    if search:
        filtered = [
            p for p in pos
            if search in (p.get('po_number') or '').lower()
            or search in (p.get('supplier_name') or '').lower()
            or search in (p.get('notes') or '').lower()
            or any(search in (it.get('name') or '').lower()
                    for it in (p.get('items') or []))
        ]

    # apply sort
    if sort_by == "ใกล้ครบกำหนด":
        # เรียง: เลยกำหนด → วันนี้ → ใกล้ (3 วัน) → อนาคต → ไม่ระบุ
        ordered = []
        for group in (overdue, today_due, upcoming, later, no_date):
            ordered += [p for p in group if p in filtered]
        filtered = ordered
    elif sort_by == "PO ใหม่สุด":
        filtered = sorted(filtered,
                            key=lambda p: p.get('created_at', ''),
                            reverse=True)
    else:  # PO เก่าสุด
        filtered = sorted(filtered, key=lambda p: p.get('created_at', ''))

    st.caption(f"พบ **{len(filtered)}** รายการ")

    if not filtered:
        st.info("ไม่พบ PO ที่ตรงกับการค้นหา")
        return

    # ----- รายการ -----
    is_adm = is_admin()
    for po in filtered:
        _render_pending_card(po, today, is_adm)


def _render_pending_card(po, today, is_adm):
    """การ์ด PO รอรับของ — แสดง info สำคัญ + ปุ่มรับของด่วน"""
    ed = po.get('expected_date')
    days = None
    badge_html = ""

    if ed:
        try:
            ed_date = date.fromisoformat(ed)
            days = (ed_date - today).days
            if days < 0:
                badge_html = (f'<span style="background:#FCEBEB; '
                              f'color:#A32D2D; padding:2px 10px; '
                              f'border-radius:10px; font-size:11px; '
                              f'font-weight:500;">🚨 เลย {-days} วัน</span>')
            elif days == 0:
                badge_html = ('<span style="background:#FAEEDA; '
                              'color:#BA7517; padding:2px 10px; '
                              'border-radius:10px; font-size:11px; '
                              'font-weight:500;">📅 วันนี้</span>')
            elif days <= 3:
                badge_html = (f'<span style="background:#FAEEDA; '
                              f'color:#BA7517; padding:2px 10px; '
                              f'border-radius:10px; font-size:11px; '
                              f'font-weight:500;">⏰ อีก {days} วัน</span>')
            else:
                badge_html = (f'<span style="background:#E8F2EE; '
                              f'color:#0F6E56; padding:2px 10px; '
                              f'border-radius:10px; font-size:11px;">'
                              f'📅 อีก {days} วัน</span>')
        except Exception:
            pass

    with st.container(border=True):
        c1, c2, c3 = st.columns([3, 4, 2])

        with c1:
            st.markdown(f"### {po['po_number']}")
            show_status_badge(po['status'])
            st.markdown(badge_html, unsafe_allow_html=True)
            st.caption(f"📅 สั่ง: {fmt_date(po.get('ordered_date'))}")
            if ed:
                st.caption(f"🎯 คาด: {fmt_date(ed)}")

        with c2:
            # supplier — admin only
            if is_adm and po.get('supplier_name'):
                st.markdown(f"🏭 **{po['supplier_name']}**")
            if po.get('tracking_number'):
                st.caption(f"📋 Tracking: `{po['tracking_number']}`")

            # รายการสินค้า (ย่อ)
            items = po.get('items', [])
            items_summary = ", ".join(
                f"{it.get('name', '')} × {it.get('qty', 0):,.0f}"
                for it in items[:3]
            )
            if len(items) > 3:
                items_summary += f" และอีก {len(items) - 3} รายการ"
            if items_summary:
                st.caption(f"📦 {items_summary}")
            st.caption(f"👤 ผู้สั่ง: {po.get('created_by_name', '-')}")

        with c3:
            if st.button("📦 รับของ",
                          key=f"recv_{po['id']}",
                          type="primary",
                          use_container_width=True):
                st.session_state['view_po_id'] = po['id']
                st.session_state['mode'] = 'po_view'
                st.session_state['action_form'] = 'receive'
                st.rerun()
            if st.button("👁️ ดูรายละเอียด",
                          key=f"view_{po['id']}",
                          use_container_width=True):
                st.session_state['view_po_id'] = po['id']
                st.session_state['mode'] = 'po_view'
                st.session_state['action_form'] = None
                st.rerun()


def render_po_list():
    user = current_user()
    role = user.get('role', '')

    pos = db.get_purchase_orders(user_id=uid(), role=role)

    # Page title row
    last_update_str = "อัปเดตล่าสุด เพิ่งอัปเดต"
    title_col, btn_col = st.columns([5, 1])
    with title_col:
        st.markdown(f"""
        <div class="page-title-block">
            <div class="page-title-text">ใบสั่งซื้อทั้งหมด</div>
            <div class="page-title-sub">{len(pos)} ใบ • {last_update_str}</div>
        </div>
        """, unsafe_allow_html=True)
    with btn_col:
        if st.button("➕ สร้างใหม่", type="primary", use_container_width=True,
                     key="po_list_create"):
            st.session_state['mode'] = 'po_create'
            st.session_state['po_items'] = []
            st.rerun()

    if not pos:
        show_empty_state(
            "📋",
            "ยังไม่มีใบสั่งซื้อ",
            "เริ่มต้นง่ายๆ — สร้างใบ PO ใหม่ ระบบจะแจ้งแอดมินอัตโนมัติ",
            "➕ สร้างใบ PO ใหม่",
            ('po_create', {'po_items': []}),
        )
        return

    # ===== Filter chips (status counts) =====
    status_count = {}
    for p in pos:
        status_count[p['status']] = status_count.get(p['status'], 0) + 1

    preset_filter = st.session_state.pop('po_list_filter', None)
    if 'po_list_active_filter' not in st.session_state:
        st.session_state['po_list_active_filter'] = preset_filter or "ทั้งหมด"
    elif preset_filter:
        st.session_state['po_list_active_filter'] = preset_filter

    active = st.session_state['po_list_active_filter']

    # Search box on top
    search = st.text_input("🔍 ค้นหา", placeholder="เลข PO / supplier / สินค้า / ผู้สร้าง...",
                           key="po_search", label_visibility="collapsed")

    # Filter chips row
    chip_options = [("ทั้งหมด", len(pos))] + [
        (s, status_count.get(s, 0))
        for s in db.PO_STATUSES
        if status_count.get(s, 0) > 0
    ]

    chip_cols = st.columns(min(len(chip_options), 7))
    for i, (s, cnt) in enumerate(chip_options[:7]):
        with chip_cols[i]:
            label = f"{s} • {cnt}"
            if st.button(
                label,
                key=f"chip_{s}",
                type="primary" if active == s else "secondary",
                use_container_width=True,
            ):
                st.session_state['po_list_active_filter'] = s
                st.rerun()

    # ===== Apply filter =====
    filtered = pos[:]
    if active != "ทั้งหมด":
        filtered = [p for p in filtered if p['status'] == active]
    if search:
        s = search.lower()
        filtered = [p for p in filtered
                    if s in p.get('po_number', '').lower()
                    or s in (p.get('notes') or '').lower()
                    or s in (p.get('supplier_name') or '').lower()
                    or s in (p.get('created_by_name') or '').lower()
                    or any(s in (it.get('name') or '').lower()
                            for it in (p.get('items') or []))]

    st.caption(f"พบ {len(filtered)} ใบ")

    # ===== Compact PO rows =====
    for po in filtered:
        n_items = len(po.get('items', []))
        items_preview = ", ".join(
            (i.get('name', '') for i in po.get('items', [])[:2])
        )
        if n_items > 2:
            items_preview += f", +{n_items - 2}"

        # Build supplier or "(ยังไม่ระบุ)"
        if is_admin():
            sup = po.get('supplier_name') or '(ยังไม่ระบุ supplier)'
        else:
            sup = po.get('supplier_name') or '—'

        amt_str = f"฿{po['total']:,.0f}" if (is_admin() and po.get('total')) else "—"
        date_str = fmt_date(po.get('created_at'))[5:].replace('-', '/') if po.get('created_at') else ""
        creator = po.get('created_by_name', '—')

        # Container with compact grid
        with st.container(border=True):
            c1, c2, c3, c4, c5, c6 = st.columns([1.4, 3, 1.6, 1, 1.3, 0.8])
            with c1:
                st.markdown(
                    f"<div class='po-num'>{po['po_number']}</div>",
                    unsafe_allow_html=True,
                )
            with c2:
                st.markdown(
                    f"<div style='font-size:13px; font-weight:600; color:var(--slate-800);'>{sup}</div>"
                    f"<div style='font-size:11px; color:var(--slate-500);'>📦 {n_items} รายการ • {items_preview}</div>",
                    unsafe_allow_html=True,
                )
            with c3:
                show_status_pill(po['status'])
            with c4:
                amt_color = "var(--slate-900)" if amt_str != "—" else "var(--slate-400)"
                st.markdown(
                    f"<div style='text-align:right; font-weight:700; color:{amt_color}; "
                    f"font-variant-numeric:tabular-nums;'>{amt_str}</div>",
                    unsafe_allow_html=True,
                )
            with c5:
                st.markdown(
                    f"<div style='font-size:11px; color:var(--slate-500);'>📅 {date_str}</div>"
                    f"<div style='font-size:11px; color:var(--slate-500);'>👤 {creator}</div>",
                    unsafe_allow_html=True,
                )
            with c6:
                if st.button("ดู →", key=f"v_{po['id']}",
                              use_container_width=True):
                    st.session_state['view_po_id'] = po['id']
                    st.session_state['mode'] = 'po_view'
                    st.rerun()





# ==================================================================
# Create PO (สำหรับผู้สั่ง — ไม่ใส่ราคา/supplier)
# ==================================================================

def render_po_create():
    user = current_user()

    # ===== Load Draft (ครั้งแรกเข้าหน้า) =====
    draft_loaded_key = f'_draft_loaded_{uid()}'
    if not st.session_state.get(draft_loaded_key):
        draft = db.get_po_draft(uid())
        if draft and draft.get('items'):
            st.session_state['po_items'] = draft['items']
            if draft.get('notes'):
                st.session_state['_po_notes_value'] = draft['notes']
        st.session_state[draft_loaded_key] = True

    # ===== Breadcrumb + Header =====
    st.markdown("""
    <div style="color:var(--slate-500); font-size:12px; margin-bottom:10px;">
        <span style="color:var(--brand-700); cursor:pointer;">ใบ PO</span>
        <span style="margin:0 6px;">›</span>
        <span>สร้างใหม่</span>
    </div>
    """, unsafe_allow_html=True)

    title_col, save_col = st.columns([5, 2])
    with title_col:
        st.markdown("""
        <div class="page-title-block">
            <div class="page-title-text">สร้างใบสั่งซื้อใหม่</div>
            <div class="page-title-sub">เลือกสินค้าจาก catalog หรือพิมพ์ชื่อเอง</div>
        </div>
        """, unsafe_allow_html=True)
    with save_col:
        if st.session_state.get('po_items'):
            now_str = datetime.now().strftime('%H:%M')
            st.markdown(f"""
            <div style="text-align:right; font-size:12px; color:var(--success);
                        font-weight:600; padding-top:14px;">
                💾 บันทึกร่างอัตโนมัติ • {now_str}
            </div>
            """, unsafe_allow_html=True)

    # Action row: clear + back
    if st.session_state.get('po_items'):
        c1, c2, c3 = st.columns([4, 1, 1])
        with c1:
            st.markdown("")
        with c2:
            if st.button("🗑️ ล้าง", use_container_width=True,
                          key="po_create_clear"):
                db.delete_po_draft(uid())
                st.session_state['po_items'] = []
                st.session_state['_po_notes_value'] = ''
                st.session_state.pop(draft_loaded_key, None)
                st.session_state.pop('po_create_notes', None)
                st.success("ล้างแล้ว")
                st.rerun()
        with c3:
            if st.button("← กลับ", use_container_width=True,
                          key="po_create_back"):
                st.session_state['mode'] = 'po_list'
                st.rerun()
    else:
        if st.button("← กลับ", key="po_create_back2"):
            st.session_state['mode'] = 'po_list'
            st.rerun()

    eq_list = db.get_equipment_list(active_only=True)

    # ===== Search + Filter =====
    st.markdown("### 📦 รายการที่ต้องการ")

    if eq_list:
        col1, col2 = st.columns([2, 1])
        with col1:
            search = st.text_input(
                "🔍 ค้นหา",
                placeholder="พิมพ์ชื่อสินค้าหรือ SKU",
                key="po_create_search",
            ).strip().lower()
        with col2:
            categories = sorted(set(e.get('category', '-') for e in eq_list))
            cat_filter = st.selectbox(
                "📂 หมวดหมู่",
                options=["ทั้งหมด"] + categories,
                key="po_create_cat",
            )

        # filter
        filtered = eq_list[:]
        if search:
            filtered = [
                e for e in filtered
                if search in (e.get('name') or '').lower()
                or search in (e.get('sku') or '').lower()
                or search in (e.get('description') or '').lower()
            ]
        if cat_filter != "ทั้งหมด":
            filtered = [e for e in filtered if e.get('category') == cat_filter]

        # set ของ id ที่เลือกแล้ว → ใช้แสดงสถานะการ์ด
        selected_ids = {it['equipment_id'] for it in st.session_state['po_items']
                        if it.get('equipment_id')}

        if not filtered:
            st.info("ไม่พบรายการที่ตรงกับเงื่อนไข — ลองเปลี่ยนคำค้นหา")
        else:
            st.caption(f"พบ {len(filtered)} รายการ — คลิกการ์ดเพื่อเพิ่ม (จำนวนเริ่มต้น = 1)")

            # ===== Catalog Cards =====
            for row_start in range(0, len(filtered), 3):
                row = filtered[row_start:row_start + 3]
                cols = st.columns(3)
                for col, eq in zip(cols, row):
                    with col:
                        _render_eq_card(eq, eq['id'] in selected_ids)
    else:
        st.info("ℹ️ ยังไม่มีอุปกรณ์ในระบบ — ติดต่อแอดมิน หรือใช้ \"พิมพ์ชื่อเอง\" ด้านล่าง")

    # ===== พิมพ์ชื่อเอง (custom item) =====
    st.markdown("---")
    with st.expander("✏️ พิมพ์ชื่อเอง (สำหรับรายการที่ไม่มีใน catalog)"):
        with st.form("custom_item_form", clear_on_submit=True):
            cc1, cc2, cc3 = st.columns([3, 1, 1])
            with cc1:
                custom_name = st.text_input(
                    "ชื่อรายการ *",
                    placeholder="พิมพ์ชื่ออุปกรณ์",
                )
            with cc2:
                custom_qty = st.number_input("จำนวน *", min_value=1, value=1, step=1)
            with cc3:
                custom_unit = st.text_input("หน่วย", value="ชิ้น")
            custom_note = st.text_input(
                "หมายเหตุ (ถ้ามี)",
                placeholder="เช่น สเปคพิเศษ / ยี่ห้อ / สี",
            )
            # ===== Upload รูป (ถ่ายมาให้ดู / link สั่งซื้อ) =====
            custom_imgs = st.file_uploader(
                "📷 รูปประกอบ (ถ้ามี — แนะนำมีเพื่อให้ admin เห็นว่าจะสั่งอะไร)",
                type=['jpg', 'jpeg', 'png', 'webp'],
                accept_multiple_files=True,
                key="custom_item_imgs",
            )
            if st.form_submit_button("➕ เพิ่ม", type="primary",
                                       use_container_width=True):
                if not custom_name:
                    st.error("กรุณาพิมพ์ชื่อรายการ")
                else:
                    # อัปโหลดรูป (ถ้ามี) ไป Supabase storage
                    image_urls = []
                    if custom_imgs:
                        with st.spinner("กำลังอัปโหลดรูป..."):
                            for img in custom_imgs:
                                url = db.upload_image(
                                    img.read(), img.name,
                                    bucket=db.IMG_EQ,
                                )
                                if url:
                                    image_urls.append(url)

                    st.session_state['po_items'].append({
                        'equipment_id': None,
                        'name': custom_name,
                        'unit': custom_unit or 'ชิ้น',
                        'qty': int(custom_qty),
                        'notes': custom_note,
                        'image_urls': image_urls,
                    })
                    db.save_po_draft(uid(), st.session_state['po_items'],
                                       st.session_state.get('_po_notes_value', ''))
                    if image_urls:
                        st.success(f"✅ เพิ่ม '{custom_name}' พร้อม {len(image_urls)} รูป")
                    st.rerun()

    # ===== รายการที่เลือก =====
    st.markdown("---")
    if st.session_state['po_items']:
        st.markdown(f"### 🛒 รายการในใบ PO ({len(st.session_state['po_items'])})")
        _render_selected_items(eq_list)

        st.divider()
        # ใช้ value จาก _po_notes_value (internal storage) — Streamlit จะคุม widget เอง
        notes = st.text_area("📝 หมายเหตุเพิ่มเติม (ถ้ามี)",
                              placeholder="เช่น ต้องการให้ส่งเร็ว",
                              height=80,
                              value=st.session_state.get('_po_notes_value', ''),
                              key="po_create_notes")
        # sync internal value
        st.session_state['_po_notes_value'] = notes

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("✅ บันทึกใบ PO", type="primary",
                          use_container_width=True):
                if not st.session_state['po_items']:
                    st.error("กรุณาเพิ่มรายการ")
                else:
                    new_po = db.create_purchase_order(
                        items=st.session_state['po_items'],
                        purpose="",
                        notes=notes,
                        created_by=uid(),
                        created_by_name=uname(),
                    )
                    if new_po:
                        # ลบ draft + reset (เลี่ยงแก้ widget key โดยตรง)
                        db.delete_po_draft(uid())
                        st.session_state['po_items'] = []
                        st.session_state['_po_notes_value'] = ''
                        st.session_state.pop(f'_draft_loaded_{uid()}', None)
                        # ลบ widget key เพื่อให้ form refresh
                        st.session_state.pop('po_create_notes', None)
                        st.session_state['view_po_id'] = new_po['id']
                        st.session_state['mode'] = 'po_view'
                        st.success(f"🎉 บันทึกใบ {new_po['po_number']} แล้ว")
                        st.rerun()
    else:
        st.info("👆 คลิกการ์ดสินค้าด้านบนเพื่อเริ่มเพิ่มรายการ")


def _stock_indicator(stock):
    """คืน (emoji, color, label) ตาม stock"""
    if stock is None or stock == 0:
        return ("🔴", "#A32D2D", "หมด")
    elif stock < 10:
        return ("🟡", "#BA7517", f"เหลือ {stock}")
    else:
        return ("🟢", "#1D9E75", f"คงเหลือ {stock}")


def _render_eq_card(eq, is_selected):
    """Catalog product card — B2B clean style"""
    images = list(eq.get('image_urls') or [])
    if eq.get('image_url') and eq['image_url'] not in images:
        images.insert(0, eq['image_url'])

    name = eq.get('name', '-')
    sku = eq.get('sku') or '-'
    unit = eq.get('unit', 'ชิ้น')
    cat = eq.get('category', '-')
    stock = eq.get('stock', 0) or 0

    # Stock chip
    if stock == 0:
        chip_bg, chip_color, chip_border = "var(--danger-soft)", "var(--danger)", "rgba(220, 38, 38, 0.2)"
        chip_text = f"⚠️ หมด"
    elif stock < 10:
        chip_bg, chip_color, chip_border = "var(--warning-soft)", "var(--warning)", "rgba(217, 119, 6, 0.2)"
        chip_text = f"⚠️ {stock} {unit} (ต่ำ)"
    else:
        chip_bg, chip_color, chip_border = "var(--success-soft)", "var(--success)", "rgba(5, 150, 105, 0.2)"
        chip_text = f"📦 {stock} {unit}"

    with st.container(border=True):
        # ===== Image (small thumb เพื่อ compact) =====
        if images:
            primary = images[0]
            st.markdown(
                f'<div style="width:100%; aspect-ratio:1/1; '
                f'background:var(--slate-100); border-radius:8px; overflow:hidden; '
                f'display:flex; align-items:center; justify-content:center; '
                f'border:1px solid var(--slate-200);">'
                f'<img src="{primary}" '
                f'style="width:100%; height:100%; object-fit:cover; display:block;" '
                f'onerror="this.style.display=\'none\'; '
                f'this.parentElement.innerHTML=\'<span style=&quot;font-size:42px&quot;>🧴</span>\';"/>'
                f'</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="width:100%; aspect-ratio:1/1; '
                'background:var(--slate-100); border-radius:8px; '
                'display:flex; align-items:center; justify-content:center; '
                'font-size:50px; border:1px solid var(--slate-200);">🧴</div>',
                unsafe_allow_html=True,
            )

        # ===== Name =====
        st.markdown(
            f'<div style="font-weight:600; font-size:13px; color:var(--slate-900); '
            f'margin-top:8px; white-space:nowrap; overflow:hidden; '
            f'text-overflow:ellipsis;" title="{name}">{name}</div>',
            unsafe_allow_html=True,
        )

        # ===== SKU + Cat =====
        st.markdown(
            f'<div style="font-size:11px; color:var(--slate-500); '
            f'margin-top:2px;">SKU: {sku}</div>'
            f'<div style="font-size:11px; color:var(--slate-500);">📂 {cat}</div>',
            unsafe_allow_html=True,
        )

        # ===== Stock chip =====
        st.markdown(
            f'<div style="margin:8px 0;">'
            f'<span style="background:{chip_bg}; color:{chip_color}; '
            f'border:1px solid {chip_border}; padding:3px 10px; '
            f'border-radius:10px; font-size:11px; font-weight:600;">'
            f'{chip_text}</span></div>',
            unsafe_allow_html=True,
        )

        # ===== Add/Remove button =====
        if is_selected:
            if st.button("✓ เลือกแล้ว", key=f"card_{eq['id']}",
                         use_container_width=True, type="primary"):
                st.session_state['po_items'] = [
                    it for it in st.session_state['po_items']
                    if it.get('equipment_id') != eq['id']
                ]
                db.save_po_draft(uid(), st.session_state['po_items'],
                                   st.session_state.get('_po_notes_value', ''))
                st.rerun()
        else:
            if st.button("+ เพิ่ม", key=f"card_{eq['id']}",
                         use_container_width=True):
                st.session_state['po_items'].append({
                    'equipment_id': eq['id'],
                    'name': name,
                    'unit': unit,
                    'qty': 1,
                    'notes': '',
                })
                db.save_po_draft(uid(), st.session_state['po_items'],
                                   st.session_state.get('_po_notes_value', ''))
                st.rerun()


def _render_selected_items(eq_list):
    """แสดงรายการที่เลือก พร้อม +/- จำนวน + ลบ"""
    eq_map = {e['id']: e for e in eq_list}

    for i, item in enumerate(st.session_state['po_items']):
        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([0.7, 3, 2, 2, 0.6])

            # รูป
            with c1:
                eq = eq_map.get(item.get('equipment_id'))
                # หารูป — จาก eq, item['image_urls'], หรือ fallback emoji
                thumb = None
                if eq:
                    thumb = eq.get('image_url')
                    if not thumb:
                        urls = eq.get('image_urls') or []
                        if urls:
                            thumb = urls[0]
                # custom item ที่ user upload เอง
                if not thumb and item.get('image_urls'):
                    thumb = item['image_urls'][0]

                if thumb:
                    try:
                        st.image(thumb, width=50)
                    except Exception:
                        st.markdown('🧴')
                else:
                    st.markdown('🧴' if item.get('equipment_id') else '✏️')

            # ชื่อ + SKU
            with c2:
                st.markdown(f"**{item['name']}**")
                if item.get('equipment_id') and eq:
                    st.caption(f"SKU: {eq.get('sku') or '-'}")
                else:
                    n_imgs = len(item.get('image_urls') or [])
                    if n_imgs:
                        st.caption(f"✏️ พิมพ์เอง • 📷 {n_imgs} รูป")
                    else:
                        st.caption("✏️ พิมพ์เอง")
                if item.get('notes'):
                    st.caption(f"💬 {item['notes']}")

            # ปุ่ม +/- + จำนวน
            with c3:
                qc1, qc2, qc3 = st.columns([1, 2, 1])
                with qc1:
                    if st.button("➖", key=f"dec_{i}",
                                 disabled=item['qty'] <= 1):
                        st.session_state['po_items'][i]['qty'] -= 1
                        db.save_po_draft(uid(), st.session_state['po_items'],
                                           st.session_state.get('_po_notes_value', ''))
                        st.rerun()
                with qc2:
                    new_qty = st.number_input(
                        "qty",
                        min_value=1,
                        value=int(item['qty']),
                        step=1,
                        key=f"qty_{i}",
                        label_visibility="collapsed",
                    )
                    if new_qty != item['qty']:
                        st.session_state['po_items'][i]['qty'] = int(new_qty)
                        db.save_po_draft(uid(), st.session_state['po_items'],
                                           st.session_state.get('_po_notes_value', ''))
                        st.rerun()
                with qc3:
                    if st.button("➕", key=f"inc_{i}"):
                        st.session_state['po_items'][i]['qty'] += 1
                        db.save_po_draft(uid(), st.session_state['po_items'],
                                           st.session_state.get('_po_notes_value', ''))
                        st.rerun()

            # หน่วย
            with c4:
                st.markdown(
                    f'<div style="padding-top:8px; color:#888; '
                    f'font-size:13px;">{item["unit"]}</div>',
                    unsafe_allow_html=True,
                )

            # ลบ
            with c5:
                if st.button("🗑️", key=f"del_{i}",
                             help="ลบออกจากรายการ"):
                    st.session_state['po_items'].pop(i)
                    db.save_po_draft(uid(), st.session_state['po_items'],
                                       st.session_state.get('_po_notes_value', ''))
                    st.rerun()


# ==================================================================
# View PO Detail
# ==================================================================

def render_po_view():
    user = current_user()
    role = user.get('role', '')

    po_id = st.session_state.get('view_po_id')
    if not po_id:
        st.session_state['mode'] = 'po_list'
        st.rerun()
        return

    po = db.get_purchase_order(po_id)
    if not po:
        st.error("ไม่พบใบ PO นี้")
        if st.button("← กลับ"):
            st.session_state['mode'] = 'po_list'
            st.rerun()
        return

    # ตรวจสิทธิ์: requester เห็นเฉพาะ PO ของตัวเอง
    if role == 'requester' and po.get('created_by') != uid():
        st.error("❌ คุณไม่มีสิทธิ์ดูใบนี้")
        if st.button("← กลับ"):
            st.session_state['mode'] = 'po_list'
            st.rerun()
        return

    # ===== Breadcrumb + Header =====
    st.markdown(f"""
    <div style="color:var(--slate-500); font-size:12px; margin-bottom:10px;">
        <span style="color:var(--brand-700); cursor:pointer;">← ใบ PO</span>
        <span style="margin:0 6px;">›</span>
        <span>{po['po_number']}</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 1])
    with col1:
        # Build header with status pill
        sup_text = po.get('supplier_name') or '(ยังไม่ระบุ supplier)'
        n_items = len(po.get('items') or [])
        creator = po.get('created_by_name', '—')
        date_str = fmt_date(po.get('created_at'))

        st.markdown(f"""
        <div style="display:flex; align-items:center; gap:12px; flex-wrap:wrap;">
            <h1 style="margin:0;">{po['po_number']}</h1>
            {status_pill_html(po['status'])}
        </div>
        <div style="color:var(--slate-500); font-size:13px; margin-top:4px;">
            {sup_text} • {n_items} รายการ • สร้างโดย {creator} เมื่อ {date_str}
        </div>
        """, unsafe_allow_html=True)
    with col2:
        if st.button("← กลับ", use_container_width=True, key="po_view_back"):
            st.session_state['mode'] = 'po_list'
            st.session_state['action_form'] = None
            st.rerun()

    # Progress bar (workflow timeline)
    render_progress_bar(po['status'])

    # คำเตือน
    di = days_indicator(po.get('expected_date'), po['status'])
    if di:
        if 'เลย' in di:
            st.error(f"🚨 **เลยกำหนดรับของแล้ว** — คาดว่าได้รับ: {fmt_date(po['expected_date'])}")
        elif 'เหลือ' in di:
            st.warning(f"⏰ **ใกล้ครบกำหนด** — คาดว่าได้รับ: {fmt_date(po['expected_date'])}")

    # ปุ่ม action ตาม role + status
    render_actions(po)

    st.divider()

    # ----- ข้อมูลทั่วไป -----
    col1, col2 = st.columns(2)

    with col1:
        if is_admin():
            st.markdown("### 🏭 Supplier")
            if po.get('supplier_name'):
                st.write(f"**{po['supplier_name']}**")
                if po.get('supplier_contact'):
                    st.write(po['supplier_contact'])
            else:
                st.info("ยังไม่ได้ระบุ supplier — กดปุ่ม \"สั่งซื้อ\" ด้านบน")
        else:
            # staff: ดูสถานะการดำเนินงานแทน (ไม่เห็น supplier ตามนโยบาย)
            st.markdown("### 📋 สถานะ")
            status = po.get('status', '-')
            if status == 'รอจัดซื้อดำเนินการ':
                st.info("⏳ รอแอดมินติดต่อ supplier")
            elif status == 'สั่งซื้อแล้ว':
                st.success("✅ แอดมินสั่ง supplier แล้ว — รอจัดส่ง")
            elif status == 'กำลังขนส่ง':
                st.success("🚚 อยู่ระหว่างจัดส่ง")
            elif status == 'รับของแล้ว':
                st.success("📦 รับของเรียบร้อย")
            elif status == 'มีปัญหา':
                st.error("⚠️ มีปัญหา — แอดมินกำลังจัดการ")
            elif status == 'เสร็จสมบูรณ์':
                st.success("🎉 เสร็จสมบูรณ์")
            elif status == 'ยกเลิก':
                st.warning("❌ ยกเลิกแล้ว")
            else:
                st.write(status)

    with col2:
        st.markdown("### 📅 วันที่")
        st.write(f"**สร้าง:** {fmt_date(po.get('created_at'))}")
        if po.get('ordered_date'):
            st.write(f"**สั่ง supplier:** {fmt_date(po['ordered_date'])}")
        if po.get('expected_date'):
            st.write(f"**คาดว่าได้รับ:** {fmt_date(po['expected_date'])}")
        if po.get('received_date'):
            st.write(f"**รับของ:** {fmt_date(po['received_date'])}")

    if is_admin() and po.get('tracking_number'):
        st.markdown(f"### 🚚 Tracking")
        st.code(po['tracking_number'])

    st.write(f"**👤 ผู้สั่ง:** {po.get('created_by_name', '-')}")

    # รายการสินค้า — interactive cards (คลิกดูรายละเอียดได้)
    st.markdown("### 📦 รายการ")
    if po.get('items'):
        # ดึงข้อมูล equipment ล่วงหน้า (เพื่อแสดงรูป + รายละเอียด)
        eq_list = db.get_equipment_list()
        eq_map = {e['id']: e for e in eq_list}

        for idx, item in enumerate(po['items']):
            _render_item_row(item, idx, eq_map, po['id'])

    # ยอดสุทธิ (admin)
    if is_admin() and po.get('total'):
        sum_col1, sum_col2 = st.columns([2, 1])
        with sum_col2:
            st.markdown("### 💰 ยอดสุทธิ")
            st.write(f"ยอดรวม: ฿{po.get('subtotal', 0):,.2f}")
            if po.get('discount', 0) > 0:
                st.write(f"ส่วนลด: -฿{po['discount']:,.2f}")
            if po.get('shipping_fee', 0) > 0:
                st.write(f"ค่าส่ง: ฿{po['shipping_fee']:,.2f}")
            if po.get('vat', 0) > 0:
                st.write(f"VAT: ฿{po['vat']:,.2f}")
            st.markdown(f"## ฿{po.get('total', 0):,.2f}")

    if po.get('notes'):
        st.markdown("### 📝 หมายเหตุ")
        st.info(po['notes'])

    if is_admin() and po.get('procurement_notes'):
        st.markdown("### 📝 หมายเหตุจัดซื้อ")
        st.info(po['procurement_notes'])

    # ประวัติการรับของ
    deliveries = db.get_deliveries(po['id'])
    if deliveries:
        st.divider()
        st.markdown("### 📦 ประวัติการรับของ")
        for d in deliveries:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.markdown(f"**ครั้งที่ {d['delivery_no']}** — {fmt_date(d['received_date'])}")
                    st.caption(f"ผู้รับ: {d.get('received_by_name', '-')}")
                with col2:
                    cond = d.get('overall_condition', 'ปกติ')
                    if cond == 'ปกติ':
                        st.success(f"✅ {cond}")
                    else:
                        st.error(f"⚠️ {cond}")

                # รายการ
                if d.get('items_received'):
                    for it in d['items_received']:
                        recv = it.get('qty_received', 0)
                        ord_ = it.get('qty_ordered', 0)
                        dmg = it.get('qty_damaged', 0)
                        line = f"- **{it.get('name')}**: รับ {recv}/{ord_}"
                        if dmg > 0:
                            line += f" (เสีย {dmg})"
                        if it.get('notes'):
                            line += f" — {it['notes']}"
                        st.write(line)

                if d.get('issue_description'):
                    st.warning(f"⚠️ ปัญหา: {d['issue_description']}")
                if d.get('notes'):
                    st.caption(f"📝 {d['notes']}")

                # รูป
                if d.get('image_urls'):
                    img_cols = st.columns(min(len(d['image_urls']), 4))
                    for i, url in enumerate(d['image_urls'][:8]):
                        with img_cols[i % 4]:
                            try:
                                st.image(url, use_container_width=True)
                            except Exception:
                                pass

    st.divider()

    # 📎 ไฟล์แนบ
    render_attachments(po)

    st.divider()

    # Comments
    render_comments(po, user)

    # Activity log
    with st.expander("📋 ประวัติกิจกรรม (Activity Log)"):
        acts = db.get_activities(po['id'])
        if not acts:
            st.caption("ยังไม่มีกิจกรรม")
        else:
            for a in acts:
                emoji = "🔐" if a.get('user_role') == 'admin' else "👤"
                st.write(f"- **{fmt_dt(a['created_at'])}** — {emoji} **{a.get('user_name', '-')}**: {a.get('description', '-')}")

    # ปุ่มลบ (admin)
    if is_admin() and po['status'] in ('ยกเลิก', 'เสร็จสมบูรณ์'):
        st.divider()
        with st.expander("⚠️ Danger Zone"):
            if st.button("🗑️ ลบใบ PO นี้ถาวร", type="secondary"):
                if st.session_state.get('confirm_del') == po['id']:
                    db.delete_purchase_order(po['id'])
                    st.session_state['mode'] = 'po_list'
                    st.success("ลบแล้ว")
                    st.rerun()
                else:
                    st.session_state['confirm_del'] = po['id']
                    st.warning("กดอีกครั้งเพื่อยืนยันการลบ")


# ==================================================================
# Progress Bar
# ==================================================================

def _render_item_row(item, idx, eq_map, po_id):
    """แสดงรายการสินค้า 1 บรรทัด + กด expand ดูรายละเอียดเต็มได้"""
    eq_id = item.get('equipment_id')
    eq = eq_map.get(eq_id) if eq_id else None

    # กล่องรายการ
    with st.container(border=True):
        # แถวบน: รูป + ชื่อ + จำนวน + ราคา + ปุ่มดู
        cols = st.columns([0.6, 4, 1.5, 2, 1])

        # รูป (thumbnail — ใช้รูปหลัก หรือ fallback image_urls[0])
        with cols[0]:
            thumb = None
            if eq:
                thumb = eq.get('image_url')
                if not thumb:
                    urls = eq.get('image_urls') or []
                    if urls:
                        thumb = urls[0]
            # custom item — รูปที่ user upload ตอนสร้าง PO
            if not thumb and item.get('image_urls'):
                thumb = item['image_urls'][0]
            if thumb:
                try:
                    st.image(thumb, width=50)
                except Exception:
                    st.markdown("🧴")
            else:
                st.markdown('<div style="font-size:32px;">🧴</div>',
                              unsafe_allow_html=True)

        # ชื่อ + SKU
        with cols[1]:
            st.markdown(f"**{item.get('name', '-')}**")
            if eq:
                st.caption(f"SKU: {eq.get('sku') or '-'}  |  📂 {eq.get('category', '-')}")
            elif not eq_id:
                n_imgs = len(item.get('image_urls') or [])
                if n_imgs:
                    st.caption(f"✏️ พิมพ์เอง (ไม่ได้อยู่ใน catalog) • 📷 {n_imgs} รูป")
                else:
                    st.caption("✏️ พิมพ์เอง (ไม่ได้อยู่ใน catalog)")
            if item.get('notes'):
                st.caption(f"💬 {item['notes']}")

        # จำนวน
        with cols[2]:
            st.markdown(f"<div style='text-align:right; padding-top:8px;'>"
                         f"<b>{item.get('qty', 0):,.0f}</b> {item.get('unit', '')}"
                         f"</div>", unsafe_allow_html=True)

        # ราคา (admin only)
        with cols[3]:
            if is_admin():
                price = item.get('unit_price', 0)
                subtotal = item.get('subtotal', 0)
                if price > 0:
                    st.markdown(
                        f"<div style='text-align:right; padding-top:8px;'>"
                        f"<span style='color:#888; font-size:11px;'>"
                        f"@฿{price:,.2f}</span><br>"
                        f"<b style='color:#4A6FA5;'>฿{subtotal:,.2f}</b>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

        # ปุ่มดูรายละเอียด — แสดงเมื่อ มี eq หรือ มีรูปจาก custom item
        custom_imgs = item.get('image_urls') or []
        with cols[4]:
            detail_key = f"item_detail_{po_id}_{idx}"
            is_open = st.session_state.get(detail_key, False)
            has_detail = bool(eq) or bool(custom_imgs)
            if has_detail:
                if st.button("👁️" if not is_open else "▲",
                              key=f"btn_detail_{po_id}_{idx}",
                              use_container_width=True,
                              help="ดูรายละเอียด / รูป"):
                    st.session_state[detail_key] = not is_open
                    st.rerun()

        # Detail expanded section
        if st.session_state.get(detail_key):
            if eq:
                st.markdown("---")
                # รวมรูปทั้งหมด (image_urls + image_url legacy)
                eq_images = list(eq.get('image_urls') or [])
                if eq.get('image_url') and eq['image_url'] not in eq_images:
                    eq_images.insert(0, eq['image_url'])

                dc1, dc2 = st.columns([1, 2])
                with dc1:
                    # รูปหลัก (รูปแรก)
                    if eq_images:
                        try:
                            st.image(eq_images[0], use_container_width=True)
                        except Exception:
                            pass
                    else:
                        st.markdown('<div style="font-size:64px; text-align:center;">🧴</div>',
                                      unsafe_allow_html=True)
            elif custom_imgs:
                # ===== Custom item — แสดงรูปที่ user upload =====
                st.markdown("---")
                st.markdown(f"#### 📷 รูปประกอบ ({len(custom_imgs)} รูป)")
                st.caption("✏️ รูปที่ผู้สร้าง PO อัปโหลดไว้ — ใช้ดูประกอบการสั่งซื้อ")
                # แสดงเป็น grid 4 คอลัมน์
                cols_per_row = 4
                for r in range(0, len(custom_imgs), cols_per_row):
                    row_imgs = custom_imgs[r:r + cols_per_row]
                    img_cols = st.columns(cols_per_row)
                    for i, url in enumerate(row_imgs):
                        with img_cols[i]:
                            try:
                                st.image(url, use_container_width=True)
                            except Exception:
                                st.caption("⚠️ โหลดรูปไม่สำเร็จ")
                if item.get('notes'):
                    st.markdown(f"💬 **หมายเหตุ:** {item['notes']}")
                return  # ไม่ต้องเข้า block ของ eq detail

        # ===== ส่วนต่อจาก eq detail =====
        if eq and st.session_state.get(detail_key):
            with dc2:
                st.markdown(f"### {eq.get('name', '-')}")
                st.caption(f"📦 SKU: **{eq.get('sku') or '-'}**")

                meta_c1, meta_c2 = st.columns(2)
                with meta_c1:
                    st.markdown(f"📂 **หมวด:** {eq.get('category', '-')}")
                    st.markdown(f"📐 **หน่วย:** {eq.get('unit', 'ชิ้น')}")
                with meta_c2:
                    stock = eq.get('stock', 0)
                    if stock == 0:
                        stock_color = "#A32D2D"
                        stock_emoji = "🔴"
                    elif stock < 10:
                        stock_color = "#BA7517"
                        stock_emoji = "🟡"
                    else:
                        stock_color = "#1D9E75"
                        stock_emoji = "🟢"
                    st.markdown(
                        f'<div>{stock_emoji} <b>คงเหลือ:</b> '
                        f'<span style="color:{stock_color}; font-weight:500;">'
                        f'{stock:,} {eq.get("unit", "ชิ้น")}</span></div>',
                        unsafe_allow_html=True,
                    )
                    if is_admin():
                        st.markdown(
                            f'💰 <b>ต้นทุนล่าสุด:</b> '
                            f'<span style="color:#4A6FA5;">'
                            f'฿{eq.get("last_cost", 0):,.2f}</span>',
                            unsafe_allow_html=True,
                        )

                if eq.get('description'):
                    st.markdown("**📝 รายละเอียด:**")
                    st.write(eq['description'])

            # ===== Gallery รูปเพิ่มเติม (ถ้ามีมากกว่า 1 รูป) =====
            if len(eq_images) > 1:
                st.markdown(f"#### 🖼️ รูปทั้งหมด ({len(eq_images)} รูป)")
                # แสดง 4 รูป/แถว
                for row_start in range(0, len(eq_images), 4):
                    row = eq_images[row_start:row_start + 4]
                    img_cols = st.columns(4)
                    for i, url in enumerate(row):
                        actual_i = row_start + i
                        with img_cols[i]:
                            try:
                                st.image(url, use_container_width=True)
                                if actual_i == 0:
                                    st.caption("⭐ รูปหลัก")
                                else:
                                    st.caption(f"รูปที่ {actual_i + 1}")
                            except Exception:
                                st.markdown("🖼️ (โหลดไม่ได้)")


def render_progress_bar(current_status):
    """B2B Workflow Timeline — circular dots + connecting lines"""
    main_steps = [
        ("สร้าง PO", "รอจัดซื้อดำเนินการ"),
        ("สั่งซื้อ", "สั่งซื้อแล้ว"),
        ("ขนส่ง", "กำลังขนส่ง"),
        ("รับของ", "รับของแล้ว"),
        ("เสร็จสมบูรณ์", "เสร็จสมบูรณ์"),
    ]

    if current_status == 'ยกเลิก':
        st.markdown(
            '<div style="padding:14px 18px; background:var(--slate-100); '
            'border-left:4px solid var(--slate-400); border-radius:8px; margin:12px 0; '
            'font-size:14px; color:var(--slate-600);">'
            '<b>❌ ยกเลิก</b></div>',
            unsafe_allow_html=True,
        )
        return

    if current_status == 'มีปัญหา':
        st.markdown(
            '<div style="padding:14px 18px; background:var(--danger-soft); '
            'border-left:4px solid var(--danger); border-radius:8px; margin:12px 0; '
            'font-size:14px; color:var(--danger);">'
            '<b>⚠️ มีปัญหา — กำลังตรวจสอบ</b></div>',
            unsafe_allow_html=True,
        )
        return

    try:
        cur_idx = next(i for i, (_, s) in enumerate(main_steps) if s == current_status)
    except StopIteration:
        cur_idx = 0

    # Build B2B timeline
    html = '<div class="workflow">'
    for i, (label, status) in enumerate(main_steps):
        if i < cur_idx:
            cls = "done"
            inner = "✓"
        elif i == cur_idx:
            cls = "active"
            inner = str(i + 1)
        else:
            cls = ""
            inner = str(i + 1)
        html += (
            f'<div class="workflow-step {cls}">'
            f'<div class="workflow-dot">{inner}</div>'
            f'<div class="workflow-label">{label}</div>'
            f'</div>'
        )
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)


# ==================================================================
# Action Buttons
# ==================================================================

def render_actions(po):
    """ปุ่ม action ตาม role + สถานะ — แสดงเฉพาะที่ใช้งานได้"""
    user = current_user()
    role = user.get('role')
    status = po['status']
    po_id = po['id']

    # ===== สร้างรายการปุ่มที่ใช้งานได้ =====
    actions = []  # list of (label, type, callback or action_form)

    # PDF download — ขึ้นเมื่อมีข้อมูลครบแล้ว (ไม่ใช่สถานะ "รอจัดซื้อ")
    # เพราะตอนรอจัดซื้อ ยังไม่มี supplier/ราคา → PDF ไม่มีประโยชน์
    if status != "รอจัดซื้อดำเนินการ":
        actions.append(('pdf', '📥 ดาวน์โหลด PDF', 'primary'))

    # Admin: สั่งซื้อ — primary action ตอนรอจัดซื้อ
    if is_admin() and status == "รอจัดซื้อดำเนินการ":
        actions.append(('order', '🛒 สั่งซื้อ', 'primary'))

    # Admin: อัปเดตขนส่ง
    if is_admin() and status == "สั่งซื้อแล้ว":
        actions.append(('ship', '🚚 อัปเดตขนส่ง', 'secondary'))

    # ทุกคน: รับของ
    if status in ('สั่งซื้อแล้ว', 'กำลังขนส่ง'):
        actions.append(('receive', '📦 รับของ', 'secondary'))

    # ทุกคน: ปิดงาน
    if status in ('รับของแล้ว', 'มีปัญหา'):
        actions.append(('close', '✔️ ปิดงาน', 'secondary'))

    # คัดลอก (admin หรือเจ้าของ)
    can_clone = is_admin() or po.get('created_by') == uid()
    if can_clone:
        actions.append(('clone', '🔁 คัดลอก', 'secondary'))

    # ยกเลิก (admin หรือเจ้าของ + ยังไม่ปิดงาน)
    if status not in ('เสร็จสมบูรณ์', 'ยกเลิก'):
        if (role == 'requester' and po.get('created_by') == uid()) or is_admin():
            actions.append(('cancel', '❌ ยกเลิก', 'secondary'))

    if not actions:
        return

    # ===== Render — ห่อในกล่องสวยๆ + จัดเรียง =====
    st.markdown(
        '<div style="margin:16px 0 8px; '
        'font-size:13px; font-weight:500; color:#4A6FA5;">'
        '⚡ การดำเนินการ</div>',
        unsafe_allow_html=True,
    )

    # ใช้ columns ตามจำนวนจริงของปุ่ม (ไม่เกิน 4 ต่อแถว)
    per_row = 4
    for row_start in range(0, len(actions), per_row):
        row_actions = actions[row_start:row_start + per_row]
        # padding columns ขวา ถ้าแถวสุดท้ายไม่เต็ม
        cols = st.columns(per_row)
        for i, (action_id, label, btn_type) in enumerate(row_actions):
            with cols[i]:
                if action_id == 'pdf':
                    try:
                        from pdf_generator import generate_po_pdf
                        pdf_bytes = generate_po_pdf(po, role=role)
                        st.download_button(
                            label, data=pdf_bytes,
                            file_name=f"{po['po_number']}.pdf",
                            mime="application/pdf",
                            use_container_width=True, type=btn_type,
                            key=f"pdf_{po_id}",
                        )
                    except Exception:
                        st.button(label, use_container_width=True,
                                    disabled=True, key=f"pdf_disabled_{po_id}")
                elif action_id == 'close':
                    if st.button(label, use_container_width=True,
                                  type=btn_type, key=f"close_{po_id}"):
                        with st.spinner("กำลังปิดงาน..."):
                            db.update_po_status(po_id, "เสร็จสมบูรณ์",
                                                  uname(), role, "ปิดงาน")
                        st.rerun()
                elif action_id == 'clone':
                    if st.button(label, use_container_width=True,
                                  type=btn_type, key=f"clone_{po_id}",
                                  help="คัดลอกรายการเดิม → ไปหน้าสร้าง PO ใหม่ (แก้ไขก่อนบันทึก)"):
                        # โหลด items เดิมเข้า session_state ของหน้า PO Create
                        # → user เห็น/แก้/เพิ่ม-ลบ รายการ ก่อนกดบันทึก
                        items_clone = []
                        for it in (po.get('items') or []):
                            items_clone.append({
                                'equipment_id': it.get('equipment_id'),
                                'name': it.get('name'),
                                'qty': int(it.get('qty', 0) or 0),
                                'unit': it.get('unit', 'ชิ้น'),
                                'notes': it.get('notes', ''),
                                # เก็บรูปจาก custom item เดิม
                                'image_urls': list(it.get('image_urls') or []),
                            })
                        st.session_state['po_items'] = items_clone
                        st.session_state['_po_notes_value'] = (
                            f"[คัดลอกจาก {po.get('po_number', '-')}] "
                            f"{po.get('notes', '')}"
                        ).strip()

                        # บันทึก draft ไว้เลย → ถ้า user ออกหน้าก็ไม่หาย
                        try:
                            db.save_po_draft(uid(),
                                              st.session_state['po_items'],
                                              st.session_state['_po_notes_value'])
                        except Exception:
                            pass

                        # reset draft_loaded flag ให้ render_po_create ไม่ overwrite
                        st.session_state[f'_draft_loaded_{uid()}'] = True
                        # ลบ widget key เก่า เพื่อให้ text_area แสดงค่าใหม่
                        st.session_state.pop('po_create_notes', None)

                        # redirect ไปหน้าสร้าง PO
                        st.session_state['mode'] = 'po_create'
                        st.session_state['action_form'] = None
                        st.rerun()
                else:
                    # เปิด form
                    if st.button(label, use_container_width=True,
                                  type=btn_type, key=f"act_{action_id}_{po_id}"):
                        st.session_state['action_form'] = action_id
                        st.rerun()

    # Render forms
    af = st.session_state.get('action_form')
    if af == 'order':
        render_order_form(po)
    elif af == 'ship':
        render_ship_form(po)
    elif af == 'receive':
        render_receive_form(po)
    elif af == 'cancel':
        render_cancel_form(po)


def render_order_form(po):
    """แอดมิน: สั่งซื้อกับ supplier — B2B styled"""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, var(--brand-700), var(--brand-900));
                color:white; padding:14px 20px; border-radius:10px;
                margin:8px 0 14px; display:flex; align-items:center; gap:12px;">
        <div style="width:40px; height:40px; background:rgba(255,255,255,0.15);
                    border-radius:10px; display:flex; align-items:center;
                    justify-content:center; font-size:20px;">🛒</div>
        <div>
            <div style="font-size:15px; font-weight:700;">
                สั่งซื้อกับ Supplier — {po['po_number']}
            </div>
            <div style="font-size:11px; opacity:0.85;">
                กรอกข้อมูล supplier + ราคาแต่ละรายการ + วันที่คาดได้รับ
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("order_form"):
        col1, col2 = st.columns(2)
        with col1:
            supplier_name = st.text_input("ชื่อ Supplier *",
                                            value=po.get('supplier_name') or '')
            ordered_date = st.date_input("วันที่สั่ง", value=date.today())
        with col2:
            supplier_contact = st.text_area("ข้อมูลติดต่อ",
                                              value=po.get('supplier_contact') or '',
                                              height=80,
                                              placeholder="เบอร์ / อีเมล / ที่อยู่")
            expected_date = st.date_input("วันที่คาดว่าได้รับ *",
                                            value=date.today() + timedelta(days=7))

        # ใส่ราคารายการ
        st.markdown("**ราคาต่อรายการ:**")
        items = po.get('items', [])
        new_items = []
        for i, item in enumerate(items):
            cols = st.columns([3, 1, 2, 2])
            with cols[0]:
                st.write(item.get('name'))
            with cols[1]:
                st.write(f"{item.get('qty', 0):,.0f} {item.get('unit', '')}")
            with cols[2]:
                price = st.number_input(
                    f"ราคา/หน่วย",
                    min_value=0.0,
                    value=float(item.get('unit_price', 0)),
                    step=1.0,
                    key=f"op_{i}",
                    label_visibility='collapsed',
                )
            with cols[3]:
                st.write(f"= ฿{price * item.get('qty', 0):,.2f}")
            new_items.append({**item,
                              'unit_price': price,
                              'subtotal': price * item.get('qty', 0)})

        col1, col2, col3 = st.columns(3)
        with col1:
            discount = st.number_input("ส่วนลด", min_value=0.0,
                                          value=float(po.get('discount', 0) or 0),
                                          step=10.0)
        with col2:
            shipping = st.number_input("ค่าส่ง", min_value=0.0,
                                          value=float(po.get('shipping_fee', 0) or 0),
                                          step=10.0)
        with col3:
            vat_pct = st.selectbox("VAT", ["ไม่มี", "7%"])

        proc_notes = st.text_area("📝 หมายเหตุจัดซื้อ",
                                     placeholder="เช่น ตกลงราคาแล้ว / เงื่อนไขพิเศษ",
                                     height=60)

        # 📎 แนบไฟล์
        st.markdown("---")
        st.markdown("#### 📎 ไฟล์แนบ (ถ้ามี)")
        st.caption("เช่น ใบเสนอราคา / ใบ PO ที่ส่ง supplier / หลักฐานการโอน")
        uploaded_files = st.file_uploader(
            "เลือกไฟล์ (PDF, Word, Excel, รูป — เลือกได้หลายไฟล์)",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                  'jpg', 'jpeg', 'png', 'gif', 'webp',
                  'txt', 'csv', 'zip', 'rar', '7z'],
            key="order_attach",
        )
        if uploaded_files:
            st.caption(f"📄 จะอัปโหลด {len(uploaded_files)} ไฟล์")

        c1, c2 = st.columns([1, 4])
        with c1:
            submitted = st.form_submit_button("✅ ยืนยัน", type="primary")
        with c2:
            cancelled = st.form_submit_button("❌ ยกเลิก")

        if submitted:
            if not supplier_name:
                st.error("กรุณากรอกชื่อ supplier")
            else:
                subtotal = sum(i['subtotal'] for i in new_items)
                vat_amt = subtotal * 0.07 if vat_pct == "7%" else 0

                # 1) update procurement info
                db.update_po_procurement(
                    po_id=po['id'],
                    supplier_name=supplier_name,
                    supplier_contact=supplier_contact,
                    items_with_prices=new_items,
                    discount=discount,
                    shipping_fee=shipping,
                    vat=vat_amt,
                    expected_date=expected_date.isoformat(),
                    procurement_notes=proc_notes,
                    user_name=uname(),
                )

                # 2) อัปโหลดไฟล์แนบ (ถ้ามี)
                if uploaded_files:
                    with st.spinner(f"กำลังอัปโหลด {len(uploaded_files)} ไฟล์..."):
                        new_attaches = []
                        for f in uploaded_files:
                            att = db.upload_attachment(f.getvalue(), f.name)
                            if att:
                                new_attaches.append(att)
                        if new_attaches:
                            db.add_po_attachments(
                                po['id'], new_attaches,
                                user_name=uname(),
                                category='order',
                            )
                            db.log_activity(
                                po['id'], uname(), urole(),
                                'attached',
                                f"แนบไฟล์ {len(new_attaches)} ไฟล์ (ดำเนินการสั่งซื้อ)",
                            )

                st.session_state['action_form'] = None
                st.rerun()
        elif cancelled:
            st.session_state['action_form'] = None
            st.rerun()


def render_ship_form(po):
    """แอดมิน: อัปเดตขนส่ง — B2B styled"""
    st.markdown(f"""
    <div style="background:linear-gradient(135deg, var(--brand-700), var(--brand-900));
                color:white; padding:14px 20px; border-radius:10px;
                margin:8px 0 14px; display:flex; align-items:center; gap:12px;">
        <div style="width:40px; height:40px; background:rgba(255,255,255,0.15);
                    border-radius:10px; display:flex; align-items:center;
                    justify-content:center; font-size:20px;">🚚</div>
        <div>
            <div style="font-size:15px; font-weight:700;">
                อัปเดตขนส่ง — {po['po_number']}
            </div>
            <div style="font-size:11px; opacity:0.85;">
                ใส่เลข Tracking + บริษัทขนส่ง • ผู้สร้าง PO จะได้รับแจ้งเตือน
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("ship_form"):
        tracking = st.text_input("เลข Tracking",
                                    value=po.get('tracking_number') or '',
                                    placeholder="เช่น KE12345678")
        note = st.text_area("หมายเหตุ",
                              placeholder="เช่น Supplier แจ้งจัดส่งวันนี้")

        # 📎 แนบไฟล์
        st.markdown("---")
        st.markdown("#### 📎 ไฟล์แนบ (ถ้ามี)")
        st.caption("เช่น ใบ tracking / slip การส่ง / ใบแจ้งจัดส่งจาก supplier")
        uploaded_files = st.file_uploader(
            "เลือกไฟล์ (PDF, Word, Excel, รูป — เลือกได้หลายไฟล์)",
            accept_multiple_files=True,
            type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                  'jpg', 'jpeg', 'png', 'gif', 'webp',
                  'txt', 'csv', 'zip', 'rar', '7z'],
            key="ship_attach",
        )
        if uploaded_files:
            st.caption(f"📄 จะอัปโหลด {len(uploaded_files)} ไฟล์")

        c1, c2 = st.columns([1, 4])
        with c1:
            submitted = st.form_submit_button("✅ ยืนยัน", type="primary")
        with c2:
            cancelled = st.form_submit_button("❌ ยกเลิก")

        if submitted:
            db.update_po_status(po['id'], "กำลังขนส่ง",
                                  uname(), urole(),
                                  note=note,
                                  tracking_number=tracking)

            # อัปโหลดไฟล์แนบ
            if uploaded_files:
                with st.spinner(f"กำลังอัปโหลด {len(uploaded_files)} ไฟล์..."):
                    new_attaches = []
                    for f in uploaded_files:
                        att = db.upload_attachment(f.getvalue(), f.name)
                        if att:
                            new_attaches.append(att)
                    if new_attaches:
                        db.add_po_attachments(
                            po['id'], new_attaches,
                            user_name=uname(),
                            category='shipping',
                        )
                        db.log_activity(
                            po['id'], uname(), urole(),
                            'attached',
                            f"แนบไฟล์ {len(new_attaches)} ไฟล์ (อัปเดตขนส่ง)",
                        )

            st.session_state['action_form'] = None
            st.rerun()
        elif cancelled:
            st.session_state['action_form'] = None
            st.rerun()


def render_receive_form(po):
    """ผู้สั่งหรือแอดมิน: บันทึกการรับของ — B2B style"""
    # Hero banner with PO context
    sup = po.get('supplier_name') or '—'
    n_items = len(po.get('items', []))
    tracking = po.get('tracking_number') or '—'
    expected = fmt_date(po.get('expected_date')) if po.get('expected_date') else '—'

    st.markdown(f"""
    <div style="background:linear-gradient(135deg, var(--brand-700), var(--brand-900));
                color:white; padding:18px 22px; border-radius:12px;
                margin:8px 0 16px; display:flex; align-items:center; gap:14px;">
        <div style="width:48px; height:48px; background:rgba(255,255,255,0.15);
                    border-radius:12px; display:flex; align-items:center;
                    justify-content:center; font-size:24px;">📦</div>
        <div style="flex:1;">
            <div style="font-size:16px; font-weight:700; margin-bottom:2px;">
                บันทึกการรับของ — {po['po_number']}
            </div>
            <div style="font-size:12px; opacity:0.85;">
                {sup} • {n_items} รายการ • Tracking: {tracking} • คาดได้รับ: {expected}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    items = po.get('items', [])
    key = f"recv_{po['id']}"

    def _make_default(it):
        return {
            'qty_received': it.get('qty', 0) or 0,
            'qty_damaged': 0,
            'item_notes': '',
            'notes': '',
        }

    # init หรือ reset ถ้าจำนวนไม่ตรงกับ items
    existing = st.session_state.get(key)
    if (not isinstance(existing, list)
            or len(existing) != len(items)):
        st.session_state[key] = [_make_default(it) for it in items]

    data = st.session_state[key]

    # ตรวจสอบเพิ่ม: แต่ละ entry ต้องเป็น dict
    for i, it in enumerate(items):
        if not isinstance(data[i], dict):
            data[i] = _make_default(it)

    has_issue = False
    for i, item in enumerate(items):
        with st.container(border=True):
            cols = st.columns([3, 1, 1, 2])
            with cols[0]:
                st.write(f"**{item['name']}**")
                st.caption(f"สั่ง: {item['qty']:,.0f} {item.get('unit', '')}")
            with cols[1]:
                # safe int — รองรับ None/string/float
                _qr_raw = data[i].get('qty_received')
                if _qr_raw is None or _qr_raw == '':
                    _qr_raw = item.get('qty', 0) or 0
                try:
                    _qr_default = int(float(_qr_raw))
                except (TypeError, ValueError):
                    _qr_default = 0
                qr = st.number_input("ได้รับ",
                                       min_value=0,
                                       value=_qr_default,
                                       step=1,
                                       key=f"qr_{po['id']}_{i}")
            with cols[2]:
                _qd_raw = data[i].get('qty_damaged', 0) or 0
                try:
                    _qd_default = int(float(_qd_raw))
                except (TypeError, ValueError):
                    _qd_default = 0
                qd = st.number_input("เสียหาย",
                                       min_value=0,
                                       max_value=qr,
                                       value=min(_qd_default, qr),
                                       step=1,
                                       key=f"qd_{po['id']}_{i}")
            with cols[3]:
                # รองรับทั้ง 'item_notes' (legacy) และ 'notes'
                prev_note = data[i].get('item_notes') or data[i].get('notes', '')
                inote = st.text_input("หมายเหตุ",
                                        value=prev_note,
                                        key=f"in_{po['id']}_{i}")

            data[i] = {
                'equipment_id': item.get('equipment_id'),
                'name': item['name'],
                'qty_ordered': item.get('qty', 0),
                'qty_received': qr,
                'qty_damaged': qd,
                'item_notes': inote,
                'notes': inote,
            }
            if qr != item.get('qty', 0) or qd > 0:
                has_issue = True

    # สภาพรวม
    overall = st.selectbox(
        "สภาพรวม",
        ['ปกติ', 'มีของเสียหาย', 'ขาดจำนวน', 'ส่งผิด', 'อื่นๆ'],
        index=1 if has_issue else 0,
    )

    issue_desc = ""
    if overall != 'ปกติ':
        issue_desc = st.text_area("รายละเอียดปัญหา",
                                     placeholder="เช่น ขวดแตก 5 อัน เสียหายระหว่างขนส่ง")

    notes = st.text_area("หมายเหตุเพิ่มเติม",
                           placeholder="(ถ้ามี)")

    # อัปโหลดรูป
    st.markdown("**📸 รูปประกอบ (ใบส่งของ / รูปสินค้า / รูปความเสียหาย):**")
    imgs = st.file_uploader("เลือกรูป", type=['jpg', 'jpeg', 'png', 'webp'],
                              accept_multiple_files=True,
                              key=f"img_{po['id']}")

    c1, c2 = st.columns([1, 4])
    with c1:
        if st.button("✅ ยืนยันรับของ", type="primary",
                       use_container_width=True,
                       key=f"sub_{po['id']}"):
            # อัปโหลด
            urls = []
            if imgs:
                with st.spinner("กำลังอัปโหลดรูป..."):
                    for img in imgs:
                        url = db.upload_image(img.getvalue(), img.name,
                                                bucket=db.IMG_DEL)
                        if url:
                            urls.append(url)

            db.add_delivery(
                po_id=po['id'],
                items_received=data,
                overall_condition=overall,
                issue_description=issue_desc,
                notes=notes,
                image_urls=urls,
                user_name=uname(),
            )
            del st.session_state[key]
            st.session_state['action_form'] = None
            st.rerun()
    with c2:
        if st.button("❌ ยกเลิก", use_container_width=True,
                       key=f"cn_{po['id']}"):
            del st.session_state[key]
            st.session_state['action_form'] = None
            st.rerun()


def render_cancel_form(po):
    with st.form("cancel_form"):
        st.markdown("#### ❌ ยกเลิกใบ PO")
        st.warning("การยกเลิกจะไม่สามารถเรียกคืนได้")
        reason = st.text_area("เหตุผล *", placeholder="เช่น Supplier แจ้งของหมด")
        c1, c2 = st.columns([1, 4])
        with c1:
            if st.form_submit_button("⚠️ ยืนยันยกเลิก"):
                if not reason:
                    st.error("กรุณากรอกเหตุผล")
                else:
                    db.update_po_status(po['id'], "ยกเลิก",
                                          uname(), urole(), note=reason)
                    st.session_state['action_form'] = None
                    st.rerun()
        with c2:
            if st.form_submit_button("← กลับ"):
                st.session_state['action_form'] = None
                st.rerun()


def render_attachments(po):
    """แสดงไฟล์แนบใน PO + ปุ่มแนบเพิ่ม / ลบ (admin)"""
    st.markdown("### 📎 ไฟล์แนบ")

    attachments = po.get('attachment_urls') or []
    is_adm = is_admin()

    # icon ตาม type
    def _icon(t):
        return {
            'pdf': '📕',
            'doc': '📘', 'docx': '📘',
            'xls': '📗', 'xlsx': '📗', 'csv': '📗',
            'ppt': '📙', 'pptx': '📙',
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️',
            'gif': '🖼️', 'webp': '🖼️',
            'zip': '🗜️', 'rar': '🗜️', '7z': '🗜️',
            'txt': '📄',
        }.get((t or '').lower(), '📎')

    def _format_size(n):
        if not n: return ""
        if n < 1024: return f"{n} B"
        if n < 1024 * 1024: return f"{n/1024:.1f} KB"
        return f"{n/(1024*1024):.1f} MB"

    def _category_label(c):
        return {
            'order': '🛒 ดำเนินการสั่งซื้อ',
            'shipping': '🚚 อัปเดตขนส่ง',
            'general': '📎 ทั่วไป',
        }.get(c, '📎 ทั่วไป')

    if not attachments:
        st.caption("ยังไม่มีไฟล์แนบ")
    else:
        # แยกตามหมวด
        groups = {}
        for a in attachments:
            cat = a.get('category', 'general')
            groups.setdefault(cat, []).append(a)

        for cat in ('order', 'shipping', 'general'):
            if cat not in groups:
                continue
            files = groups[cat]
            st.markdown(f"**{_category_label(cat)}** ({len(files)})")
            for a in files:
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.5, 4, 2, 1])
                    with c1:
                        st.markdown(f"### {_icon(a.get('type'))}")
                    with c2:
                        st.markdown(f"**{a.get('name', '-')}**")
                        meta_parts = []
                        if a.get('size'):
                            meta_parts.append(_format_size(a['size']))
                        if a.get('uploaded_by'):
                            meta_parts.append(f"โดย {a['uploaded_by']}")
                        if a.get('uploaded_at'):
                            meta_parts.append(fmt_dt(a['uploaded_at']))
                        if meta_parts:
                            st.caption(" • ".join(meta_parts))

                        # Preview รูปถ้าเป็นรูป
                        if (a.get('type') or '').lower() in ('jpg', 'jpeg', 'png', 'gif', 'webp'):
                            try:
                                st.image(a['url'], width=200)
                            except Exception:
                                pass
                    with c3:
                        st.markdown(
                            f'<a href="{a["url"]}" target="_blank" '
                            f'style="display:inline-block; padding:6px 14px; '
                            f'background:#4A6FA5; color:white; border-radius:4px; '
                            f'text-decoration:none; font-size:13px;">'
                            f'⬇️ ดาวน์โหลด</a>',
                            unsafe_allow_html=True,
                        )
                    with c4:
                        if is_adm:
                            cd_key = f"da_{a.get('url', '')[-20:]}"
                            if st.session_state.get(cd_key):
                                if st.button("⚠️ ยืนยัน", key=f"d2_{cd_key}",
                                             use_container_width=True):
                                    db.remove_po_attachment(po['id'], a['url'])
                                    db.log_activity(
                                        po['id'], uname(), urole(),
                                        'attachment_removed',
                                        f"ลบไฟล์แนบ: {a.get('name', '-')}",
                                    )
                                    st.session_state.pop(cd_key, None)
                                    st.rerun()
                            else:
                                if st.button("🗑️", key=f"d_{cd_key}",
                                             use_container_width=True,
                                             help="ลบไฟล์แนบ"):
                                    st.session_state[cd_key] = True
                                    st.rerun()

    # ----- เพิ่มไฟล์แนบเพิ่มเติม (admin only) -----
    if is_adm:
        with st.expander("➕ เพิ่มไฟล์แนบ"):
            with st.form(f"add_attach_{po['id']}", clear_on_submit=True):
                files = st.file_uploader(
                    "เลือกไฟล์ (PDF, Word, Excel, รูป)",
                    accept_multiple_files=True,
                    type=['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
                          'jpg', 'jpeg', 'png', 'gif', 'webp',
                          'txt', 'csv', 'zip', 'rar', '7z'],
                )
                if st.form_submit_button("📎 อัปโหลด", type="primary"):
                    if not files:
                        st.error("กรุณาเลือกไฟล์")
                    else:
                        with st.spinner(f"กำลังอัปโหลด {len(files)} ไฟล์..."):
                            new_attaches = []
                            for f in files:
                                att = db.upload_attachment(f.getvalue(), f.name)
                                if att:
                                    new_attaches.append(att)
                            if new_attaches:
                                db.add_po_attachments(
                                    po['id'], new_attaches,
                                    user_name=uname(),
                                    category='general',
                                )
                                db.log_activity(
                                    po['id'], uname(), urole(),
                                    'attached',
                                    f"แนบไฟล์เพิ่ม {len(new_attaches)} ไฟล์",
                                )
                                st.success(f"อัปโหลด {len(new_attaches)} ไฟล์แล้ว")
                                st.rerun()


def render_comments(po, user):
    """ความคิดเห็นระหว่างทีม"""
    st.markdown("### 💬 ความคิดเห็น")

    comments = db.get_comments(po['id'])
    if comments:
        for c in comments:
            emoji = "🔐" if c.get('user_role') == 'admin' else "👤"
            with st.container(border=True):
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.markdown(f"{emoji} **{c['user_name']}**")
                with col2:
                    st.caption(fmt_dt(c['created_at']))
                st.write(c['message'])
    else:
        st.caption("ยังไม่มีความคิดเห็น")

    with st.form(f"add_cm_{po['id']}", clear_on_submit=True):
        msg = st.text_area("เพิ่มความคิดเห็น",
                              placeholder="ส่งข้อความถึงทีม...", height=80)
        if st.form_submit_button("💬 ส่ง", type="primary"):
            if msg.strip():
                db.add_comment(po['id'], uname(), urole(), msg.strip())
                st.rerun()
