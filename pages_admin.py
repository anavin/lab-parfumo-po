"""pages_admin.py — equipment, reports, users, notifications"""
from datetime import datetime, date, timedelta
import streamlit as st
import pandas as pd

import database as db
from helpers import fmt_date, fmt_dt, is_admin, uid, show_empty_state


# ==================================================================
# Equipment
# ==================================================================

def render_equipment():
    if not is_admin():
        st.error("เฉพาะแอดมิน")
        return

    st.markdown("## 📦 จัดการอุปกรณ์")

    with st.expander("➕ เพิ่มอุปกรณ์ใหม่"):
        with st.form("ae", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                n = st.text_input("ชื่อ *")
                cat = st.selectbox("หมวด", db.get_categories())
                sk = st.text_input("SKU")
            with c2:
                u = st.text_input("หน่วย", value="ชิ้น")
                lc = st.number_input("ราคาต้นทุนล่าสุด", min_value=0.0, step=1.0)
                stk = st.number_input("คงเหลือ", min_value=0, step=1, value=0)
            d = st.text_area("รายละเอียด", height=60)
            img = st.file_uploader("รูป", type=['jpg', 'jpeg', 'png', 'webp'])
            if st.form_submit_button("✅ เพิ่ม", type="primary"):
                if not n:
                    st.error("กรุณากรอกชื่อ")
                else:
                    iu = db.upload_image(img.getvalue(), img.name) if img else None
                    db.add_equipment(name=n, category=cat, unit=u, sku=sk,
                                       description=d, last_cost=lc, stock=stk, image_url=iu)
                    st.success("เพิ่มแล้ว")
                    st.rerun()

    st.divider()
    items = db.get_equipment_list()
    if not items:
        show_empty_state(
            "🧴",
            "ยังไม่มีอุปกรณ์ในระบบ",
            "เริ่มจากเพิ่มอุปกรณ์แรก — ใส่รูป + SKU + ราคา ทีมจะใช้สั่งซื้อได้ง่าย",
        )
        return

    c1, c2 = st.columns([1, 2])
    with c1:
        f_cat = st.selectbox("หมวดหมู่", ["ทั้งหมด"] + db.get_categories())
    with c2:
        f_search = st.text_input("🔍 ค้นหา", placeholder="ชื่อหรือ SKU")

    filt = items[:]
    if f_cat != "ทั้งหมด":
        filt = [i for i in filt if i.get('category') == f_cat]
    if f_search:
        s = f_search.lower()
        filt = [i for i in filt
                if s in i.get('name', '').lower()
                or s in (i.get('sku') or '').lower()
                or s in (i.get('description') or '').lower()]

    st.caption(f"พบ {len(filt)} รายการ")

    # ---- Catalog Cards (3 ต่อแถว) ----
    for row_start in range(0, len(filt), 3):
        row = filt[row_start:row_start + 3]
        cols = st.columns(3)
        for col, eq in zip(cols, row):
            with col:
                _render_eq_admin_card(eq)


def _stock_status(stock):
    """คืน (emoji, color, label) ตาม stock"""
    if stock is None or stock == 0:
        return ("🔴", "#A32D2D", "หมด")
    elif stock < 10:
        return ("🟡", "#BA7517", f"เหลือ {stock}")
    else:
        return ("🟢", "#1D9E75", f"คงเหลือ {stock}")


def _render_eq_admin_card(eq):
    """การ์ดอุปกรณ์ในหน้าจัดการ — มีรูป + ราคา + คงเหลือ + ปุ่มแก้/ลบ"""
    edit_key = f'ee_{eq["id"]}'
    is_editing = st.session_state.get(edit_key, False)

    with st.container(border=True):
        # รูป
        if eq.get('image_url'):
            try:
                st.image(eq['image_url'], use_container_width=True)
            except Exception:
                st.markdown(
                    '<div style="background:#333; height:140px; '
                    'border-radius:4px; display:flex; align-items:center; '
                    'justify-content:center; font-size:48px;">🧴</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="background:#333; height:140px; '
                'border-radius:4px; display:flex; align-items:center; '
                'justify-content:center; font-size:48px;">🧴</div>',
                unsafe_allow_html=True,
            )

        # ชื่อ
        st.markdown(f"**{eq.get('name', '-')}**")

        # SKU + หมวด + หน่วย
        sku = eq.get('sku') or '-'
        st.caption(f"SKU: {sku}")
        st.caption(f"📂 {eq.get('category', '-')}  |  📐 {eq.get('unit', 'ชิ้น')}")

        # คำอธิบาย
        desc = (eq.get('description') or '').strip()
        if desc:
            short = desc if len(desc) <= 80 else desc[:80] + "..."
            st.caption(f"📝 {short}")

        # แถวราคา + คงเหลือ
        emoji, color, stock_label = _stock_status(eq.get('stock', 0))
        st.markdown(
            f'<div style="display:flex; justify-content:space-between; '
            f'align-items:center; padding:6px 0; margin-top:6px; '
            f'border-top:1px solid #333;">'
            f'<span style="color:#C8A47E; font-weight:500;">'
            f'💰 ฿{eq.get("last_cost", 0):,.2f}</span>'
            f'<span style="color:{color}; font-size:12px;">'
            f'{emoji} {stock_label}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ปุ่ม แก้/ลบ
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("✏️ แก้ไข", key=f"e_{eq['id']}",
                         use_container_width=True,
                         type="primary" if is_editing else "secondary"):
                st.session_state[edit_key] = not is_editing
                st.rerun()
        with bc2:
            del_key = f'cd_{eq["id"]}'
            if st.session_state.get(del_key):
                if st.button("⚠️ ยืนยันลบ", key=f"d_{eq['id']}",
                             use_container_width=True):
                    db.delete_equipment(eq['id'])
                    st.session_state.pop(del_key, None)
                    st.rerun()
            else:
                if st.button("🗑️ ลบ", key=f"d_{eq['id']}",
                             use_container_width=True):
                    st.session_state[del_key] = True
                    st.rerun()

    # ---- Edit form ----
    if is_editing:
        with st.form(f"ef_{eq['id']}"):
            st.markdown(f"#### ✏️ แก้ไข: {eq.get('name', '')}")
            ec1, ec2 = st.columns(2)
            with ec1:
                n = st.text_input("ชื่อ", value=eq['name'])
                cl = db.get_categories()
                cat = st.selectbox(
                    "หมวด", cl,
                    index=cl.index(eq['category']) if eq['category'] in cl else 0,
                )
                sk = st.text_input("SKU", value=eq.get('sku') or '')
            with ec2:
                u = st.text_input("หน่วย", value=eq.get('unit', 'ชิ้น'))
                lc = st.number_input("ต้นทุน",
                                       value=float(eq.get('last_cost', 0)),
                                       step=1.0)
                stk = st.number_input("คงเหลือ",
                                        value=int(eq.get('stock', 0)),
                                        step=1)
            d = st.text_area("รายละเอียด", value=eq.get('description', ''))
            new_img = st.file_uploader(
                "เปลี่ยนรูป (เว้นว่าง = ใช้รูปเดิม)",
                type=['jpg', 'jpeg', 'png', 'webp'],
                key=f"img_{eq['id']}",
            )
            s1, s2 = st.columns(2)
            with s1:
                if st.form_submit_button("💾 บันทึก", type="primary",
                                            use_container_width=True):
                    update_data = {
                        'name': n, 'category': cat, 'sku': sk,
                        'unit': u, 'last_cost': lc,
                        'stock': stk, 'description': d,
                    }
                    if new_img:
                        new_url = db.upload_image(
                            new_img.getvalue(), new_img.name,
                        )
                        if new_url:
                            update_data['image_url'] = new_url
                    db.update_equipment(eq['id'], **update_data)
                    st.session_state.pop(edit_key, None)
                    st.rerun()
            with s2:
                if st.form_submit_button("❌ ยกเลิก",
                                            use_container_width=True):
                    st.session_state.pop(edit_key, None)
                    st.rerun()


# ==================================================================
# Reports
# ==================================================================

def render_reports():
    if not is_admin():
        st.error("เฉพาะแอดมิน")
        return

    st.markdown("## 📈 รายงาน")
    pos = db.get_purchase_orders(role='admin')
    if not pos:
        show_empty_state(
            "📊",
            "ยังไม่มีข้อมูลรายงาน",
            "เมื่อเริ่มมี PO ในระบบ รายงานนี้จะแสดงสถิติ + กราฟ + Top supplier ให้อัตโนมัติ",
        )
        return

    today = date.today()
    c1, c2, c3 = st.columns(3)
    with c1:
        period = st.selectbox("ช่วง", ["7 วัน", "30 วัน", "เดือนนี้", "ปีนี้", "ทั้งหมด", "กำหนดเอง"])
    if period == "7 วัน":
        sd, ed = today - timedelta(days=7), today
    elif period == "30 วัน":
        sd, ed = today - timedelta(days=30), today
    elif period == "เดือนนี้":
        sd, ed = today.replace(day=1), today
    elif period == "ปีนี้":
        sd, ed = today.replace(month=1, day=1), today
    elif period == "กำหนดเอง":
        with c2:
            sd = st.date_input("ตั้งแต่", value=today - timedelta(days=30))
        with c3:
            ed = st.date_input("ถึง", value=today)
    else:
        sd, ed = date(2000, 1, 1), today

    filt = [p for p in pos
             if sd.isoformat() <= p.get('created_at', '')[:10] <= ed.isoformat()]
    valid = [p for p in filt if p['status'] != 'ยกเลิก']

    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📝 PO", len(filt))
    m2.metric("✅ เสร็จสิ้น", sum(1 for p in valid if p['status'] == 'เสร็จสมบูรณ์'))
    m3.metric("💰 ยอดรวม", f"฿{sum(p.get('total', 0) for p in valid):,.2f}")
    avg = sum(p.get('total', 0) for p in valid) / len(valid) if valid else 0
    m4.metric("📊 เฉลี่ย/ใบ", f"฿{avg:,.2f}")

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### 🏭 ตาม Supplier")
        sup_d = {}
        for p in valid:
            s = p.get('supplier_name') or '-'
            if s not in sup_d:
                sup_d[s] = {'จำนวน': 0, 'ยอดรวม': 0}
            sup_d[s]['จำนวน'] += 1
            sup_d[s]['ยอดรวม'] += p.get('total', 0)
        if sup_d:
            df = pd.DataFrame([{'Supplier': k, **v} for k, v in sup_d.items()]).sort_values('ยอดรวม', ascending=False)
            st.dataframe(df, column_config={'ยอดรวม': st.column_config.NumberColumn(format="฿%.2f")},
                          hide_index=True, use_container_width=True)
    with c2:
        st.markdown("#### 📦 Top Items")
        it_d = {}
        for p in valid:
            for it in p.get('items', []):
                n = it.get('name', '-')
                if n not in it_d:
                    it_d[n] = {'จำนวน': 0, 'ยอดรวม': 0}
                it_d[n]['จำนวน'] += it.get('qty', 0)
                it_d[n]['ยอดรวม'] += it.get('subtotal', 0)
        if it_d:
            df = pd.DataFrame([{'รายการ': k, **v} for k, v in it_d.items()]).sort_values('ยอดรวม', ascending=False).head(10)
            st.dataframe(df, column_config={'ยอดรวม': st.column_config.NumberColumn(format="฿%.2f")},
                          hide_index=True, use_container_width=True)

    # ===== Interactive Charts =====
    st.divider()
    st.markdown("#### 📊 กราฟ")

    chart_c1, chart_c2 = st.columns(2)

    # 1) แท่งสถานะ
    with chart_c1:
        st.markdown("**สถานะ PO**")
        try:
            import plotly.express as px
            status_count = {}
            for p in filt:
                s = p['status']
                status_count[s] = status_count.get(s, 0) + 1
            if status_count:
                df_status = pd.DataFrame([
                    {'สถานะ': k, 'จำนวน': v}
                    for k, v in status_count.items()
                ])
                fig = px.bar(
                    df_status, x='สถานะ', y='จำนวน',
                    color='สถานะ',
                    color_discrete_map={
                        'รอจัดซื้อดำเนินการ': '#888',
                        'สั่งซื้อแล้ว': '#0F6E56',
                        'กำลังขนส่ง': '#BA7517',
                        'รับของแล้ว': '#1D9E75',
                        'มีปัญหา': '#A32D2D',
                        'เสร็จสมบูรณ์': '#27500A',
                        'ยกเลิก': '#666',
                    },
                )
                fig.update_layout(
                    showlegend=False,
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            st.caption("ติดตั้ง plotly เพื่อดูกราฟ — `pip install plotly`")
        except Exception as e:
            st.caption(f"กราฟไม่พร้อม: {e}")

    # 2) Pie chart ตาม supplier
    with chart_c2:
        st.markdown("**ยอดสั่งซื้อแยก Supplier**")
        try:
            import plotly.express as px
            sup_total = {}
            for p in valid:
                s = p.get('supplier_name') or '-'
                sup_total[s] = sup_total.get(s, 0) + p.get('total', 0)
            if sup_total:
                df_sup = pd.DataFrame([
                    {'Supplier': k, 'ยอดรวม': v}
                    for k, v in sup_total.items()
                ]).sort_values('ยอดรวม', ascending=False).head(8)
                fig = px.pie(df_sup, names='Supplier', values='ยอดรวม',
                              color_discrete_sequence=px.colors.sequential.Sunset)
                fig.update_layout(
                    height=300,
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            pass
        except Exception:
            pass

    # 3) Trend ตามเดือน (ถ้ามีข้อมูล > 7 วัน)
    if (ed - sd).days > 7:
        st.markdown("**📅 ยอดสั่งซื้อรายวัน**")
        try:
            import plotly.express as px
            from collections import defaultdict
            daily = defaultdict(float)
            for p in valid:
                d = p.get('created_at', '')[:10]
                if d:
                    daily[d] += p.get('total', 0)
            if daily:
                df_daily = pd.DataFrame([
                    {'วันที่': k, 'ยอด': v} for k, v in sorted(daily.items())
                ])
                fig = px.line(df_daily, x='วันที่', y='ยอด',
                                markers=True,
                                color_discrete_sequence=['#C8A47E'])
                fig.update_layout(
                    height=280,
                    margin=dict(l=10, r=10, t=10, b=10),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                )
                st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

    st.divider()
    st.markdown("#### 📥 Export")
    if filt:
        df = pd.DataFrame([{
            'PO': p['po_number'],
            'วันสร้าง': p.get('created_at', '')[:10],
            'ผู้สร้าง': p.get('created_by_name', ''),
            'Supplier': p.get('supplier_name', ''),
            'รายการ': len(p.get('items', [])),
            'ยอดรวม': p.get('subtotal', 0),
            'ส่วนลด': p.get('discount', 0),
            'ค่าส่ง': p.get('shipping_fee', 0),
            'VAT': p.get('vat', 0),
            'รวมสุทธิ': p.get('total', 0),
            'สถานะ': p['status'],
            'คาดได้รับ': p.get('expected_date', ''),
            'ได้รับจริง': p.get('received_date', ''),
        } for p in filt])
        csv = df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📄 CSV", data=csv,
                            file_name=f"po_{today.isoformat()}.csv",
                            mime="text/csv", type="primary")


# ==================================================================
# Users
# ==================================================================

def render_users():
    if not is_admin():
        st.error("เฉพาะแอดมิน")
        return

    st.markdown("## 👥 จัดการผู้ใช้")

    with st.expander("➕ เพิ่มผู้ใช้ใหม่"):
        with st.form("au", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                un = st.text_input("Username *")
                pw = st.text_input("รหัสผ่าน *", type="password")
                fn = st.text_input("ชื่อ-นามสกุล *")
            with c2:
                rl = st.selectbox("Role", list(db.ROLES.keys()),
                                    format_func=lambda x: db.ROLES[x])
                em = st.text_input("อีเมล", placeholder="สำหรับแจ้งเตือน")
            if st.form_submit_button("✅ เพิ่ม", type="primary"):
                if not un or not pw or not fn:
                    st.error("กรุณากรอกข้อมูล")
                else:
                    if db.add_user(un, pw, fn, rl, em):
                        st.success(f"เพิ่ม {un} แล้ว")
                        st.rerun()

    st.divider()
    users = db.get_users()
    me = st.session_state['user']

    for u in users:
        with st.container(border=True):
            c1, c2, c3, c4 = st.columns([2, 3, 2, 1])
            with c1:
                em_ico = "👑" if u['role'] == 'admin' else "👤"
                st.markdown(f"{em_ico} **{u['full_name']}**")
                st.caption(f"@{u['username']}")
            with c2:
                st.write(f"**Role:** {db.ROLES.get(u['role'], u['role'])}")
                if u.get('email'):
                    st.caption(f"✉️ {u['email']}")
            with c3:
                st.caption(f"สถานะ: {'🟢 ใช้งาน' if u.get('is_active') else '🔴 ปิด'}")
                st.caption(f"สร้าง: {fmt_date(u.get('created_at'))}")
            with c4:
                if st.button("✏️", key=f"eu_{u['id']}", use_container_width=True):
                    st.session_state[f'edu_{u["id"]}'] = True
                if u['id'] != me['id']:
                    cd_key = f'cdu_{u["id"]}'
                    if st.session_state.get(cd_key):
                        if st.button("⚠️ ยืนยันลบ", key=f"du2_{u['id']}",
                                     use_container_width=True):
                            db.delete_user(u['id'])
                            st.session_state.pop(cd_key, None)
                            st.success("ลบเรียบร้อย")
                            st.rerun()
                    else:
                        if st.button("🗑️", key=f"du_{u['id']}",
                                     use_container_width=True,
                                     help="ลบผู้ใช้"):
                            st.session_state[cd_key] = True
                            st.rerun()

            if st.session_state.get(f'edu_{u["id"]}'):
                with st.form(f"euf_{u['id']}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        n = st.text_input("ชื่อ", value=u['full_name'])
                        rl = st.selectbox("Role", list(db.ROLES.keys()),
                                            format_func=lambda x: db.ROLES[x],
                                            index=list(db.ROLES.keys()).index(u['role']))
                        ac = st.checkbox("ใช้งาน", value=u.get('is_active', True))
                    with c2:
                        em = st.text_input("อีเมล", value=u.get('email') or '')
                        np_ = st.text_input("เปลี่ยนรหัส (เว้นว่าง=ไม่เปลี่ยน)", type="password")
                    s1, s2 = st.columns(2)
                    with s1:
                        if st.form_submit_button("💾", type="primary"):
                            ud = {'full_name': n, 'role': rl, 'is_active': ac, 'email': em}
                            if np_:
                                ud['password'] = np_
                            db.update_user(u['id'], **ud)
                            del st.session_state[f'edu_{u["id"]}']
                            st.rerun()
                    with s2:
                        if st.form_submit_button("❌"):
                            del st.session_state[f'edu_{u["id"]}']
                            st.rerun()


# ==================================================================
# Notifications
# ==================================================================

def render_notifications():
    st.markdown("## 🔔 การแจ้งเตือน")
    user_id = uid()
    notifs = db.get_notifications(user_id)
    if not notifs:
        show_empty_state(
            "🔕",
            "ยังไม่มีการแจ้งเตือน",
            "เมื่อมีการอัปเดตเกี่ยวกับ PO ของคุณ ระบบจะแจ้งให้ทราบที่นี่",
        )
        return

    if any(not n['is_read'] for n in notifs):
        if st.button("✓ อ่านทั้งหมด"):
            db.mark_all_notifications_read(user_id)
            st.rerun()

    for n in notifs:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1])
            with c1:
                ico = "🔵" if not n['is_read'] else "⚪"
                st.markdown(f"{ico} **{n['title']}**")
                if n.get('message'):
                    st.caption(n['message'])
                st.caption(f"📅 {fmt_dt(n.get('created_at'))}")
            with c2:
                if n.get('po_id'):
                    if st.button("ดู PO →", key=f"vn_{n['id']}", use_container_width=True):
                        if not n['is_read']:
                            db.mark_notification_read(n['id'])
                        st.session_state['view_po_id'] = n['po_id']
                        st.session_state['mode'] = 'po_view'
                        st.rerun()
