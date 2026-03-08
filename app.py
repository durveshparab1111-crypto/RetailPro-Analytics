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
DB = {
    "host": "localhost",
    "database": "customer_analysis",
    "user": "postgres",
    "password": "durvesh1107",
    "port": "5432"
}

SENDER_EMAIL = "durveshparab200410@gmail.com"
SENDER_PASSWORD = "zswralvmysxpnuny"

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

    # ---------------- LOGIN ----------------
    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if username == "" or password == "":
                st.error("Please fill all fields")
            else:
                conn = connect()
                cur = conn.cursor()

                cur.execute(
                    "SELECT * FROM users WHERE username=%s AND password=%s",
                    (username, password)
                )

                if cur.fetchone():
                    st.session_state.logged_in = True
                    st.success("Login Successful")
                    st.rerun()
                else:
                    st.error("Invalid Credentials")

                conn.close()

    # ---------------- SIGNUP ----------------
    with tab2:
        new_username = st.text_input("New Username")
        new_password = st.text_input("New Password", type="password")

        if st.button("Create Account"):
            if new_username == "" or new_password == "":
                st.error("Please fill all fields")
            else:
                conn = connect()
                cur = conn.cursor()

                # Check if username exists
                cur.execute(
                    "SELECT * FROM users WHERE username=%s",
                    (new_username,)
                )

                if cur.fetchone():
                    st.error("Username already exists")
                else:
                    cur.execute(
                        "INSERT INTO users(username, password) VALUES(%s, %s)",
                        (new_username, new_password)
                    )
                    conn.commit()
                    st.success("Account Created Successfully")

                conn.close()
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

# ================= DASHBOARD =================
# ================= DASHBOARD =================
def dashboard():
    
    import pandas as pd
    import matplotlib.pyplot as plt
    from datetime import datetime

    conn = connect()
    cur = conn.cursor()

    # ===== TOTAL KPIs =====
    try:
        cur.execute("""
            SELECT 
                COALESCE(SUM(selling_price),0), 
                COALESCE(SUM(profit),0), 
                COUNT(*)
            FROM products
        """)
        result = cur.fetchone()

        total_revenue = float(result[0])
        total_profit = float(result[1])
        total_orders = int(result[2])

    except:
        total_revenue = 0
        total_profit = 0
        total_orders = 0

    # ===== DAILY REVENUE DATA =====
    try:
        cur.execute("""
            SELECT DATE(created_at), 
                   SUM(selling_price), 
                   SUM(profit), 
                   COUNT(*)
            FROM products
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)
        data = cur.fetchall()

        df = pd.DataFrame(data, columns=["Date", "Revenue", "Profit", "Orders"])

    except:
        df = pd.DataFrame(columns=["Date", "Revenue", "Profit", "Orders"])

    conn.close()

    # ===== TITLE =====
    st.title("📊 RetailPro Analytics Dashboard")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("💰 Total Revenue", f"₹ {total_revenue:,.2f}")
    col2.metric("📈 Total Profit", f"₹ {total_profit:,.2f}")
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

    # ===== CHART SECTION =====
    if not df.empty:

        st.subheader("📅 Revenue Over Time")

        fig1 = plt.figure()
        plt.plot(df["Date"], df["Revenue"])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Revenue")
        st.pyplot(fig1)

        st.subheader("📈 Profit Over Time")

        fig2 = plt.figure()
        plt.plot(df["Date"], df["Profit"])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Profit")
        st.pyplot(fig2)

        st.subheader("🛍 Orders Over Time")

        fig3 = plt.figure()
        plt.plot(df["Date"], df["Orders"])
        plt.xticks(rotation=45)
        plt.xlabel("Date")
        plt.ylabel("Orders")
        st.pyplot(fig3)

    else:
        st.info("No sales data available yet.")

    st.divider()

    # ===== CSV DOWNLOAD =====
    summary_data = {
        "Date Generated": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        "Total Revenue": [total_revenue],
        "Total Profit": [total_profit],
        "Total Orders": [total_orders]
    }

    summary_df = pd.DataFrame(summary_data)

    csv = summary_df.to_csv(index=False)

    st.download_button(
        label="📥 Download Daily Summary CSV",
        data=csv,
        file_name="daily_summary.csv",
        mime="text/csv"
    )
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
    
    conn = connect()
    cur = conn.cursor()

    st.subheader("🧾 RetailPro Billing")

    barcode = st.text_input("Scan / Enter Barcode")

    if barcode:

        # Fetch product
        cur.execute("""
            SELECT name, selling_price, cost_price, stock 
            FROM products 
            WHERE barcode = %s
        """, (barcode,))
        
        product = cur.fetchone()

        if product:

            name, price, cost, stock = product

            st.write(f"Product: {name}")
            st.write(f"Price: ₹{price}")
            st.write(f"Stock Available: {stock}")

            qty = st.number_input("Quantity", min_value=1, max_value=stock, value=1)

            # ===== CALCULATIONS (MUST BE BEFORE BUTTON) =====
            price = float(price)
            cost = float(cost)

            subtotal = price * qty
            gst = subtotal * 0.18
            cgst = gst / 2
            sgst = gst / 2
            total = subtotal + gst
            profit = (price - cost) * qty

            st.write(f"Subtotal: ₹{subtotal:.2f}")
            st.write(f"CGST (9%): ₹{cgst:.2f}")
            st.write(f"SGST (9%): ₹{sgst:.2f}")
            st.write(f"Total GST: ₹{gst:.2f}")
            st.write(f"Total Amount: ₹{total:.2f}")

            customer_email = st.text_input("Customer Email")

            # ===== CONFIRM BUTTON =====
            if st.button("🔥 Confirm Sale"):

                from datetime import datetime

                # Insert into sales
                cur.execute("""
                    INSERT INTO sales 
                    (barcode, selling_price, profit, quantity, created_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (barcode, total, profit, qty, datetime.now()))

                # Update stock
                cur.execute("""
                    UPDATE products 
                    SET stock = stock - %s 
                    WHERE barcode = %s
                """, (qty, barcode))

                conn.commit()

                # Create invoice text
                invoice_text = f"""
                RetailPro Clothing
                ----------------------------------
                Product: {name}
                Quantity: {qty}
                Subtotal: ₹{subtotal:.2f}
                CGST (9%): ₹{cgst:.2f}
                SGST (9%): ₹{sgst:.2f}
                Total GST: ₹{gst:.2f}
                ----------------------------------
                Total Amount: ₹{total:.2f}

                Thank you for shopping!
                """

                st.success("✅ Sale Completed Successfully!")
                st.text(invoice_text)

                # ===== EMAIL SECTION =====
                if customer_email:

                    from email.message import EmailMessage
                    import smtplib

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

                        st.success("📧 Invoice Email Sent Successfully!")

                    except Exception as e:
                        st.error(f"❌ Email Failed: {e}")

                # ===== PDF DOWNLOAD =====
                from io import BytesIO
                from reportlab.platypus import SimpleDocTemplate, Paragraph
                from reportlab.lib.styles import getSampleStyleSheet

                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer)
                elements = []

                styles = getSampleStyleSheet()
                elements.append(Paragraph(invoice_text.replace("\n", "<br/>"), styles["Normal"]))
                doc.build(elements)

                st.download_button(
                    label="📄 Download Invoice PDF",
                    data=buffer.getvalue(),
                    file_name="invoice.pdf",
                    mime="application/pdf"
                )

        else:
            st.error("❌ Product not found.")

    conn.close()
# =========================================
# 🔥 PASTE LOGIN CHECK HERE (BOTTOM)
# =========================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False


if not st.session_state.logged_in:
    auth()
else:

    menu = st.sidebar.radio(
        "Navigation",
        ["Dashboard", "Add Product", "Billing", "Data Management", "Logout"]
    )

    if menu == "Dashboard":
        dashboard()

    elif menu == "Add Product":
        add_product()

    elif menu == "Billing":
        billing()

    elif menu == "Data Management":

        st.markdown("## ⚙ Data Management Panel")
        st.warning("⚠ This will delete ALL product data permanently!")

        if st.button("🗑 Clear All Data"):

            conn = connect()
            cur = conn.cursor()

            try:
                cur.execute("DELETE FROM products")
                conn.commit()

                for key in list(st.session_state.keys()):
                    if key != "logged_in":
                        del st.session_state[key]

                st.success("✅ All Data Cleared Successfully!")
                st.rerun()

            except Exception as e:
                st.error(f"Error: {e}")

            conn.close()

    elif menu == "Logout":
        st.session_state.logged_in = False
        st.rerun()