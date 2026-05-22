from __future__ import annotations

import requests
from app.config import Settings

class EmailService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_url = "https://api.brevo.com/v3/smtp/email"

    def send_verification_email(self, to_email: str, user_name: str | None = None):
        if not self.settings.brevo_api_key:
            print("Brevo API key not configured. Skipping email.")
            return False

        payload = {
            "sender": {
                "name": self.settings.sender_name,
                "email": self.settings.sender_email
            },
            "to": [
                {
                    "email": to_email,
                    "name": user_name or to_email
                }
            ],
            "subject": "Welcome to MythoStack - Verify your account",
            "htmlContent": f"""
                <html>
                <body style="font-family: sans-serif; background-color: #0C0B1A; color: #ffffff; padding: 40px;">
                    <h1 style="color: #F5B042;">Welcome to MythoStack</h1>
                    <p>Thanks for joining the waitlist! We're excited to help you build a marketing engine that compounds.</p>
                    <p>To get started with your 7-day free trial, please verify your email address by clicking the button below:</p>
                    <div style="margin: 40px 0;">
                        <a href="https://mythostack.com/login" style="background-color: #F5B042; color: #0C0B1A; padding: 12px 24px; border-radius: 8px; text-decoration: none; font-weight: bold;">Verify Account</a>
                    </div>
                    <p style="color: #8E8EA0; font-size: 12px;">If you didn't sign up for MythoStack, you can safely ignore this email.</p>
                    <hr style="border: 0; border-top: 1px solid #1F1740; margin: 40px 0;">
                    <p style="color: #8E8EA0; font-size: 12px;">Ayman from MythoStack<br>ayman@mythostack.com</p>
                </body>
                </html>
            """
        }

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "api-key": self.settings.brevo_api_key
        }

        try:
            response = requests.post(self.api_url, json=payload, headers=headers)
            response.raise_for_status()
            return True
        except Exception as e:
            print(f"Failed to send Brevo email: {e}")
            return False
