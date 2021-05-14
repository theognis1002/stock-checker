import logging
import os
import smtplib
from datetime import datetime
from email import encoders
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from decouple import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("stock-checker")


def dispatch_email(dataframe, filename):
    msg = MIMEMultipart()
    msg["Subject"] = f"Stock Checker - {datetime.utcnow().strftime('%m-%d-%Y')}"
    msg["From"] = config("SENDER_EMAIL_ADDRESS")
    msg["To"] = config("RECIPIENT_EMAIL_ADDRESS")

    style = """<style>
    h2 {
        color: #428bca;
    }
    .title-link {
        text-decoration: none;
    }
    table { 
        font-family: "Verdana", arial, sans-serif;
        border-spacing: 0px;
        border-collapse: collapse;
        width: 90%;
        margin: 25px 0px;
    }
    th, td {
        overflow: hidden;
        font-size: 12px;
        padding: 2px;
        text-align: center;
    }
    </style>"""
    html = """
    <html>
    <head>
    {0}
    </head>
    <body>
        <h2 style="color: #2e3943;">S&P500 statistics: </h2>
        {1}
    </body>
    </html>
    """.format(
        style, dataframe.to_html(index=False, escape=False)
    )

    part1 = MIMEText(html, "html")
    msg.attach(part1)

    with open(filename) as fp:
        record = MIMEBase("application", "octet-stream")
        record.set_payload(fp.read())
        encoders.encode_base64(record)
        record.add_header(
            "Content-Disposition", "attachment", filename=os.path.basename(filename)
        )
        msg.attach(record)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(config("EMAIL_APP_USER"), config("EMAIL_APP_PASSWORD"))
        smtp.send_message(msg)
        logger.info(f"Email notification sent successfully")
