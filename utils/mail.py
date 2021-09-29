"""Simple funciton to send emails via Gmail."""
#!/usr/bin/python3
# -*- coding: utf-8 -*-
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from email.message import EmailMessage
import os

def send_email(receiver, subject, content, attachments=None):
        if attachments is None:
            attachments = []
        if isinstance(receiver, str):
            receiver = [receiver]
        
        # Credentials
        sender = 'TODO: Email address'
        username = 'TODO: Email address'
        password = 'TODO: Password'

        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = 'Turnverein Mettmenstetten <{}>'.format(sender)
        #msg['To'] = target

        msg.set_content(content)

        msg.add_alternative(content, subtype='html')

        for png_cid in attachments:
            full_path_to_png = os.path.abspath(os.path.join(
                os.path.dirname(__file__), attachments[png_cid]
            ))
            with open(full_path_to_png, 'rb') as png_file:
                file_contents = png_file.read()
                msg.get_payload()[1].add_related(file_contents, 'image', 'png', cid=png_cid)

        # The actual mail sent (Gmail SMTP)
        with smtplib.SMTP('smtp.gmail.com:587') as server:
            server.starttls()
            server.login(username, password)
            for rec in receiver:
                msg['To'] = rec
                server.sendmail(msg['From'], rec, msg.as_string())
            

            
# def send_email(receiver, sbj, msg, txt_type='plain'):
#     """Send a message
# 
#     Arguments:
#         receivers (str/tuple): email address(es)
#         sbj (str): The subject of the message
#         msg (str): The message
# 
#     Optional Arguments:
#         txt_type (str): 'plain' or 'html' (Default 'plain')
#         msg_charset (str): 'UTF-8', 'ascii' or another encoding;
#                            encoding for the message. (Default 'UTF-8')
#         sbj_charset (str): as msg_charset (Default None).
#     """
#     if isinstance(receiver, str):
#         receiver = [receiver]
# 
#     # Credentials
#     sender = 'tvmettmenstetten@gmail.com'
#     username = 'tvmettmenstetten@gmail.com'
#     password = '16tvMettmi'
# 
#     mime = MIMEText(msg.encode('UTF-8'), txt_type, 'UTF-8')
#     mime['From'] = 'Turnverein Mettmenstetten <{}>'.format(sender)
#     mime['Reply-To'] = 'Turnverein Mettmenstetten <tickets@tvmettmenstetten.ch>'
#     mime['Subject'] = Header(sbj.encode('UTF-8'), 'UTF-8')
# 
#     # The actual mail sent (Gmail SMTP)
#     server = smtplib.SMTP('smtp.gmail.com:587')
#     server.starttls()
#     server.login(username, password)
#     for rec in receiver:
#         mime['To'] = rec
#         server.sendmail(mime['From'], rec, mime.as_string())
#     server.quit()


if __name__ == '__main__':
    send_email('jon.eugster@gmx.ch', 'Test', 'Test für Fake-Absender.\nLg Jon')
