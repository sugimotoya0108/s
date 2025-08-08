
from flask import Flask, request, jsonify, send_file, send_from_directory
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
import os

app = Flask(__name__, static_folder="static")

COMPANY = {
    "name": "株式会社 SUGIMOTOYA",
    "ceo": "杉本 直樹",
    "address": "〒192-0014 東京都八王子市みつい台2-2-8",
    "tel": "TEL 042-649-7565",
    "fax": "FAX 042-649-7566",
    "mobile": "携帯 090-4133-6276",
    "email1": "info@sugimotoya-co.jp",
    "email2": "n.sugimoto@sugimotoya-co.jp",
    "website": "sugimotoya-rehome.com",
    "license": "東京都知事 許可(般-3)第152475号 内外装リフォーム工事一式",
    "logo_path": os.path.join(os.path.dirname(__file__), "assets", "logo.jpg"),
}

PRICE_ITEMS = {
    "K-01": {"desc": "システムキッチン標準", "unit_price": 450000},
    "K-02": {"desc": "給排水取替", "unit_price": 80000},
    "T-01": {"desc": "便器交換（温水洗浄便座付）", "unit_price": 120000},
    "W-01": {"desc": "洗面化粧台交換（W=750）", "unit_price": 90000},
    "B-01": {"desc": "ユニットバス1216サイズ", "unit_price": 600000},
}

def _header_footer(c, title):
    W, H = A4
    c.setFillColorRGB(0.15, 0.35, 0.65)
    c.rect(0, H-30, W, 30, stroke=0, fill=1)
    try:
        c.drawImage(COMPANY["logo_path"], 10, H-28, width=40, height=14, mask='auto')
    except Exception:
        pass
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, H-20, COMPANY["name"])
    c.setFont("Helvetica", 9)
    c.drawRightString(W-20, H-20, title)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    footer = f"{COMPANY['address']} | {COMPANY['tel']} | {COMPANY['fax']} | {COMPANY['mobile']} | {COMPANY['website']}"
    c.drawString(20, 15, footer)

@app.route("/")
def index():
    return send_from_directory(app.static_folder, "index.html")

@app.route("/api/estimate/generate", methods=["POST"])
def estimate_generate():
    data = request.json or {}
    tax_rate = data.get("tax_rate", 0.10)
    req_lines = data.get("lines", [])
    lines, subtotal = [], 0
    for item in req_lines:
        code = item.get("code")
        qty = int(item.get("qty", 1))
        if code not in PRICE_ITEMS:
            continue
        unit_price = PRICE_ITEMS[code]["unit_price"]
        line_total = unit_price * qty
        subtotal += line_total
        lines.append({
            "code": code,
            "desc": PRICE_ITEMS[code]["desc"],
            "qty": qty,
            "line_total": line_total
        })
    tax = int(subtotal * tax_rate)
    total = subtotal + tax
    return jsonify({"lines": lines, "subtotal": subtotal, "tax": tax, "total": total})

@app.route("/api/estimate/pdf", methods=["POST"])
def estimate_pdf():
    data = request.json or {}
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    _header_footer(c, "見積書")
    W, H = A4
    y = H-70
    c.setFont("Helvetica-Bold", 16)
    c.drawString(30, y, "見積書（デモ）")
    y -= 30
    c.setFont("Helvetica", 11)
    for line in data.get("lines", []):
        c.drawString(40, y, f"- {line['desc']} x {line['qty']}  = ¥{line['line_total']:,}")
        y -= 18
        if y < 100:
            c.showPage(); _header_footer(c, "見積書"); y = H-70
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, f"小計: ¥{data.get('subtotal',0):,}"); y -= 18
    c.drawString(40, y, f"消費税: ¥{data.get('tax',0):,}"); y -= 18
    c.drawString(40, y, f"合計: ¥{data.get('total',0):,}")
    c.showPage(); c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="estimate_demo.pdf", mimetype="application/pdf")

@app.route("/api/presentation/pdf", methods=["POST"])
def presentation_pdf():
    info = request.json or {}
    customer = info.get("customer", {"name":"山田 太郎 様","address":"東京都新宿区〇〇","date":"2025/08/08"})
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    W, H = A4

    _header_footer(c, "表紙 / Cover")
    c.setFont("Helvetica-Bold", 22)
    c.drawString(30, H-90, "リフォーム提案書（デモ）")
    c.setFont("Helvetica", 10)
    c.setFillColor(colors.grey); c.drawString(30, H-115, "お客様名")
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12); c.drawString(30, H-130, customer.get("name",""))
    c.setFillColor(colors.grey); c.setFont("Helvetica", 10); c.drawString(220, H-115, "現場住所")
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12); c.drawString(220, H-130, customer.get("address",""))
    c.setFillColor(colors.grey); c.setFont("Helvetica", 10); c.drawString(410, H-115, "日付")
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12); c.drawString(410, H-130, customer.get("date",""))
    c.setStrokeColor(colors.grey); c.rect(30, H-350, W-60, 180, stroke=1, fill=0)
    c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.grey)
    c.drawCentredString(W/2, H-260, "キービジュアル（完成イメージ）")
    c.setFillColor(colors.black)
    c.showPage()

    _header_footer(c, "プラン概要")
    c.setFont("Helvetica-Bold", 16); c.drawString(30, H-70, "提案プラン概要")
    bullets = info.get("bullets", [
        "キッチン：I型2550／食洗機搭載／静音シンク",
        "浴室：ユニットバス1216／保温浴槽／換気乾燥暖房機",
        "トイレ：節水型＋温水洗浄便座",
        "洗面：W750三面鏡／LED照明",
    ])
    y = H-100; c.setFont("Helvetica", 11)
    for b in bullets:
        c.circle(35, y+3, 1.5, stroke=1, fill=1); c.drawString(45, y, b); y -= 18
    c.rect(W-210, H-320, 160, 180, stroke=1, fill=0)
    c.setFont("Helvetica-Oblique", 10); c.setFillColor(colors.grey)
    c.drawCentredString(W-130, H-230, "間取り図 / 3Dイメージ")
    c.setFillColor(colors.black); c.showPage()

    _header_footer(c, "価格まとめ")
    c.setFont("Helvetica-Bold", 16); c.drawString(30, H-70, "価格まとめ（税抜）")
    rows = info.get("price_rows", [
        ("キッチン", "¥630,000"),
        ("浴室", "¥900,000"),
        ("トイレ", "¥200,000"),
        ("洗面室", "¥145,000"),
        ("諸経費", "¥90,400"),
    ])
    y = H-110; c.setFont("Helvetica", 11)
    for name, val in rows:
        c.drawString(40, y, name); c.drawRightString(W-40, y, val); y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y-10, "小計"); c.drawRightString(W-40, y-10, "¥1,965,400")
    c.drawString(40, y-30, "消費税(10%)"); c.drawRightString(W-40, y-30, "¥196,540")
    c.drawString(40, y-50, "合計"); c.drawRightString(W-40, y-50, "¥2,161,940")
    c.showPage()

    _header_footer(c, "会社情報")
    c.setFont("Helvetica-Bold", 16); c.drawString(30, H-70, "会社情報")
    c.setFont("Helvetica", 11)
    c.drawString(40, H-100, COMPANY["name"])
    c.drawString(40, H-120, f"代表取締役 {COMPANY['ceo']}")
    c.drawString(40, H-140, COMPANY["license"])
    c.drawString(40, H-160, COMPANY["address"])
    c.drawString(40, H-180, f"{COMPANY['tel']} / {COMPANY['fax']}")
    c.drawString(40, H-200, COMPANY["mobile"])
    c.drawString(40, H-220, COMPANY["email1"])
    c.drawString(40, H-240, COMPANY["email2"])
    c.drawString(40, H-260, COMPANY["website"])
    c.showPage()

    c.save(); buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="presentation_demo.pdf", mimetype="application/pdf")

@app.route("/static/<path:filename>")
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
