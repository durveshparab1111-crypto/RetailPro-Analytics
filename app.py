import streamlit as st
import psycopg2
import pandas as pd
import cv2
from pyzbar.pyzbar import decode
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import TableStyle
import smtplib
from email.message import EmailMessage

# ================= CONFIG =================
st.set_page_config(page_title="RetailPro Clothing", layout="wide")

# ================= CUSTOM CSS =================
st.markdown("""
<style>

/* Main Background */
.stApp {
    background: linear-gradient(135deg, #0f2027, #203a43, #2c5364);
    color: white;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #111827;
}

/* Titles */
h1, h2, h3 {
    color: #ffffff;
    font-weight: 700;
}

/* Input Fields */
.stTextInput > div > div > input,
.stNumberInput input {
    background-color: #1f2937;
    color: white;
    border-radius: 10px;
    border: 1px solid #374151;
}

/* Selectbox */
.stSelectbox > div > div {
    background-color: #1f2937;
    color: white;
    border-radius: 10px;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(45deg, #00c6ff, #0072ff);
    color: white;
    border-radius: 12px;
    border: none;
    padding: 0.6em 1.2em;
    font-weight: 600;
    transition: 0.3s ease;
}

.stButton > button:hover {
    transform: scale(1.05);
    box-shadow: 0px 0px 20px rgba(0,114,255,0.6);
}

/* Success Messages */
.stSuccess {
    background-color: #064e3b;
    color: #34d399;
    border-radius: 10px;
}

/* Error Messages */
.stError {
    background-color: #7f1d1d;
    color: #f87171;
    border-radius: 10px;
}

/* Metric Cards */
[data-testid="stMetric"] {
    background-color: #1f2937;
    padding: 20px;
    border-radius: 15px;
    box-shadow: 0px 4px 20px rgba(0,0,0,0.4);
}

</style>
""", unsafe_allow_html=True)
import os
from dotenv import load_dotenv

load_dotenv()

DB = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "port": "5432"
}

SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
def connect():
    return psycopg2.connect(**DB)

# ================= SESSION =================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "scanned_barcode" not in st.session_state:
    st.session_state.scanned_barcode = ""

# ================= AUTH =================
def auth():
    st.title("RetailPro Clothing")

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login"):
            conn = connect()
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE username=%s AND password=%s",(u,p))
            if cur.fetchone():
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Invalid Credentials")
            conn.close()

    with tab2:
        u = st.text_input("New Username")
        p = st.text_input("New Password", type="password")
        if st.button("Create Account"):
            conn = connect()
            cur = conn.cursor()
            try:
                cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)",(u,p))
                conn.commit()
                st.success("Account Created")
            except:
                conn.rollback()
                st.error("Username Exists")
            conn.close()

# ================= CAMERA =================
def scan_barcode():
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        for barcode in decode(frame):
            code = barcode.data.decode("utf-8")
            cap.release()
            cv2.destroyAllWindows()
            return code
        cv2.imshow("Scan Barcode", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
    return None

# ================= INVOICE =================
def generate_invoice(product, customer, qty, gst, total, profit):
    file_name = "invoice.pdf"
    doc = SimpleDocTemplate(file_name)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("RetailPro Clothing Invoice", styles["Title"]))
    elements.append(Spacer(1, 20))

    subtotal = product["selling_price"] * qty
    cgst = gst / 2
    sgst = gst / 2
    cgst_amt = subtotal * (cgst / 100)
    sgst_amt = subtotal * (sgst / 100)

    data = [
        ["Customer", customer],
        ["Product", product["name"]],
        ["Size", product["size"]],
        ["Color", product["color"]],
        ["Quantity", qty],
        ["Subtotal", f"₹ {subtotal}"],
        [f"CGST ({cgst}%)", f"₹ {cgst_amt}"],
        [f"SGST ({sgst}%)", f"₹ {sgst_amt}"],
        ["Total", f"₹ {total}"],
        ["Profit", f"₹ {profit}"],
    ]

    table = Table(data)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)
    return file_name

# ================= EMAIL =================
def send_email(receiver, file_path):
    msg = EmailMessage()
    msg["Subject"] = "Your RetailPro Invoice"
    msg["From"] = SENDER_EMAIL
    msg["To"] = receiver
    msg.set_content("Thank you for shopping with RetailPro.")

    with open(file_path, "rb") as f:
        msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename="Invoice.pdf")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
        smtp.send_message(msg)

# ================= DASHBOARD =================
# ================= DASHBOARD =================
def dashboard():

    st.markdown("""
    <h1 style='
    text-align:center;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    color: transparent;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 40px;
    '>
    📊 RetailPro Analytics Dashboard
    </h1>
    """, unsafe_allow_html=True)

    conn = connect()

    sales = pd.read_sql("SELECT * FROM sales", conn)
    products = pd.read_sql("SELECT * FROM products", conn)

    conn.close()

    if sales.empty:
        st.info("No sales data available yet.")
        return

    # ================= CLEAN DATA =================

    # Ensure numeric types
    sales["total"] = pd.to_numeric(sales["total"], errors="coerce")
    sales["profit"] = pd.to_numeric(sales["profit"], errors="coerce")

    # Clean text columns
    if "product_name" in sales.columns:
        sales["product_name"] = sales["product_name"].astype(str).str.strip().str.lower()

    if "name" in products.columns:
        products["name"] = products["name"].astype(str).str.strip().str.lower()

    # ================= KPI SECTION =================

    revenue = sales["total"].sum()
    profit = sales["profit"].sum()
    total_orders = len(sales)

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total Revenue", f"₹ {revenue:,.2f}")
    col2.metric("📈 Total Profit", f"₹ {profit:,.2f}")
    col3.metric("🛒 Total Orders", total_orders)

    with col4:
        st.write("")
        st.write("")
        if st.button("🗑️ Clear Data", key="clear_data"):
            conn = connect()
            cur = conn.cursor()
            try:
                cur.execute("DELETE FROM sales")
                conn.commit()
                st.success("✅ All sales data cleared successfully!")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error clearing data: {e}")
            finally:
                conn.close()

    st.markdown("---")

    # ================= CATEGORY ANALYTICS =================

    st.subheader("📦 Revenue by Category")

    if not products.empty and "category" in products.columns:

        merged = sales.merge(
            products[["name", "category"]],
            left_on="product_name",
            right_on="name",
            how="left"
        )

        merged = merged.dropna(subset=["category"])

        if not merged.empty:
            category_revenue = (
                merged.groupby("category")["total"]
                .sum()
                .reset_index()
                .sort_values(by="total", ascending=False)
            )

            st.bar_chart(category_revenue.set_index("category"))
        else:
            st.warning("No matching category data found.")

    else:
        st.warning("Products table missing category column.")

    st.markdown("---")

    # ================= PRODUCT ANALYTICS =================

    st.subheader("👕 Product-wise Revenue")

    product_revenue = (
        sales.groupby("product_name")["total"]
        .sum()
        .reset_index()
        .sort_values(by="total", ascending=False)
    )

    if not product_revenue.empty:
        st.bar_chart(product_revenue.set_index("product_name"))
    else:
        st.warning("No product revenue data available.")

    st.markdown("---")

    # ================= SALES TREND =================

    if "sale_date" in sales.columns:
        st.subheader("📅 Sales Trend")

        sales["sale_date"] = pd.to_datetime(sales["sale_date"], errors="coerce")
        sales = sales.dropna(subset=["sale_date"])

        if not sales.empty:
            daily_sales = (
                sales.groupby(sales["sale_date"].dt.date)["total"]
                .sum()
            )

            st.line_chart(daily_sales)

    # ================= LOW STOCK ALERT =================

    if not products.empty and "stock" in products.columns:

        low_stock = products[products["stock"] < 5]

        if not low_stock.empty:
            st.markdown("---")
            st.warning("⚠ Low Stock Alert (Below 5 Units)")
            st.dataframe(low_stock[["name", "category", "stock"]])
# ================= ADD PRODUCT =================
def add_product():
    st.header("Add Product")

    name = st.text_input("Product Name")
    category = st.selectbox("Category", ["Shirt","T-Shirt","Jeans","Jacket"])
    size = st.selectbox("Size", ["XS","S","M","L","XL","XXL"])

    color_option = st.selectbox("Color",
        ["Black","White","Blue","Red","Green","Grey","Orange","Other"]
    )

    if color_option == "Other":
        color = st.text_input("Enter Custom Color")
    else:
        color = color_option

    cost = st.number_input("Cost Price", min_value=0.0)
    selling = st.number_input("Selling Price", min_value=0.0)
    stock = st.number_input("Stock", min_value=0)

    barcode = st.text_input("Barcode", value=st.session_state.scanned_barcode)

    if st.button("Scan Barcode"):
        scanned = scan_barcode()
        if scanned:
            st.session_state.scanned_barcode = scanned
            st.rerun()

    if st.button("Add Product"):
        conn = connect()
        cur = conn.cursor()
        try:
            cur.execute("""
            INSERT INTO products(name,category,size,color,cost_price,selling_price,stock,barcode)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
            """,(name,category,size,color,cost,selling,stock,barcode))
            conn.commit()
            st.success("Product Added")
            st.session_state.scanned_barcode = ""
        except:
            conn.rollback()
            st.error("Barcode already exists")
        conn.close()

# ================= BILLING =================
# ================= BILLING =================
def billing():

    # -------- Premium Gradient Heading --------
    st.markdown("""
    <h1 style='
    text-align:center;
    background: linear-gradient(90deg, #00c6ff, #0072ff);
    -webkit-background-clip: text;
    color: transparent;
    font-size: 42px;
    font-weight: 800;
    margin-bottom: 40px;
    '>
    🧾 RetailPro Billing Dashboard
    </h1>
    """, unsafe_allow_html=True)

    # -------- Barcode Input + Scan --------
    col1, col2 = st.columns([3,1])

    with col1:
        barcode = st.text_input("Enter Barcode", value=st.session_state.scanned_barcode)

    with col2:
        st.write("")
        st.write("")
        if st.button("📷 Scan"):
            scanned = scan_barcode()
            if scanned:
                st.session_state.scanned_barcode = scanned
                st.rerun()

    if barcode:
        conn = connect()
        cur = conn.cursor()

        cur.execute(
            "SELECT name, selling_price, cost_price, stock FROM products WHERE barcode=%s",
            (barcode,)
        )
        product = cur.fetchone()

        if product:
            name, price, cost, stock = product

            qty = st.number_input("Quantity", min_value=1, max_value=stock, value=1)

            # Fix Decimal issue
            price = float(price)
            cost = float(cost)

            subtotal = price * qty
            gst = subtotal * 0.18
            cgst = gst / 2
            sgst = gst / 2
            total = subtotal + gst
            profit = (price - cost) * qty

            # -------- Beautiful Summary Box --------
            st.markdown("""
            <div style='
            background-color:#1f2937;
            padding:25px;
            border-radius:15px;
            box-shadow:0 0 20px rgba(0,0,0,0.5);
            margin-top:20px;
            '>
            """, unsafe_allow_html=True)

            st.write(f"**Product:** {name}")
            st.write(f"**Subtotal:** ₹{subtotal:.2f}")
            st.write(f"**CGST (9%):** ₹{cgst:.2f}")
            st.write(f"**SGST (9%):** ₹{sgst:.2f}")
            st.write(f"**Total GST:** ₹{gst:.2f}")
            st.write(f"**Total Amount:** ₹{total:.2f}")
            st.write(f"**Profit:** ₹{profit:.2f}")

            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")

            customer_name = st.text_input("Customer Name")
            customer_email = st.text_input("Customer Email")

            if st.button("🚀 Confirm Sale"):

                # Save Sale
                cur.execute("""
                    INSERT INTO sales(product_name, customer_name, quantity, gst, total, profit)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (name, customer_name, qty, gst, total, profit))

                # Update Stock
                cur.execute(
                    "UPDATE products SET stock = stock - %s WHERE barcode=%s",
                    (qty, barcode)
                )

                conn.commit()
                conn.close()

                invoice_text = f"""
RetailPro Clothing
-------------------------
Product: {name}
Quantity: {qty}
Subtotal: ₹{subtotal:.2f}
CGST (9%): ₹{cgst:.2f}
SGST (9%): ₹{sgst:.2f}
Total GST: ₹{gst:.2f}
Total Amount: ₹{total:.2f}
-------------------------
Thank you for shopping!
"""

                # -------- EMAIL --------
                try:
                    msg = EmailMessage()
                    msg["Subject"] = "RetailPro Invoice"
                    msg["From"] = SENDER_EMAIL
                    msg["To"] = customer_email
                    msg.set_content(invoice_text)

                    server = smtplib.SMTP("smtp.gmail.com", 587)
                    server.starttls()
                    server.login(SENDER_EMAIL, SENDER_PASSWORD)
                    server.send_message(msg)
                    server.quit()

                    st.success("✅ Invoice Email Sent Successfully")

                except Exception as e:
                    st.error(f"❌ Email Failed: {e}")

                # -------- PDF DOWNLOAD --------
                from io import BytesIO
                from reportlab.platypus import SimpleDocTemplate, Paragraph
                from reportlab.lib.styles import ParagraphStyle

                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer)
                elements = []
                elements.append(Paragraph(invoice_text, ParagraphStyle(name='Normal')))
                doc.build(elements)

                st.download_button(
                    label="📥 Download Invoice",
                    data=buffer.getvalue(),
                    file_name="invoice.pdf",
                    mime="application/pdf"
                )

        else:
            st.error("Product not found.")
# ================= MAIN =================
if not st.session_state.logged_in:
    auth()
else:
    menu = st.sidebar.radio("Navigation", ["Dashboard","Add Product","Billing","Logout"])

    if menu == "Dashboard":
        dashboard()
    elif menu == "Add Product":
        add_product()
    elif menu == "Billing":
        billing()
    elif menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()