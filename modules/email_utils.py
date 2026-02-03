import smtplib
import streamlit as st
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import os

def send_email_with_pdf(to_email, subject, body, pdf_path):
    """
    Sends an email with a PDF attachment using SMTP credentials from st.secrets.
    
    Args:
        to_email (str): Recipient email address.
        subject (str): Email subject.
        body (str): Email body text.
        pdf_path (str): Path to the PDF file to attach.
        
    Returns:
        bool: True if sent successfully, False otherwise.
    """
    # Check for secrets
    if "smtp" not in st.secrets:
        st.error("SMTP secrets not configured! Please add [smtp] section to .streamlit/secrets.toml")
        return False
        
    smtp_config = st.secrets["smtp"]
    smtp_server = smtp_config.get("server", "smtp.gmail.com")
    smtp_port = smtp_config.get("port", 587)
    smtp_user = smtp_config.get("username")
    smtp_password = smtp_config.get("password")
    
    if not smtp_user or not smtp_password:
        st.error("SMTP username or password missing in secrets.")
        return False
        
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach PDF
    try:
        with open(pdf_path, "rb") as f:
            pdf_data = f.read()
            pdf_name = os.path.basename(pdf_path)
            part = MIMEApplication(pdf_data, Name=pdf_name)
            part['Content-Disposition'] = f'attachment; filename="{pdf_name}"'
            msg.attach(part)
    except Exception as e:
        st.error(f"Failed to attach PDF: {e}")
        return False
        
    # Send Email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email: {e}")
        return False
