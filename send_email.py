# import smtplib, ssl
# from smtplib import SMTP
# with SMTP("example.com") as smtp:
# 	smtp.noop()
#
# smtp_server = "localhost"
# port = 25  # For starttls
# sender_email = "test@test.com"
# password = "password"
#
# # Create a secure SSL context
# # cert = {'subject': ((('4f5a651ab208', 'example.com'),),)}
# context = ssl.create_default_context()
#
# # Try to log in to server and send email
#
# server = smtplib.SMTP("example.com",port)
# server.ehlo() # Can be omitted
# server.starttls() # Secure the connection
# server.ehlo() # Can be omitted
# # server.login(sender_email, password)
# # TODO: Send email here
#
# receiver_email = "stobartcc@gmail.com"
# message = """\
# Subject: Hi there
#
# This message is sent from Python."""
#
# server.sendmail(sender_email, receiver_email, message, relay='api:10025')

import smtplib
receiver_email = "username@example.com"
sender_email = "username@example.com"
message = "this is a great success"
server = smtplib.SMTP("localhost", "587")
server.starttls()
server.login("username@example.com", "password")
# server.set_debuglevel(1)
server.sendmail(sender_email, receiver_email, message)
server.quit()
