import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List, Dict, Any
from app.core.config import settings

logger = logging.getLogger("agri_smart.email_service")


class EmailService:
    """
    Production Email Notification Service.
    Dispatches styled HTML and plain-text notifications for user onboarding, order invoices,
    payment confirmations, and delivery tracking.
    """

    @staticmethod
    def _send_smtp(to_email: str, subject: str, html_content: str, text_content: Optional[str] = None) -> bool:
        """Internal SMTP sender with simulation fallback."""
        if not settings.EMAIL_ENABLED or not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.info(
                "[EMAIL SIMULATED] To: %s | Subject: %s | (Enable EMAIL_ENABLED=true and set SMTP credentials to send live)",
                to_email,
                subject
            )
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            msg["To"] = to_email

            if text_content:
                msg.attach(MIMEText(text_content, "plain", "utf-8"))
            msg.attach(MIMEText(html_content, "html", "utf-8"))

            if settings.SMTP_SSL:
                server = smtplib.SMTP_SSL(settings.SMTP_HOST, settings.SMTP_PORT)
            else:
                server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT)
                if settings.SMTP_TLS:
                    server.starttls()

            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_FROM_EMAIL, [to_email], msg.as_string())
            server.quit()

            logger.info("Email successfully sent to %s with subject: %s", to_email, subject)
            return True
        except Exception as exc:
            logger.error("Failed to send email to %s: %s", to_email, exc, exc_info=True)
            return False

    @classmethod
    def send_welcome_email(cls, to_email: str, user_name: str, role: str) -> bool:
        subject = f"Welcome to Agri-Smart Ecosystem, {user_name}!"
        html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 24px;">
                <h1 style="color: #16a34a; margin: 0;">🌱 Agri-Smart Ecosystem</h1>
                <p style="color: #64748b; font-size: 14px; margin-top: 4px;">Smart Agriculture Management & Direct Marketplace</p>
            </div>
            <div style="padding: 20px; background-color: #f8fafc; border-radius: 6px;">
                <h2 style="color: #1e293b; margin-top: 0;">Welcome, {user_name}!</h2>
                <p style="color: #475569; line-height: 1.6;">Your account has been successfully created with the role of <strong>{role}</strong>.</p>
                <p style="color: #475569; line-height: 1.6;">You can now access farm management tools, precision cultivation stages, produce listings, and atomic checkout.</p>
                <div style="text-align: center; margin: 25px 0;">
                    <a href="{settings.FRONTEND_URL}/login" style="background-color: #16a34a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Go to Dashboard</a>
                </div>
            </div>
            <div style="margin-top: 24px; text-align: center; color: #94a3b8; font-size: 12px;">
                <p>© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = f"Welcome to Agri-Smart Ecosystem, {user_name}! Your {role} account is now ready. Visit: {settings.FRONTEND_URL}/login"
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_order_confirmation_email(
        cls,
        to_email: str,
        customer_name: str,
        order_number: str,
        total_amount: str,
        items: List[Dict[str, Any]],
        delivery_address: str,
    ) -> bool:
        subject = f"Order Confirmed: {order_number} — Agri-Smart"
        
        items_html = "".join([
            f"""<tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; color: #334155;">{item.get('name', 'Item')}</td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: center; color: #334155;">{item.get('quantity', 1)}</td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #e2e8f0; text-align: right; color: #334155;">₹{item.get('subtotal', '0.00')}</td>
            </tr>"""
            for item in items
        ])

        html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #16a34a; margin: 0;">🌱 Agri-Smart Marketplace</h1>
                <p style="color: #64748b; font-size: 14px;">Order & Invoice Confirmation</p>
            </div>
            <div style="padding: 16px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #15803d; margin: 0 0 8px 0;">✓ Order Placed Successfully</h3>
                <p style="color: #166534; margin: 0; font-size: 14px;">Order Number: <strong>{order_number}</strong></p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <thead>
                    <tr style="background-color: #f8fafc;">
                        <th style="padding: 8px 12px; text-align: left; color: #475569; font-size: 13px; border-bottom: 2px solid #cbd5e1;">Item Description</th>
                        <th style="padding: 8px 12px; text-align: center; color: #475569; font-size: 13px; border-bottom: 2px solid #cbd5e1;">Qty</th>
                        <th style="padding: 8px 12px; text-align: right; color: #475569; font-size: 13px; border-bottom: 2px solid #cbd5e1;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                </tbody>
                <tfoot>
                    <tr>
                        <td colspan="2" style="padding: 12px; text-align: right; font-weight: bold; color: #1e293b;">Total Invoice Amount:</td>
                        <td style="padding: 12px; text-align: right; font-weight: bold; color: #16a34a; font-size: 16px;">₹{total_amount}</td>
                    </tr>
                </tfoot>
            </table>
            <div style="padding: 12px; background-color: #f8fafc; border-radius: 6px; margin-bottom: 20px;">
                <strong style="color: #334155; font-size: 13px;">Delivery Destination:</strong>
                <p style="color: #64748b; margin: 4px 0 0 0; font-size: 13px;">{delivery_address}</p>
            </div>
            <div style="text-align: center; margin: 20px 0;">
                <a href="{settings.FRONTEND_URL}/orders" style="background-color: #16a34a; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">View Order & Tracking</a>
            </div>
        </div>
        """
        text = f"Order {order_number} placed successfully. Total Amount: ₹{total_amount}. Track order at {settings.FRONTEND_URL}/orders"
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_payment_receipt_email(
        cls,
        to_email: str,
        customer_name: str,
        order_number: str,
        payment_number: str,
        amount: str,
        payment_method: str,
        transaction_ref: Optional[str] = None,
    ) -> bool:
        subject = f"Payment Receipt: {payment_number} for Order {order_number}"
        html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #16a34a; margin: 0;">🌱 Payment Settled</h1>
                <p style="color: #64748b; font-size: 14px;">Official Digital Payment Receipt</p>
            </div>
            <div style="padding: 16px; background-color: #f0fdf4; border-radius: 6px; margin-bottom: 20px;">
                <p style="margin: 4px 0; color: #334155;"><strong>Payment Number:</strong> {payment_number}</p>
                <p style="margin: 4px 0; color: #334155;"><strong>Order Number:</strong> {order_number}</p>
                <p style="margin: 4px 0; color: #334155;"><strong>Amount Paid:</strong> <span style="color: #16a34a; font-size: 16px; font-weight: bold;">₹{amount}</span></p>
                <p style="margin: 4px 0; color: #334155;"><strong>Payment Method:</strong> {payment_method}</p>
                {f'<p style="margin: 4px 0; color: #334155;"><strong>Transaction Ref:</strong> {transaction_ref}</p>' if transaction_ref else ''}
                <p style="margin: 4px 0; color: #334155;"><strong>Status:</strong> <span style="background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 4px; font-weight: bold;">PAID</span></p>
            </div>
            <p style="color: #64748b; font-size: 13px; text-align: center;">Thank you for your transaction with Agri-Smart Ecosystem.</p>
        </div>
        """
        text = f"Payment Receipt {payment_number} for Order {order_number}. Amount: ₹{amount}. Status: PAID."
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_delivery_dispatch_email(
        cls,
        to_email: str,
        customer_name: str,
        order_number: str,
        driver_name: str,
        driver_phone: str,
        vehicle_number: Optional[str] = None,
    ) -> bool:
        subject = f"Your Order {order_number} is Out for Delivery!"
        html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #2563eb; margin: 0;">🚚 Out for Delivery</h1>
                <p style="color: #64748b; font-size: 14px;">Your order has been dispatched from the farm</p>
            </div>
            <div style="padding: 16px; background-color: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #1e40af; margin-top: 0;">Driver & Vehicle Details</h3>
                <p style="color: #1e3a8a; margin: 4px 0;"><strong>Driver Name:</strong> {driver_name}</p>
                <p style="color: #1e3a8a; margin: 4px 0;"><strong>Contact Number:</strong> {driver_phone}</p>
                {f'<p style="color: #1e3a8a; margin: 4px 0;"><strong>Vehicle Number:</strong> {vehicle_number}</p>' if vehicle_number else ''}
            </div>
            <div style="text-align: center; margin: 20px 0;">
                <a href="{settings.FRONTEND_URL}/orders" style="background-color: #2563eb; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">Track Live Dispatch</a>
            </div>
        </div>
        """
        text = f"Order {order_number} is out for delivery! Driver: {driver_name} ({driver_phone})."
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_harvest_yield_email(
        cls,
        to_email: str,
        customer_name: str,
        farmer_name: str,
        crop_name: str,
        crop_name_local: Optional[str],
        yield_quantity: str,
        yield_unit: str,
        price_per_unit: str,
        farm_location: Optional[str] = None,
        farm_name: Optional[str] = None,
    ) -> bool:
        display_crop = f"{crop_name} ({crop_name_local})" if crop_name_local else crop_name
        subject = f"🌾 Fresh Harvest Alert: {display_crop} available now from {farmer_name}!"
        html = f"""
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #e2e8f0; border-radius: 8px; background-color: #ffffff;">
            <div style="text-align: center; margin-bottom: 20px;">
                <h1 style="color: #15803d; margin: 0;">🌾 Fresh Harvest Available</h1>
                <p style="color: #64748b; font-size: 14px;">Direct Farm-to-Buyer Procurement Alert</p>
            </div>
            <div style="padding: 16px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 6px; margin-bottom: 20px;">
                <h3 style="color: #166534; margin: 0 0 6px 0;">New Yield Recorded & Ready for Order</h3>
                <p style="color: #15803d; margin: 0; font-size: 14px;">
                    Farmer <strong>{farmer_name}</strong> has just harvested fresh <strong>{display_crop}</strong>!
                </p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tbody>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Crop / Produce</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #1e293b; font-size: 14px;">{display_crop}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Available Harvest Yield</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #16a34a; font-size: 14px;">{yield_quantity} {yield_unit}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Direct Mandi Price</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #b45309; font-size: 14px;">₹{price_per_unit} per {yield_unit}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #e2e8f0;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Farm Origin</td>
                        <td style="padding: 8px 12px; color: #334155; font-size: 13px;">{farm_name or 'Verified Farm'}, {farm_location or 'Tamil Nadu'}</td>
                    </tr>
                </tbody>
            </table>
            <div style="text-align: center; margin: 25px 0;">
                <a href="{settings.FRONTEND_URL}/marketplace/produce" style="background-color: #16a34a; color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 6px; font-weight: 600; display: inline-block;">
                    View Produce & Procure Directly
                </a>
            </div>
            <div style="margin-top: 24px; text-align: center; color: #94a3b8; font-size: 12px;">
                <p>You received this alert because you are subscribed to fresh farm harvest notifications on Agri-Smart.</p>
                <p>© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = (
            f"Fresh Harvest Alert: Farmer {farmer_name} has just harvested {yield_quantity} {yield_unit} of "
            f"{display_crop} at ₹{price_per_unit}/{yield_unit}. Procure directly at {settings.FRONTEND_URL}/marketplace/produce"
        )
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_otp_email(
        cls,
        to_email: str,
        user_name: str,
        otp_code: str,
        purpose: str = "Two-Factor Verification",
        expiry_minutes: int = 10,
    ) -> bool:
        """
        Dispatches high-security One-Time Password (OTP) verification email.
        """
        subject = f"Your Agri-Smart Security Code: {otp_code}"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; color: #1e293b;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="display: inline-block; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; background: linear-gradient(135deg, #10b981, #059669); color: white; font-size: 24px; margin-bottom: 8px;">🛡️</div>
                <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700;">{purpose}</h2>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Agri-Smart Ecosystem Identity Protection</p>
            </div>
            <div style="padding: 24px; background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%); border-radius: 8px; border: 1px solid #e2e8f0; text-align: center;">
                <p style="margin-top: 0; color: #475569; font-size: 14px;">Hello <strong>{user_name}</strong>,</p>
                <p style="color: #475569; font-size: 14px; margin-bottom: 20px;">Use the following verification code to proceed with your request. This code will expire in <strong>{expiry_minutes} minutes</strong>.</p>
                <div style="display: inline-block; padding: 12px 28px; background-color: #0f172a; color: #10b981; font-family: 'Courier New', Courier, monospace; font-size: 32px; font-weight: 800; letter-spacing: 6px; border-radius: 8px; border: 1px solid #334155; margin-bottom: 12px;">
                    {otp_code}
                </div>
                <p style="margin: 12px 0 0 0; color: #94a3b8; font-size: 12px;">Never share this code with anyone, including Agri-Smart representatives.</p>
            </div>
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #f1f5f9; text-align: center; color: #94a3b8; font-size: 12px;">
                <p style="margin: 0;">If you did not initiate this request, please change your password immediately.</p>
                <p style="margin: 4px 0 0 0;">© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = f"Hello {user_name}, your Agri-Smart verification code for {purpose} is: {otp_code}. Valid for {expiry_minutes} minutes. Do not share this code."
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_password_reset_email(
        cls,
        to_email: str,
        user_name: str,
        otp_code: str,
        reset_url: Optional[str] = None,
        expiry_minutes: int = 15,
    ) -> bool:
        """
        Dispatches password reset email with OTP code and direct reset button link.
        """
        subject = "Reset Your Agri-Smart Password"
        direct_link = reset_url or f"{settings.FRONTEND_URL}/reset-password"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; color: #1e293b;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="display: inline-block; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; background: linear-gradient(135deg, #3b82f6, #1d4ed8); color: white; font-size: 24px; margin-bottom: 8px;">🔑</div>
                <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700;">Password Reset Request</h2>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Agri-Smart Ecosystem Security</p>
            </div>
            <div style="padding: 24px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">
                <p style="margin-top: 0; color: #475569; font-size: 14px;">Hello <strong>{user_name}</strong>,</p>
                <p style="color: #475569; font-size: 14px; line-height: 1.5;">We received a request to reset your password. You can reset your password using the verification OTP code below or by clicking the button.</p>
                <div style="text-align: center; margin: 20px 0;">
                    <div style="display: inline-block; padding: 10px 24px; background-color: #0f172a; color: #38bdf8; font-family: 'Courier New', Courier, monospace; font-size: 28px; font-weight: 800; letter-spacing: 5px; border-radius: 8px; border: 1px solid #334155;">
                        {otp_code}
                    </div>
                </div>
                <div style="text-align: center; margin: 20px 0;">
                    <a href="{direct_link}" style="background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; font-size: 14px;">
                        Reset My Password
                    </a>
                </div>
                <p style="margin: 0; color: #64748b; font-size: 12px; text-align: center;">This code will expire in <strong>{expiry_minutes} minutes</strong>.</p>
            </div>
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #f1f5f9; text-align: center; color: #94a3b8; font-size: 12px;">
                <p style="margin: 0;">If you didn't request a password reset, you can safely ignore this email.</p>
                <p style="margin: 4px 0 0 0;">© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = f"Hello {user_name}, your password reset verification code is: {otp_code} (Valid for {expiry_minutes} minutes). Or visit: {direct_link}"
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_password_changed_email(
        cls,
        to_email: str,
        user_name: str,
    ) -> bool:
        """
        Dispatches security advisory alert when user password is changed.
        """
        subject = "Security Alert: Agri-Smart Password Changed"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; color: #1e293b;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="display: inline-block; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; background: linear-gradient(135deg, #10b981, #059669); color: white; font-size: 24px; margin-bottom: 8px;">🔒</div>
                <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700;">Password Updated Successfully</h2>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Agri-Smart Account Security</p>
            </div>
            <div style="padding: 20px; background: #f0fdf4; border-radius: 8px; border: 1px solid #bbf7d0;">
                <p style="margin-top: 0; color: #166534; font-size: 14px;">Hello <strong>{user_name}</strong>,</p>
                <p style="color: #166534; font-size: 14px; margin-bottom: 0;">Your Agri-Smart account password has just been changed. All previous active browser sessions have been logged out for your protection.</p>
            </div>
            <div style="margin-top: 24px; padding-top: 16px; border-top: 1px solid #f1f5f9; text-align: center; color: #94a3b8; font-size: 12px;">
                <p style="margin: 0;">If you did not make this change, contact support immediately at support@agrismart.local</p>
                <p style="margin: 4px 0 0 0;">© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = f"Hello {user_name}, your Agri-Smart account password was successfully updated. If you did not make this change, please contact support immediately."
        return cls._send_smtp(to_email, subject, html, text)

    @classmethod
    def send_subscription_active_email(
        cls,
        to_email: str,
        user_name: str,
        plan_type: str,
        end_date_str: str,
        amount_paid: str,
        payment_reference: str,
    ) -> bool:
        """
        Dispatches subscription activation confirmation.
        """
        subject = f"🌟 Subscription Activated: Agri-Smart {plan_type.capitalize()} Pass"
        html = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 560px; margin: 0 auto; padding: 24px; border: 1px solid #e2e8f0; border-radius: 12px; background-color: #ffffff; color: #1e293b;">
            <div style="text-align: center; margin-bottom: 24px;">
                <div style="display: inline-block; width: 48px; height: 48px; line-height: 48px; border-radius: 12px; background: linear-gradient(135deg, #f59e0b, #d97706); color: white; font-size: 24px; margin-bottom: 8px;">🌟</div>
                <h2 style="margin: 0; color: #0f172a; font-size: 20px; font-weight: 700;">Historical Archive & Pass Activated</h2>
                <p style="margin: 4px 0 0 0; color: #64748b; font-size: 13px;">Agri-Smart Pro Subscription</p>
            </div>
            <div style="padding: 20px; background: #fffbeb; border-radius: 8px; border: 1px solid #fde68a; margin-bottom: 20px;">
                <p style="margin-top: 0; color: #92400e; font-size: 14px;">Hello <strong>{user_name}</strong>,</p>
                <p style="color: #92400e; font-size: 14px; margin-bottom: 0;">Thank you for subscribing! Your <strong>{plan_type}</strong> plan is now active. You have full access to multi-year cultivation records, worker ledgers, and unlimited exports.</p>
            </div>
            <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
                <tbody>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Plan Type</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #0f172a; font-size: 13px;">{plan_type} Pass</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Amount Paid</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #10b981; font-size: 13px;">₹{amount_paid}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Valid Until</td>
                        <td style="padding: 8px 12px; font-weight: bold; color: #0f172a; font-size: 13px;">{end_date_str}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; color: #64748b; font-size: 13px;">Payment Reference</td>
                        <td style="padding: 8px 12px; color: #475569; font-size: 13px; font-family: monospace;">{payment_reference}</td>
                    </tr>
                </tbody>
            </table>
            <div style="text-align: center; margin: 20px 0;">
                <a href="{settings.FRONTEND_URL}/farmer/reports" style="background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; padding: 12px 24px; text-decoration: none; border-radius: 8px; font-weight: 600; display: inline-block; font-size: 14px;">
                    Access Historical Archives
                </a>
            </div>
            <div style="margin-top: 24px; text-align: center; color: #94a3b8; font-size: 12px;">
                <p>© 2026 Agri-Smart Ecosystem. All rights reserved.</p>
            </div>
        </div>
        """
        text = f"Hello {user_name}, your Agri-Smart {plan_type} subscription is active until {end_date_str}. Ref: {payment_reference}."
        return cls._send_smtp(to_email, subject, html, text)


