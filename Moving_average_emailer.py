#!/usr/bin/env python3
# remove this command when running as a taks on PythonAnywhere
import os
import smtplib
from email.message import EmailMessage
import yfinance as yf # pip install yfinance
from datetime import datetime
from ta.momentum import RSIIndicator

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

def moving_avg_status(ticker1, period, moving_avg_days):
    # Fetch stock info
    try:
        indx1 = yf.Ticker(ticker1) # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
        indx1_data = indx1.history(period = period) # Index data to track, '1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y', '10y', 'ytd', 'max'
        indx1_data['MA'] = indx1_data['Close'].rolling(window=moving_avg_days).mean()
        ticker_above = indx1_data['Close'].iloc[-1] > indx1_data['MA'].iloc[-1]
        ticker_above_y = indx1_data['Close'].iloc[-2] > indx1_data['MA'].iloc[-2]
        return ticker_above, ticker_above_y
    #ticker above can be compared to ticker above y to check for a crossover.
        
    except Exception as e:
        print(f"Error in moving_avg_status: {e}")
        return None, None, None, None

def RSI_status(RSI_ticker):
    RSI_data = yf.download(tickers=RSI_ticker, period='5d', interval='5m', auto_adjust=True, progress=False)
    closeValues = RSI_data['Close'].squeeze()
    rsi_14 = RSIIndicator(close=closeValues, window=14) # window = num days for RSI
    RSI_series = rsi_14.rsi()
    RSI_day = RSI_series.iloc[-1]
    return RSI_day

def get_MA_RSI_status(tickers, period, moving_avg_days):
    tickers_statuses = []
    RSI_statuses = []
    for ticker in tickers:
        tickers_statuses.append(moving_avg_status(ticker, period, moving_avg_days))
        RSI_statuses.append(RSI_status(ticker))
    return tickers_statuses, RSI_statuses

def build_email_body(email, table, tickers, tickers_statuses, RSI_statuses):
    email.set_content(
        "Good morning! Here's your update:\n\n"
        f"--- {NUM_MA_DAYS} DAY MOVING AVG & RSI REPORT ---\n\n"
        f"\n{table}"
    ) #plain text for if HTML is not supported

    html_table = "".join(
        f"<tr><td>{ticker}</td><td>{'ABOVE' if ma[0] else 'BELOW'}</td><td>{rsi:.2f}</td></tr>"
        for ticker, ma, rsi in zip(tickers, tickers_statuses, RSI_statuses)
    )

    html = f"""
    <html>
    <body>
        <h2>Morning Market Update 📈</h2>
        <p><b>{NUM_MA_DAYS}-Day Moving Average & RSI Report</b></p>
        <table border="1" cellpadding="6" cellspacing="0">
        <tr>
            <th>Ticker</th><th>MA Status</th><th>RSI</th>
        </tr>
        {html_table}
        </table>
    </body>
    </html>
    """
    email.add_alternative(html, subtype='html')
    return

def send_email(
    email, sender, recipient, subject, smtp_server, smtp_port, password
):
    """Send an email using the specified SMTP server and login credentials."""
    try:
        email = email
        email["From"] = sender
        email["To"] = recipient
        email["Subject"] = subject   

        with smtplib.SMTP(smtp_server, port=smtp_port) as smtp:
            smtp.starttls()
            smtp.login(sender, password)
            smtp.send_message(email)
        return "Email sent successfully."
    except Exception as e:
        print(f"Failed to send HTML email. Error: {e}")
        print("Retrying with plain text only...")

        # Rebuild plain-text-only email
        fallback_email = EmailMessage()
        fallback_email["From"] = sender
        fallback_email["To"] = recipient
        fallback_email["Subject"] = subject
        fallback_email.set_content(email.get_body(preferencelist=('plain')).get_content())

        try:
            with smtplib.SMTP(smtp_server, port=smtp_port) as smtp:
                smtp.starttls()
                smtp.login(sender, password)
                smtp.send_message(fallback_email)
            return "Plain text fallback email sent successfully."
        except Exception as e2:
            return f"Failed to send even fallback plain-text email. Error: {e2}"
    
def create_table(tickers, ma_statuses, rsi_values):
    # Define header with column widths
    header = f"{'Ticker':<8} | {'MA Status':<9} | {'RSI':<6}\n"
    separator = "-" * (8 + 3 + 9 + 3 + 6 +4) + "\n"  # length matches header
    table_str = header + separator    
    for i, ticker in enumerate(tickers):
        ma_stat = "ABOVE" if ma_statuses[i][0] else "BELOW"
        rsi_val = rsi_values[i]
        table_str += f"{ticker:<8} | {ma_stat:<9} | {rsi_val:5.2f}\n"
    return table_str

def main():
    load_environment_variables()
    today = datetime.now().weekday()
    if (today == 5 or today == 6): 
        return # market info not needed on weekends
    tickers = ('^GSPC', '^NDX', '^DJI', '^DJT', 'AAPL', 'AMZN', 'GOOG', 'MSFT', 'NVDA', 'TSLA', 'BTC-CAD') # ^GSPC = S&P500, ^NDX = NASDAQ, ^DJI = Dow Jones
    period = '2y'
    moving_avg_days = NUM_MA_DAYS
    # Retrieve sensitive data
    sender = os.getenv("EMAIL_SENDER")
    password = os.getenv("EMAIL_PASSWORD")
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    email = EmailMessage()
    tickers_statuses, RSI_statuses = get_MA_RSI_status(tickers, period, moving_avg_days)
    table = create_table(tickers, tickers_statuses, RSI_statuses)
    build_email_body(email, table, tickers, tickers_statuses, RSI_statuses)
    email_status = send_email(
        email=email,
        sender=sender,
        recipient=sender,  # sending email to myself
        subject="Morning Market Update 🚀",
        smtp_server=SMTP_SERVER,
        smtp_port=SMTP_PORT,
        password=password,
    )
    print(email_status)

    # print(email)

if __name__ == "__main__":

    main()
