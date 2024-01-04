import smtplib
import ssl
from decouple import config

smtpServer = config('SMTPSERVER')
port = config('SMTPPORT')
senderEmail = config('SMTPSENDEREMAIL')
recieverEmail = [config('SMTPRECEIVEREMAIL')]

class EmailAlerts:
    def __init__(self):
        self.smtpServer = smtpServer
        self.port = port
        self.senderEmail = senderEmail
        self.recieverEmail = recieverEmail
        self.message = None
        self.context = ssl.create_default_context()
        self.server = None

    def send_email(self, subject, body):
        self.message = f"From: {config('FROM_HEADER')}\nSubject:{subject}\n\n RADIUS MYSQL Replication Monitor is up and running"

