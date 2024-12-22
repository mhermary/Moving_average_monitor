#!/usr/bin/env python3
import os
import smtplib
from email.message import EmailMessage
import yfinance as yf # pip isntall yfinance

NUM_MA_DAYS = 100 # Number of days to be included in the simple moving average

# Load environment variables from .env file
def load_environment_variables(env_file=".env"):
    """Load environment variables from a .env file."""
    try:
        with open(env_file, "r") as file:
            for line in file:
                # Ignore comments and empty lines
                if line.strip() and not line.startswith("#"):
                    key, value = map(str.strip, line.split("=", 1))
                    os.environ[key] = value
    except FileNotFoundError:
        raise FileNotFoundError(f"{env_file} file not found. Please ensure it exists in the script directory.")
    
def get_moving_avg():
    # Fetch stock info
    try:
        moving_avg_days = NUM_MA_DAYS
        ticker1 = '^GSPC' # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        ticker2 = '^NDX' 
        period = '2y'
        indx1 = yf.Ticker(ticker1) # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        indx2 = yf.Ticker(ticker2) # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        indx1_data = indx1.history(period = period) # Index data to track, '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        indx2_data = indx2.history(period = period) # Index data to track
        indx1_data['MA'] = indx1_data['Close'].rolling(window=moving_avg_days).mean()
        indx2_data['MA'] = indx2_data['Close'].rolling(window=moving_avg_days).mean()

        moving_avg_msg1 = ""
        moving_avg_msg2 = ""

    # IS BELOW
        if indx1_data['Close'].iloc[-1] < indx1_data['MA'].iloc[-1]:
            moving_avg_msg1 = "S&P500 IS TRADING BELOW " + str(moving_avg_days) +" DAY MOVING AVERAGE."
        if indx2_data['Close'].iloc[-1] < indx2_data['MA'].iloc[-1]:
            moving_avg_msg2 = "NASDAQ IS TRADING BELOW " + str(moving_avg_days) +" DAY MOVING AVERAGE."
        moving_avg_msg = moving_avg_msg1 + "\n" + moving_avg_msg2 + "\n"
    # IS ABOVE
        if indx1_data['Close'].iloc[-1] > indx1_data['MA'].iloc[-1]:
            moving_avg_msg1 = "S&P500 IS TRADING ABOVE " + str(moving_avg_days) +" DAY MOVING AVERAGE."
        if indx2_data['Close'].iloc[-1] > indx2_data['MA'].iloc[-1]:
            moving_avg_msg2 = "NASDAQ IS TRADING ABOVE " + str(moving_avg_days) +" DAY MOVING AVERAGE."
        moving_avg_msg = moving_avg_msg1 + "\n" + moving_avg_msg2 + "\n"
        return moving_avg_msg
    
    except Exception as e:
        return f"Stock information is currently unavailable. Error: {e}"

def send_email(
    sender, recipient, subject, message_body, smtp_server, smtp_port, password
):
    """Send an email using the specified SMTP server and login credentials."""
    try:
        email = EmailMessage()
        email["From"] = sender
        email["To"] = recipient
        email["Subject"] = subject
        email.set_content(message_body)
        

        with smtplib.SMTP(smtp_server, port=smtp_port) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(email)
        return "Email sent successfully."
    except Exception as e:
        return f"Failed to send email. Error: {e}"

def main():
    load_environment_variables()

    # Retrieve sensitive data
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    Moving_avg_message = get_moving_avg()

    # Create the email body with separated sections
    message_body = (
        "Good morning! Here's your update:\n\n"
        "---- MOVING AVERAGE REPORT ----\n\n"
        f"{Moving_avg_message}\n"
    )

    # Send the email to the sender
    email_status = send_email(
        sender=sender,
        recipient=sender,  # sending email to myself
        subject="Morning Market Update 🚀",
        message_body=message_body,
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        password=password,
    )
    print(email_status)

if __name__ == "__main__":
    main()