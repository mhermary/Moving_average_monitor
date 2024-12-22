#!/usr/bin/env python3
import os
import smtplib
from email.message import EmailMessage
import yfinance as yf # pip isntall yfinance
from datetime import datetime


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

def moving_avg_status(ticker1, ticker2, period, moving_avg_days):
    # Fetch stock info
    try:
        indx1 = yf.Ticker(ticker1) # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        indx2 = yf.Ticker(ticker2) # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        indx1_data = indx1.history(period = period) # Index data to track, '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        indx2_data = indx2.history(period = period) # Index data to track
        indx1_data['MA'] = indx1_data['Close'].rolling(window=moving_avg_days).mean()
        indx2_data['MA'] = indx2_data['Close'].rolling(window=moving_avg_days).mean()
        spy_above = indx1_data['Close'].iloc[-1] > indx1_data['MA'].iloc[-1]
        ndx_above = indx2_data['Close'].iloc[-1] > indx2_data['MA'].iloc[-1]
        spy_above_y = indx1_data['Close'].iloc[-2] > indx1_data['MA'].iloc[-2]
        ndx_above_y = indx2_data['Close'].iloc[-2] > indx2_data['MA'].iloc[-2]
        return spy_above, ndx_above, spy_above_y, ndx_above_y
        
    except Exception as e:
        print(f"Error in moving_avg_status: {e}")
        return None, None, None, None

def create_msg(spy, ndx):
    try:
        if spy is None or ndx is None:
             raise ValueError("Invalid input: None Type detected where boolean was expected.")
        msg = ''
        spy_stat = 'ABOVE' if spy else 'BELOW'
        ndx_stat = 'ABOVE' if ndx else 'BELOW'
        msg = "S&P500 IS TRADING " + spy_stat + ' ' + str(NUM_MA_DAYS) +" DAY MOVING AVERAGE. \n" + "NASDAQ IS TRADING " + ndx_stat + ' ' + str(NUM_MA_DAYS) +" DAY MOVING AVERAGE.\n"
        return msg
    except ValueError as e:
        print(f"Error in create_msg: {e}")
        return f"Error in create_msg: {e}"

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
    ticker1 = '^GSPC' # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
    ticker2 = '^NDX' 
    period = '2y'
    moving_avg_days = NUM_MA_DAYS
    
    # Retrieve sensitive data
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    SPY_status, NDX_status, SPY_stat_y, NDX_stat_y = moving_avg_status(ticker1, ticker2, period, moving_avg_days)
    today = datetime.now().weekday() # Check if saturday for check-in
    if SPY_status != SPY_stat_y or NDX_status != NDX_stat_y:
        moving_avg_message = create_msg(SPY_status, NDX_status)
        if (today == 5): 
            moving_avg_message = "Saturday check in, everything is still connected. \n" + moving_avg_message
    else: 
        print("No change in moving average side, terminating program")
        return

    # Create the email body with separated sections
    message_body = (
        "Good morning! Here's your update:\n\n"
        "---- MOVING AVERAGE REPORT ----\n\n"
        f"{moving_avg_message}\n"
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