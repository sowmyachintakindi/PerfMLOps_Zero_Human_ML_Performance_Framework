from flask import Flask, request, jsonify
import time
import random
import subprocess
import threading
import os
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ----------------------------------------
# Email Configuration
# ----------------------------------------
EMAIL_FROM = "sowmyar909@gmail.com"
EMAIL_TO = [
    "sowmyar909@gmail.com",
    "kumar.mbk2110@gmail.com"
]

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "sowmyar909@gmail.com"
SMTP_PASSWORD = "xxxx xxxx xxxx xxxx"  # Gmail App Password


def send_email(subject, body, to_emails=EMAIL_TO, html=False):
    if isinstance(to_emails, str):
        to_emails = [to_emails]

    msg = MIMEMultipart()
    msg["From"] = EMAIL_FROM
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "html" if html else "plain"))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(
                msg,
                from_addr=EMAIL_FROM,
                to_addrs=to_emails
            )
        print("[Email] Sent successfully")
    except Exception as e:
        print(f"[Email] Failed to send: {e}")


# ----------------------------------------
# Flask App
# ----------------------------------------
app = Flask(__name__)

# ----------------------------------------
# In-memory database
# ----------------------------------------
items = {}

# ----------------------------------------
# CRUD Endpoints
# ----------------------------------------
@app.route("/items/", methods=["POST"])
def create_item():
    data = request.json
    name = data.get("name")

    if not name:
        return jsonify(error="Name is required"), 400
    if name in items:
        return jsonify(error="Item already exists"), 400

    items[name] = data
    return jsonify(message="Item created", item=data), 200


@app.route("/items/<name>", methods=["GET"])
def read_item(name):
    if name not in items:
        return jsonify(error="Item not found"), 404
    return jsonify(items[name])


@app.route("/items/<name>", methods=["PUT"])
def update_item(name):
    if name not in items:
        return jsonify(error="Item not found"), 404

    data = request.json
    items[name] = data
    return jsonify(message="Item updated", item=data)


@app.route("/items/<name>", methods=["DELETE"])
def delete_item(name):
    if name not in items:
        return jsonify(error="Item not found"), 404

    del items[name]
    return jsonify(message=f"Item '{name}' deleted")


# ----------------------------------------
# JMeter Configuration
# ----------------------------------------
JMETER_PATH = "/Users/sowmyareddychintakindi/Desktop/EB1/Research/apache-jmeter-5.6.3/bin/jmeter"
JMETER_TEST_PLAN = "/Users/sowmyareddychintakindi/Desktop/EB1/Research/TestScripts/Python_API_script/TestPlan_Auto01122026.jmx"
JMETER_RESULTS = "/Users/sowmyareddychintakindi/Desktop/EB1/Research/TestScripts/Python_API_script/results.jtl"
JMETER_REPORT = "/Users/sowmyareddychintakindi/Desktop/EB1/Research/TestScripts/Python_API_script/report"
JMETER_LOG = "jmeter.log"


# ----------------------------------------
# Cleanup Previous Run
# ----------------------------------------
def cleanup_previous_run():
    if os.path.exists(JMETER_RESULTS):
        os.remove(JMETER_RESULTS)

    if os.path.exists(JMETER_LOG):
        os.remove(JMETER_LOG)

    if os.path.exists(JMETER_REPORT):
        subprocess.run(["rm", "-rf", JMETER_REPORT])


# ----------------------------------------
# Run JMeter + Email Report
# ----------------------------------------
def run_jmeter():
    try:
        cleanup_previous_run()

        print("[JMeter] Starting test...")
        subprocess.run(
            [
                JMETER_PATH,
                "-n",
                "-t", JMETER_TEST_PLAN,
                "-l", JMETER_RESULTS,
                "-e",
                "-o", JMETER_REPORT,
                "-j", JMETER_LOG
            ],
            check=True
        )
        print("[JMeter] Test completed successfully.")
    except Exception as e:
        send_email("JMeter Test Failed", str(e))
        return

    df = pd.read_csv(JMETER_RESULTS)

    total_requests = len(df)
    #passed = len(df[df["responseCode"] == 200])
    passed = len(df[df["responseCode"].isin([200, 204])])
    failed = total_requests - passed
    pass_percentage = (passed / total_requests) * 100 if total_requests else 0

    requests_per_label = df["label"].value_counts().to_frame("Requests")
    response_codes_per_label = (
        df.groupby("label")["responseCode"]
        .value_counts()
        .to_frame("Count")
    )
    avg_response_time_per_label = (
        df.groupby("label")["elapsed"]
        .mean()
        .to_frame("Avg Response Time (ms)")
    )

    html_body = f"""
   <h1>Email sent from Python code that triggered JMeter test</h1>  
   <h2>JMeter Test Summary</h2>

    <table border="1" cellpadding="6" cellspacing="0">
        <tr><th>Total Requests</th><td>{total_requests}</td></tr>
        <tr><th>Passed (200)</th><td>{passed}</td></tr>
        <tr><th>Failed</th><td>{failed}</td></tr>
        <tr><th>Pass Percentage</th><td><b>{pass_percentage:.2f}%</b></td></tr>
    </table>

    <h3>Requests per Label</h3>
    {requests_per_label.to_html(border=1)}

    <h3>Response Codes per Label</h3>
    {response_codes_per_label.to_html(border=1)}

    <h3>Average Response Time</h3>
    {avg_response_time_per_label.to_html(border=1)}
    """

    send_email(
        subject=f"JMeter Results – Pass {pass_percentage:.2f}%",
        body=html_body,
        html=True
    )


# ----------------------------------------
# Trigger JMeter on Startup
# ----------------------------------------
def trigger_jmeter_on_startup():
    def delayed_start():
        time.sleep(3)
        run_jmeter()

    threading.Thread(target=delayed_start, daemon=False).start()


# ----------------------------------------
# Health + Test Endpoints
# ----------------------------------------
@app.route("/")
def root():
    return jsonify(status="ok", message="API is running!")


@app.route("/fast")
def fast_endpoint():
    return jsonify(status="ok", response_time="fast")


@app.route("/slow")
def slow_endpoint():
    time.sleep(2)
    return jsonify(status="ok", response_time="slow (2s)")


@app.route("/random")
def random_endpoint():
    delay = random.uniform(0.1, 3.0)
    time.sleep(delay)
    return jsonify(status="ok", response_time=f"{delay:.2f}s")


@app.route("/unstable")
def unstable_endpoint():
    if random.random() < 0.2:
        return jsonify(error="Random failure occurred"), 500
    return jsonify(status="ok", message="Request succeeded")


# ----------------------------------------
# Run Server
# ----------------------------------------
if __name__ == "__main__":
    print("[Startup] Starting Flask server...")
    trigger_jmeter_on_startup()
    app.run(host="0.0.0.0", port=8000, debug=False)
