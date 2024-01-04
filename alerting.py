import smtplib
import ssl
from decouple import config

smtpServer = config('SMTPSERVER')
port = config('SMTPPORT')
senderEmail = config('SMTPSENDEREMAIL')
recieverEmail = ['jethro@realtelematics.co.za', 'cameron@realtelematics.co.za']
name = "Qsmacker"

class EmailAlerts:
    def __init__(self):
        self.smtpServer = smtpServer
        self.port = port
        self.senderEmail = senderEmail
        self.recieverEmail = recieverEmail
        self.message = None
        self.context = ssl.create_default_context()
        self.server = None
        self.body = None
        self.name = name


    def send_email(self, subject, body):
        self.message = f"From: {name}\nSubject:{subject}\n\n {body}"
        try:
            self.server = smtplib.SMTP(smtpServer, port)
            self.server.starttls(context=self.context)
            for email in recieverEmail:
                self.server.sendmail(self.senderEmail, email, self.message)
        except Exception as e:
            print(e)
        finally:
            self.server.quit()

