#!/bin/bash
cd "$(dirname "$0")"

echo ""
echo "=========================================="
echo " 📦 Lab Parfumo PO Pro System"
echo "=========================================="

if ! command -v python3 &> /dev/null; then
    echo "❌ ไม่พบ Python 3"
    read -p "กด Enter เพื่อออก..."
    exit 1
fi

if ! python3 -c "import streamlit, supabase, reportlab, pandas, PIL, requests" 2>/dev/null; then
    echo "📦 กำลังติดตั้ง dependencies..."
    python3 -m pip install -r requirements.txt
fi

echo ""
echo "🚀 เริ่ม web server..."
python3 -m streamlit run app.py
