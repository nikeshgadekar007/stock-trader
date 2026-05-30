"""
Notifications Module
Send alerts via Email, Telegram, or Windows Toast
"""

import smtplib
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import config

def send_telegram_message(message: str) -> bool:
    """Send message via Telegram bot"""
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("Telegram not configured. Skipping notification.")
        return False
    
    try:
        import requests
        url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': config.TELEGRAM_CHAT_ID,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data)
        return response.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}")
        return False

def send_email(subject: str, body: str) -> bool:
    """Send email via Gmail SMTP"""
    if not config.NOTIFICATION_EMAIL:
        print("Email not configured. Skipping notification.")
        return False
    
    try:
        # Gmail SMTP settings - read from environment variable
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = config.NOTIFICATION_EMAIL
        sender_password = os.environ.get('GMAIL_APP_PASSWORD', '')
        
        if not sender_password:
            print("GMAIL_APP_PASSWORD not set. Email not sent.")
            print("To enable email:")
            print("1. Go to https://myaccount.google.com/security")
            print("2. Enable 2-Factor Authentication")
            print("3. Create App Password (App type: Mail)")
            print("4. Set environment variable: set GMAIL_APP_PASSWORD=your_password")
            return False
        
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = sender_email
        msg['Subject'] = subject
        
        msg.attach(MIMEText(body, 'html'))
        
        # Connect to SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, sender_email, msg.as_string())
        server.quit()
        
        print(f"Email sent: {subject}")
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False

def send_windows_toast(title: str, message: str) -> bool:
    """Send Windows toast notification"""
    if not config.ENABLE_TOAST_NOTIFICATIONS:
        return False
    
    try:
        from winotify import Notification, audio
        toast = Notification(
            app_id="Stock Trader",
            title=title,
            msg=message,
            duration="long"
        )
        toast.show()
        return True
    except ImportError:
        # Fallback to simple print
        print(f"[TOAST] {title}: {message}")
        return True
    except Exception as e:
        print(f"Toast error: {e}")
        return False

def send_trade_alert(symbol: str, action: str, price: float, 
                     target: float, stop: float, confidence: float) -> None:
    """Send trade alert notification"""
    emoji = "📈" if action == "BUY" else "📉"
    message = f"""
{emoji} <b>{action} Signal: {symbol}</b>

💰 Price: ${price:.2f}
🎯 Target: ${target:.2f}
🛡️ Stop: ${stop:.2f}
📊 Confidence: {confidence:.0%}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    # Send to all enabled channels
    if config.ENABLE_TELEGRAM_NOTIFICATIONS:
        send_telegram_message(message)
    
    if config.ENABLE_EMAIL_NOTIFICATIONS:
        send_email(f"{action} Signal: {symbol}", message)
    
    if config.ENABLE_TOAST_NOTIFICATIONS:
        send_windows_toast(f"{action} {symbol}", f"${price:.2f} | Target: ${target:.2f}")

def send_market_update(signals: list) -> None:
    """Send market update notification"""
    buy_count = len([s for s in signals if s.get('action') == 'BUY'])
    sell_count = len([s for s in signals if s.get('action') == 'SELL'])
    
    message = f"""
📊 <b>Market Scan Complete</b>

📈 BUY Signals: {buy_count}
📉 SELL Signals: {sell_count}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if config.ENABLE_TELEGRAM_NOTIFICATIONS:
        send_telegram_message(message)
    
    if config.ENABLE_TOAST_NOTIFICATIONS:
        send_windows_toast("Market Scan", f"BUY: {buy_count} | SELL: {sell_count}")

def send_daily_summary(trades: list, pnl: float) -> None:
    """Send end of day summary"""
    total_trades = len(trades)
    winning_trades = len([t for t in trades if t.get('pnl', 0) > 0])
    
    message = f"""
📋 <b>Daily Trading Summary</b>

📊 Total Trades: {total_trades}
✅ Winners: {winning_trades}
❌ Losers: {total_trades - winning_trades}
💰 P&L: ${pnl:.2f}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    if config.ENABLE_TELEGRAM_NOTIFICATIONS:
        send_telegram_message(message)
    
    if config.ENABLE_EMAIL_NOTIFICATIONS:
        send_email("Daily Trading Summary", message)
    
    if config.ENABLE_TOAST_NOTIFICATIONS:
        send_windows_toast("Daily Summary", f"P&L: ${pnl:.2f}")

def send_error_alert(error_message: str) -> None:
    """Send error alert"""
    message = f"⚠️ <b>Trading System Error</b>\n\n{error_message}"
    
    if config.ENABLE_TELEGRAM_NOTIFICATIONS:
        send_telegram_message(message)
    
    if config.ENABLE_TOAST_NOTIFICATIONS:
        send_windows_toast("System Error", error_message)


class NotificationService:
    """Centralized notification service for the trading system"""
    
    def __init__(self):
        self.telegram_enabled = config.ENABLE_TELEGRAM_NOTIFICATIONS
        self.email_enabled = config.ENABLE_EMAIL_NOTIFICATIONS
        self.toast_enabled = config.ENABLE_TOAST_NOTIFICATIONS
    
    def send_trade_alert(self, message: str) -> None:
        """Send trade alert message"""
        if self.telegram_enabled:
            send_telegram_message(message)
        if self.email_enabled:
            send_email("Trade Alert", message)
        if self.toast_enabled:
            send_windows_toast("Trade Alert", message[:100])
    
    def send_daily_report(self, report: dict) -> None:
        """Send daily report"""
        message = f"""
📋 <b>Daily Trading Report</b>

📊 Total Trades: {report.get('total_trades', 0)}
✅ Winners: {report.get('winners', 0)}
❌ Losers: {report.get('losers', 0)}
💰 P&L: ${report.get('pnl', 0):.2f}
📈 Win Rate: {report.get('win_rate', 0):.1%}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        if self.telegram_enabled:
            send_telegram_message(message)
        if self.email_enabled:
            send_email("Daily Trading Report", message)
        if self.toast_enabled:
            send_windows_toast("Daily Report", f"P&L: ${report.get('pnl', 0):.2f}")
    
    def send_signal_alert(self, symbol: str, action: str, price: float, 
                         target: float, stop: float, confidence: float) -> None:
        """Send signal alert"""
        emoji = "📈" if action == "BUY" else "📉"
        message = f"""
{emoji} <b>{action} Signal: {symbol}</b>

💰 Price: ${price:.2f}
🎯 Target: ${target:.2f}
🛡️ Stop: ${stop:.2f}
📊 Confidence: {confidence:.0%}

Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        self.send_trade_alert(message)


# Test function
def test_notifications():
    """Test all notification channels"""
    print("Testing notifications...")
    
    print("\n1. Testing Windows Toast...")
    send_windows_toast("Test Alert", "This is a test notification!")
    
    print("\n2. Testing Telegram...")
    if config.TELEGRAM_BOT_TOKEN:
        send_telegram_message("🧪 <b>Test Message</b>\n\nTrading system is online!")
    else:
        print("Telegram not configured. Add your bot token to config.py")
    
    print("\n3. Testing Email...")
    if config.NOTIFICATION_EMAIL:
        send_email("Test Subject", "This is a test email!")
    else:
        print("Email not configured. Add your email to config.py")
    
    print("\n✅ Notification test complete!")

if __name__ == "__main__":
    test_notifications()