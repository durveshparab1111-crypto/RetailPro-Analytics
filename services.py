import bcrypt
import smtplib
import cv2
from pyzbar.pyzbar import decode
from email.message import EmailMessage
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import TableStyle
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()

# ================= PASSWORD SECURITY =================

def hash_password(password: str):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password: str, hashed: str):
    return bcrypt.checkpw(password.encode(), hashed.encode())

# ================= EMAIL CONFIG =================

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_invoice_email(receiver_email, invoice_text, pdf_buffer):
    msg = EmailMessage()
    msg["Subject"] = "RetailPro Invoice"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver_email
    msg.set_content(invoice_text)

    msg.add_attachment(
        pdf_buffer.getvalue(),
        maintype="application",
        subtype="pdf",
        filename="Invoice.pdf"
    )

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)

# ================= PDF INVOICE =================

def generate_invoice_pdf(product_data, customer_name, qty):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer)
    elements = []
    styles = getSampleStyleSheet()

    subtotal = product_data["selling_price"] * qty
    gst = subtotal * 0.18
    cgst = gst / 2
    sgst = gst / 2
    total = subtotal + gst
    profit = (product_data["selling_price"] - product_data["cost_price"]) * qty

    elements.append(Paragraph("RetailPro Clothing Invoice", styles["Title"]))
    elements.append(Spacer(1, 20))

    data = [
        ["Customer", customer_name],
        ["Product", product_data["name"]],
        ["Category", product_data["category"]],
        ["Size", product_data["size"]],
        ["Color", product_data["color"]],
        ["Quantity", qty],
        ["Subtotal", f"₹ {subtotal:.2f}"],
        ["CGST (9%)", f"₹ {cgst:.2f}"],
        ["SGST (9%)", f"₹ {sgst:.2f}"],
        ["Total", f"₹ {total:.2f}"],
        ["Profit", f"₹ {profit:.2f}"]
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black)
    ]))

    elements.append(table)
    doc.build(elements)

    buffer.seek(0)

    invoice_text = f"""
RetailPro Clothing
--------------------------
Customer: {customer_name}
Product: {product_data["name"]}
Quantity: {qty}
Total: ₹ {total:.2f}
Thank you for shopping!
"""

    return buffer, invoice_text, total, profit

# ================= CAMERA SCANNER =================

def scan_barcode_camera():
    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        for barcode in decode(frame):
            code = barcode.data.decode("utf-8")
            cap.release()
            cv2.destroyAllWindows()
            return code

        cv2.imshow("Scan Barcode - Press Q to Exit", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return None

# ================= EAN13 VALIDATION =================

def validate_ean13(barcode):
    if len(barcode) != 13 or not barcode.isdigit():
        return False
    digits = list(map(int, barcode))
    check_sum = sum(digits[::2]) + sum([d * 3 for d in digits[1::2][:-1]])
    check_digit = (10 - (check_sum % 10)) % 10
    return check_digit == digits[-1]