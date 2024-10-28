import smtplib
from email.mime.text import MIMEText

# Define email parameters
sender = "ripeart@gmail.com"
recipient = "eric@level3itcorp.com"
subject = "Test Email"
body = "This is a test email."

# Create the email message
msg = MIMEText(body)
msg['Subject'] = subject
msg['From'] = sender
msg['To'] = recipient

# Add a more standard Received header to simulate sending IP
msg.add_header('Received', 'from 2.56.1.1')

# Connect to the SMTP server
with smtplib.SMTP('smtp.gmail.com', 587) as server:
    server.starttls()
    server.login("ripeart@gmail.com", "rlbs cqyn jlao jqnb")
    server.sendmail(sender, recipient, msg.as_string())

