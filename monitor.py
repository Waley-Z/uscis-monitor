"""A program for monitoring slot availability at USCIS Detroit."""
import time
import threading
from threading import Event
import smtplib
import signal
from email.mime.text import MIMEText
import requests
import json
# from bs4 import BeautifulSoup
from config import sender_email, sender_password, recipient_emails

SENDER_EMAIL = sender_email
SENDER_PASSWORD = sender_password # if using Gmail, check https://support.google.com/accounts/answer/185833
RECIPIENT_EMAILS = recipient_emails # list of recipients' emails, e.g., ["waleyz@umich.edu", "waley_zheng@sjtu.edu.cn"]
UPDATE_INTERVAL = 15  # Time to wait between requests in seconds

exit = Event()


class Monitor:
    """A Web page monitor."""

    def monitor_run(self):
        """Run monitor thread."""
        while not exit.is_set():
            try:
                response = requests.get("https://my.uscis.gov/appointmentscheduler-appointment/field-offices/state/MI")
                data = response.json()
                response.raise_for_status()
                slots = data[0]["timeSlots"]
            except (requests.exceptions.RequestException, requests.exceptions.HTTPError, json.JSONDecodeError, KeyError) as e:
                print(f"ERROR: {e}")
                exit.wait(UPDATE_INTERVAL)
                continue

            # print query result
            t = time.localtime()
            current_time = time.strftime("%H:%M:%S", t)
            print(f"{current_time} available slots are {slots}.")
            if not slots:
                exit.wait(UPDATE_INTERVAL)
            else:
                print("USCIS Detroit is available now!")
                msg = MIMEText(f"Book USCIS Detroit now!\nhttps://my.uscis.gov/appointmentscheduler-appointment/ca/en/office-search\nAvailable slots: {slots}.")
                msg["Subject"] = f"[USCIS Detroit] Booking Reminder"
                msg["From"] = f"Hongxiao Zheng <{SENDER_EMAIL}>"
                msg["To"] = ", ".join(RECIPIENT_EMAILS)
                s = smtplib.SMTP("smtp.gmail.com", 587)
                s.starttls()
                s.login(SENDER_EMAIL, SENDER_PASSWORD)
                s.sendmail(SENDER_EMAIL, RECIPIENT_EMAILS, msg.as_string())
                s.quit()
                break

    def __init__(self):
        threading.Thread(target=self.monitor_run).start()


def quit(signo, _frame):
    """Handle interuptions."""
    print(f"Interrupted by {signo}, shutting down")
    exit.set()


def main():
    """Run multiple monitors."""
    Monitor()


if __name__ == "__main__":
    for sig in ("TERM", "HUP", "INT"):
        signal.signal(getattr(signal, "SIG"+sig), quit)
    main()
