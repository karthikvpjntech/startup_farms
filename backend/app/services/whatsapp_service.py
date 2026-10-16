import logging
import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from app.core.config import settings

logger = logging.getLogger("agri_smart.whatsapp_service")


class WhatsAppService:
    """
    Meta Cloud WhatsApp Business API Client.
    Dispatches interactive text notifications, order updates, harvest procurement alerts,
    and verification OTPs directly to user WhatsApp numbers.
    """

    @classmethod
    def format_phone_number(cls, mobile: str) -> str:
        """
        Normalizes mobile number into standard international format for WhatsApp (E.164 without +).
        Default prefix is 91 (India) for 10-digit mobile numbers.
        """
        cleaned = "".join(filter(str.isdigit, mobile))
        if len(cleaned) == 10:
            cleaned = f"91{cleaned}"
        return cleaned

    @classmethod
    def send_text_message(cls, to_mobile: str, message_body: str) -> Dict[str, Any]:
        """
        Sends standard text message via Meta Graph API.
        """
        if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.info(
                "[WHATSAPP SIMULATED] To: %s | Message: %s | (Set WHATSAPP_ACCESS_TOKEN to send live)",
                to_mobile,
                message_body
            )
            return {"status": "simulated", "to": to_mobile, "message": message_body}

        recipient = cls.format_phone_number(to_mobile)
        url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": True,
                "body": message_body,
            },
        }

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                logger.info("WhatsApp message successfully dispatched to %s: %s", recipient, res_json)
                return {"status": "sent", "response": res_json}
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                err_data = json.loads(err_body)
                error_obj = err_data.get("error", {})
                error_code = error_obj.get("code")
                error_msg = error_obj.get("message", "")
                if error_code == 190 or "OAuthException" in str(err_body):
                    logger.error(
                        "❌ [WHATSAPP ERROR 401] Meta Cloud API Access Token has EXPIRED or is INVALID (OAuthException code 190). "
                        "Please update WHATSAPP_ACCESS_TOKEN in backend/.env with a valid token from Meta for Developers dashboard."
                    )
                elif error_code == 131030:
                    logger.error(
                        "❌ [WHATSAPP ERROR] Recipient %s is not registered in Meta Sandbox test phone numbers list. "
                        "Add the recipient number in Meta Developer Console under WhatsApp -> API Setup -> To.", recipient
                    )
                elif error_code == 131047:
                    logger.error(
                        "❌ [WHATSAPP ERROR] Cannot send free-form text outside 24h window to %s. "
                        "Configure WHATSAPP_OTP_TEMPLATE_NAME in .env to send an approved Meta Template message.", recipient
                    )
                else:
                    logger.error("WhatsApp API HTTP error %d: %s", err.code, err_body)
            except Exception:
                logger.error("WhatsApp API HTTP error %d: %s", err.code, err_body)
            return {"status": "failed", "error": err_body, "code": err.code}
        except Exception as exc:
            logger.error("Failed to send WhatsApp message to %s: %s", recipient, exc, exc_info=True)
            return {"status": "failed", "error": str(exc)}

    @classmethod
    def send_template_message(
        cls,
        to_mobile: str,
        template_name: str,
        language_code: str = "en_US",
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Sends an approved Meta WhatsApp template message (e.g. for marketing, utility, authentication).
        """
        if not settings.WHATSAPP_ENABLED or not settings.WHATSAPP_ACCESS_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
            logger.info("[WHATSAPP SIMULATED TEMPLATE] To: %s | Template: %s", to_mobile, template_name)
            return {"status": "simulated", "template": template_name}

        recipient = cls.format_phone_number(to_mobile)
        url = f"{settings.WHATSAPP_API_URL}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"

        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
            },
        }

        if components:
            payload["template"]["components"] = components

        headers = {
            "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                logger.info("WhatsApp template '%s' successfully sent to %s: %s", template_name, recipient, res_json)
                return {"status": "sent", "response": res_json}
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8")
            try:
                err_data = json.loads(err_body)
                error_obj = err_data.get("error", {})
                error_code = error_obj.get("code")
                if error_code == 190 or "OAuthException" in str(err_body):
                    logger.error(
                        "❌ [WHATSAPP ERROR 401] Meta Cloud API Access Token has EXPIRED or is INVALID (code 190). "
                        "Please update WHATSAPP_ACCESS_TOKEN in backend/.env."
                    )
                elif error_code == 131030:
                    logger.error(
                        "❌ [WHATSAPP ERROR] Recipient %s is not registered in Meta Sandbox test phone numbers list.", recipient
                    )
                else:
                    logger.error("WhatsApp Template HTTP error %d: %s", err.code, err_body)
            except Exception:
                logger.error("WhatsApp Template HTTP error %d: %s", err.code, err_body)
            return {"status": "failed", "error": err_body, "code": err.code}
        except Exception as exc:
            logger.error("Failed to send WhatsApp template to %s: %s", recipient, exc, exc_info=True)
            return {"status": "failed", "error": str(exc)}

    @classmethod
    def send_order_confirmation(
        cls,
        to_mobile: str,
        order_number: str,
        customer_name: str,
        total_amount: str,
        tracking_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends order confirmation message via WhatsApp.
        """
        track_link = tracking_url or f"{settings.FRONTEND_URL}/orders"
        msg = (
            f"🌱 *Agri-Smart Order Confirmation*\n\n"
            f"Hello {customer_name},\n"
            f"Your order *{order_number}* has been confirmed!\n\n"
            f"💰 *Total Amount:* ₹{total_amount}\n"
            f"📦 *Status:* Processing\n\n"
            f"Track live harvest dispatch & delivery:\n"
            f"{track_link}\n\n"
            f"Thank you for supporting local farmers! 🌾"
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_otp(
        cls,
        to_mobile: str,
        user_name: str,
        otp_code: str,
        purpose: str = "Two-Factor Verification",
        expiry_minutes: int = 10,
    ) -> Dict[str, Any]:
        """
        Sends OTP verification code via WhatsApp.
        Supports Meta Approved Template messages or standard text messages.
        """
        # If a custom or standard Meta OTP template is configured, dispatch via Template
        if settings.WHATSAPP_OTP_TEMPLATE_NAME:
            template_components = [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": str(otp_code)}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {"type": "text", "text": str(otp_code)}
                    ]
                }
            ]
            template_res = cls.send_template_message(
                to_mobile=to_mobile,
                template_name=settings.WHATSAPP_OTP_TEMPLATE_NAME,
                language_code=settings.WHATSAPP_OTP_TEMPLATE_LANG or "en_US",
                components=template_components,
            )
            if template_res.get("status") == "sent":
                return template_res

        # Standard direct text message
        msg = (
            f"🛡️ *Agri-Smart Security Verification*\n\n"
            f"Hello {user_name},\n"
            f"Your code for *{purpose}* is:\n\n"
            f"👉 *{otp_code}*\n\n"
            f"⏱️ Valid for {expiry_minutes} minutes. Do not share this code with anyone.\n"
            f"© 2026 Agri-Smart Ecosystem"
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_password_reset(
        cls,
        to_mobile: str,
        user_name: str,
        otp_code: str,
        reset_url: Optional[str] = None,
        expiry_minutes: int = 15,
    ) -> Dict[str, Any]:
        """
        Sends Password Reset OTP and link via WhatsApp.
        """
        link = reset_url or f"{settings.FRONTEND_URL}/reset-password"
        msg = (
            f"🔑 *Agri-Smart Password Reset*\n\n"
            f"Hello {user_name},\n"
            f"Use the OTP code below to reset your password:\n\n"
            f"👉 *{otp_code}*\n\n"
            f"Direct Reset Link:\n{link}\n\n"
            f"⏱️ Valid for {expiry_minutes} minutes. If you did not request this, please secure your account."
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_welcome(
        cls,
        to_mobile: str,
        user_name: str,
        role: str,
    ) -> Dict[str, Any]:
        """
        Sends Welcome message on account creation via WhatsApp.
        """
        msg = (
            f"🌱 *Welcome to Agri-Smart Ecosystem!*\n\n"
            f"Hello {user_name},\n"
            f"Your account as *{role}* is now active.\n\n"
            f"Access your farm dashboard & marketplace:\n"
            f"{settings.FRONTEND_URL}/login\n\n"
            f"Empowering direct farm trade and smart cultivation! 🌾"
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_payment_receipt(
        cls,
        to_mobile: str,
        customer_name: str,
        order_number: str,
        payment_number: str,
        amount: str,
        payment_method: str,
    ) -> Dict[str, Any]:
        """
        Sends Payment confirmation receipt via WhatsApp.
        """
        msg = (
            f"✅ *Payment Received — Agri-Smart*\n\n"
            f"Hello {customer_name},\n"
            f"Your payment of *₹{amount}* for order *{order_number}* has been successfully recorded.\n\n"
            f"🧾 *Receipt:* {payment_number}\n"
            f"💳 *Method:* {payment_method}\n"
            f"Status: *PAID*\n\n"
            f"View order details: {settings.FRONTEND_URL}/orders"
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_delivery_dispatch(
        cls,
        to_mobile: str,
        customer_name: str,
        order_number: str,
        driver_name: str,
        driver_phone: str,
        vehicle_number: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sends Out for Delivery notification via WhatsApp.
        """
        veh_str = f"\n🚙 *Vehicle:* {vehicle_number}" if vehicle_number else ""
        msg = (
            f"🚚 *Out for Delivery — Agri-Smart*\n\n"
            f"Hello {customer_name},\n"
            f"Your order *{order_number}* is on its way!\n\n"
            f"👤 *Driver:* {driver_name}\n"
            f"📞 *Contact:* {driver_phone}{veh_str}\n\n"
            f"Track live delivery: {settings.FRONTEND_URL}/orders"
        )
        return cls.send_text_message(to_mobile, msg)

    @classmethod
    def send_harvest_alert(
        cls,
        to_mobile: str,
        farmer_name: str,
        crop_name: str,
        yield_quantity: str,
        yield_unit: str,
        price_per_unit: str,
    ) -> Dict[str, Any]:
        """
        Sends Fresh Harvest notification to buyers via WhatsApp.
        """
        msg = (
            f"🌾 *Fresh Farm Harvest Alert!*\n\n"
            f"Farmer *{farmer_name}* has fresh *{crop_name}* ready for procurement!\n\n"
            f"📦 *Quantity:* {yield_quantity} {yield_unit}\n"
            f"💰 *Mandi Price:* ₹{price_per_unit}/{yield_unit}\n\n"
            f"Order directly from the farm:\n"
            f"{settings.FRONTEND_URL}/marketplace/produce"
        )
        return cls.send_text_message(to_mobile, msg)

