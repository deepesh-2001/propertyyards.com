"""
Travel Notification Service
Sends professional, warm greeting + request-style notifications for
cab, train, and hotel bookings and auto-lead creation.

Channels: Email (SMTP) + WhatsApp (Meta Cloud API)
Tone:     Professional greeting, personalised, ends with a polite property-interest request.
"""
import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

logger = logging.getLogger(__name__)

# ─── Brand constants ──────────────────────────────────────────────────────────
BRAND_NAME = "PropertyYards"
BRAND_TAGLINE = "Your Trusted Real Estate Partner"
BRAND_COLOUR = "#1a3c5e"      # deep navy
ACCENT_COLOUR = "#e8a020"     # warm gold
BRAND_URL = "https://propertyyards.com"
SUPPORT_EMAIL = "support@propertyyards.com"
SUPPORT_PHONE = "+91-1800-XXX-XXXX"


# ─── Shared HTML scaffold ─────────────────────────────────────────────────────
_BASE_STYLE = f"""
<style>
  body {{ margin:0; padding:0; background:#f4f6f9; font-family:'Segoe UI',Arial,sans-serif; color:#333; }}
  .wrapper {{ max-width:620px; margin:30px auto; background:#fff; border-radius:12px;
              box-shadow:0 4px 20px rgba(0,0,0,.10); overflow:hidden; }}
  .header {{ background:linear-gradient(135deg,{BRAND_COLOUR} 0%,#2a5298 100%);
             padding:36px 32px 28px; text-align:center; }}
  .header img {{ height:42px; margin-bottom:12px; }}
  .header h1 {{ margin:0; color:#fff; font-size:24px; font-weight:700; letter-spacing:.3px; }}
  .header p  {{ margin:6px 0 0; color:rgba(255,255,255,.80); font-size:14px; }}
  .body {{ padding:32px; }}
  .greeting {{ font-size:17px; color:{BRAND_COLOUR}; font-weight:600; margin-bottom:8px; }}
  .intro   {{ font-size:14px; line-height:1.7; color:#555; margin-bottom:20px; }}
  .card    {{ background:#f8fafc; border-left:4px solid {ACCENT_COLOUR};
              border-radius:8px; padding:18px 22px; margin:20px 0; }}
  .card h3 {{ margin:0 0 12px; font-size:15px; color:{BRAND_COLOUR}; text-transform:uppercase;
              letter-spacing:.5px; }}
  .row     {{ display:flex; justify-content:space-between; padding:6px 0;
              border-bottom:1px solid #eee; font-size:13px; }}
  .row:last-child {{ border-bottom:none; }}
  .label   {{ color:#888; font-weight:500; }}
  .value   {{ color:#222; font-weight:600; text-align:right; max-width:55%; }}
  .request-box {{ background:linear-gradient(135deg,#fef9ee 0%,#fef3d0 100%);
                  border:1px solid {ACCENT_COLOUR}; border-radius:8px;
                  padding:18px 22px; margin:24px 0; }}
  .request-box h3 {{ margin:0 0 8px; color:{BRAND_COLOUR}; font-size:15px; }}
  .request-box p  {{ margin:0; font-size:13px; line-height:1.7; color:#555; }}
  .cta    {{ text-align:center; margin:28px 0 12px; }}
  .btn    {{ display:inline-block; padding:13px 32px; background:{ACCENT_COLOUR};
             color:#fff; text-decoration:none; border-radius:6px; font-size:14px;
             font-weight:700; letter-spacing:.3px; }}
  .divider {{ border:none; border-top:1px solid #eee; margin:24px 0; }}
  .footer {{ background:#f8fafc; padding:20px 32px; text-align:center;
             font-size:12px; color:#999; line-height:1.8; }}
  .footer a {{ color:{BRAND_COLOUR}; text-decoration:none; }}
</style>
"""


def _html_wrap(header_icon: str, header_title: str, header_subtitle: str, body: str) -> str:
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8">{_BASE_STYLE}</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>{header_icon} {header_title}</h1>
      <p>{header_subtitle}</p>
    </div>
    <div class="body">
      {body}
    </div>
    <div class="footer">
      <p>You received this message because you booked a service on <strong>{BRAND_NAME}</strong>.</p>
      <p>Questions? Write to <a href="mailto:{SUPPORT_EMAIL}">{SUPPORT_EMAIL}</a>
         &nbsp;|&nbsp; Call <a href="tel:{SUPPORT_PHONE}">{SUPPORT_PHONE}</a></p>
      <p>&copy; {datetime.utcnow().year} {BRAND_NAME}. All rights reserved.</p>
    </div>
  </div>
</body></html>"""


def _row(label: str, value: str) -> str:
    return f'<div class="row"><span class="label">{label}</span><span class="value">{value}</span></div>'


def _property_request_block(name: str, city: Optional[str] = None) -> str:
    city_txt = f" in {city}" if city else ""
    return f"""
    <div class="request-box">
      <h3>🏡 Explore Properties{city_txt}</h3>
      <p>
        Dear <strong>{name}</strong>, as you plan your visit{city_txt}, we would be honoured to assist you
        in exploring premium residential and commercial properties available through <strong>{BRAND_NAME}</strong>.
        Whether you are looking to invest, rent, or simply explore the real estate market,
        our expert team is ready to guide you every step of the way.
      </p>
      <p style="margin-top:10px;">
        We kindly request a few minutes of your time to connect with our property advisor —
        at your convenience, completely free of any obligation.
      </p>
    </div>
    <div class="cta">
      <a href="{BRAND_URL}/properties{('?city=' + city.lower().replace(' ', '-')) if city else ''}"
         class="btn">Browse Properties {city_txt.strip()}</a>
    </div>"""


# ─── TravelNotificationService ────────────────────────────────────────────────

class TravelNotificationService:
    """
    Sends professional greeting + property-request notifications via
    Email and WhatsApp for all travel booking events.
    """

    def __init__(self):
        from app.config import settings
        self.settings = settings
        self.from_email: str = getattr(settings, "FROM_EMAIL", f"noreply@propertyyards.com")
        self.smtp_host: str = getattr(settings, "SMTP_HOST", "smtp.gmail.com")
        self.smtp_port: int = int(getattr(settings, "SMTP_PORT", 587))
        self.smtp_user: str = getattr(settings, "SMTP_USERNAME", "") or getattr(settings, "SMTP_USER", "")
        self.smtp_pass: str = getattr(settings, "SMTP_PASSWORD", "") or getattr(settings, "SMTP_PASS", "")
        self.wa_token: str = getattr(settings, "WHATSAPP_ACCESS_TOKEN", "")
        self.wa_phone_id: str = getattr(settings, "WHATSAPP_PHONE_NUMBER_ID", "")

    # ── Internal send helpers ─────────────────────────────────────────────────

    async def _send_email(self, to: str, subject: str, html: str) -> bool:
        """Send via SMTP; silently skip if not configured."""
        if not self.smtp_user or not self.smtp_pass:
            logger.info(f"[TravelNotif] Email skipped (SMTP not configured) → {to}")
            return False
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{BRAND_NAME} <{self.from_email}>"
            msg["To"] = to
            msg.attach(MIMEText(html, "html"))
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self._sync_send, msg)
            logger.info(f"[TravelNotif] Email sent → {to} | {subject}")
            return True
        except Exception as e:
            logger.warning(f"[TravelNotif] Email failed → {to}: {e}")
            return False

    def _sync_send(self, msg: MIMEMultipart):
        with smtplib.SMTP(self.smtp_host, self.smtp_port) as srv:
            srv.ehlo()
            srv.starttls()
            srv.login(self.smtp_user, self.smtp_pass)
            srv.send_message(msg)

    async def _send_whatsapp(self, phone: str, text: str) -> bool:
        """Send free-form WhatsApp text; silently skip if not configured."""
        if not self.wa_token or not self.wa_phone_id:
            logger.info(f"[TravelNotif] WhatsApp skipped (not configured) → {phone}")
            return False
        try:
            import aiohttp
            url = f"https://graph.facebook.com/v18.0/{self.wa_phone_id}/messages"
            headers = {"Authorization": f"Bearer {self.wa_token}",
                       "Content-Type": "application/json"}
            payload = {
                "messaging_product": "whatsapp",
                "to": phone.replace(" ", "").replace("-", ""),
                "type": "text",
                "text": {"body": text}
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, headers=headers, json=payload) as r:
                    if r.status in (200, 201):
                        logger.info(f"[TravelNotif] WhatsApp sent → {phone}")
                        return True
                    err = await r.text()
                    logger.warning(f"[TravelNotif] WhatsApp API error {r.status}: {err}")
                    return False
        except Exception as e:
            logger.warning(f"[TravelNotif] WhatsApp failed → {phone}: {e}")
            return False

    # ── CAB booking notification ──────────────────────────────────────────────

    async def notify_cab_booking(
        self,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        booking_id: str,
        provider: str,
        category: str,
        pickup: str,
        drop: str,
        fare: float,
        otp: str,
        city: Optional[str] = None
    ):
        """Booking confirmation + warm property interest request."""
        subject = f"Your {provider} Cab is Confirmed — {BRAND_NAME}"
        fare_str = f"₹{fare:,.0f}"

        body = f"""
        <p class="greeting">Dear {name},</p>
        <p class="intro">
          Greetings from <strong>{BRAND_NAME}</strong>! 🎉<br>
          We are delighted to confirm that your cab has been successfully booked.
          Your ride details are listed below — please share the OTP only with your driver.
        </p>
        <div class="card">
          <h3>Cab Booking Details</h3>
          {_row("Booking ID", booking_id)}
          {_row("Provider", provider)}
          {_row("Category", category.title())}
          {_row("Pickup", pickup)}
          {_row("Drop", drop)}
          {_row("Estimated Fare", fare_str)}
          {_row("Driver OTP", f"<span style='font-size:20px;letter-spacing:4px;color:{BRAND_COLOUR};'>{otp}</span>")}
        </div>
        <hr class="divider">
        {_property_request_block(name, city)}
        <p class="intro" style="font-size:12px;color:#999;margin-top:20px;">
          For any assistance with your ride, contact {provider} support directly.
          For property enquiries, we are always here at {SUPPORT_EMAIL}.
        </p>
        """
        html = _html_wrap("🚕", "Cab Booking Confirmed", f"Booking ID: {booking_id}", body)

        wa_text = (
            f"Hello {name}! 👋\n\n"
            f"*{BRAND_NAME}* — Cab Booking Confirmed ✅\n\n"
            f"🚕 *{provider}* ({category.title()})\n"
            f"📍 Pickup: {pickup}\n"
            f"📍 Drop: {drop}\n"
            f"💰 Fare: {fare_str}\n"
            f"🔐 OTP: *{otp}*  _(Share only with driver)_\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏡 *Exploring properties{' in ' + city if city else ''}?*\n"
            f"We'd love to help you find your perfect home or investment. "
            f"May we schedule a quick call with our property advisor at your convenience?\n\n"
            f"Browse: {BRAND_URL}/properties\n\n"
            f"Warm regards,\n{BRAND_NAME} Team\n{SUPPORT_EMAIL}"
        )

        tasks = []
        if email:
            tasks.append(self._send_email(email, subject, html))
        if phone:
            tasks.append(self._send_whatsapp(phone, wa_text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ── TRAIN booking notification ────────────────────────────────────────────

    async def notify_train_booking(
        self,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        booking_id: str,
        pnr: str,
        train_name: str,
        train_number: str,
        from_station: str,
        to_station: str,
        travel_date: str,
        travel_class: str,
        passengers: int,
        total_fare: float,
        city: Optional[str] = None
    ):
        """Train ticket confirmation + property discovery request for destination city."""
        subject = f"Train Ticket Confirmed — PNR {pnr} | {BRAND_NAME}"
        fare_str = f"₹{total_fare:,.0f}"
        dest_city = city or to_station

        body = f"""
        <p class="greeting">Dear {name},</p>
        <p class="intro">
          Warm greetings from <strong>{BRAND_NAME}</strong>! 🚆<br>
          Your train ticket has been booked successfully. Please save your PNR number for
          tracking, cancellation, and boarding.
        </p>
        <div class="card">
          <h3>Train Booking Details</h3>
          {_row("PNR Number", f"<span style='font-size:18px;font-weight:800;letter-spacing:3px;color:{BRAND_COLOUR};'>{pnr}</span>")}
          {_row("Booking ID", booking_id)}
          {_row("Train", f"{train_name} ({train_number})")}
          {_row("From", from_station)}
          {_row("To", to_station)}
          {_row("Date of Travel", travel_date)}
          {_row("Class", travel_class)}
          {_row("Passengers", str(passengers))}
          {_row("Total Fare", fare_str)}
        </div>
        <hr class="divider">
        {_property_request_block(name, dest_city)}
        <p class="intro" style="font-size:12px;color:#999;margin-top:20px;">
          Track your PNR at <a href="https://www.indianrail.gov.in" style="color:{BRAND_COLOUR};">Indian Railways</a>.
          For property enquiries in {dest_city}, reach us at {SUPPORT_EMAIL}.
        </p>
        """
        html = _html_wrap("🚆", "Train Ticket Confirmed", f"PNR: {pnr} | {train_name}", body)

        wa_text = (
            f"Hello {name}! 👋\n\n"
            f"*{BRAND_NAME}* — Train Ticket Confirmed ✅\n\n"
            f"🚆 *{train_name}* ({train_number})\n"
            f"📍 {from_station} → {to_station}\n"
            f"📅 Date: {travel_date}  |  Class: {travel_class}\n"
            f"👥 Passengers: {passengers}\n"
            f"💰 Total Fare: {fare_str}\n"
            f"🎫 *PNR: {pnr}*\n\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🏡 *Planning a stay in {dest_city}?*\n"
            f"We have curated properties and investment opportunities in {dest_city} that "
            f"may interest you. We would be happy to connect you with a local property "
            f"expert — at no cost, and entirely at your convenience.\n\n"
            f"View properties: {BRAND_URL}/properties?city={dest_city.lower().replace(' ', '-')}\n\n"
            f"Warm regards,\n{BRAND_NAME} Team\n{SUPPORT_EMAIL}"
        )

        tasks = []
        if email:
            tasks.append(self._send_email(email, subject, html))
        if phone:
            tasks.append(self._send_whatsapp(phone, wa_text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ── HOTEL booking notification ────────────────────────────────────────────

    async def notify_hotel_booking(
        self,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        booking_id: str,
        confirmation_number: str,
        hotel_name: str,
        hotel_address: str,
        check_in: str,
        check_out: str,
        nights: int,
        guests: int,
        room_type: str,
        final_price: float,
        provider: str,
        city: Optional[str] = None
    ):
        """Hotel booking confirmation + long-stay property request."""
        subject = f"Hotel Booking Confirmed — {hotel_name} | {BRAND_NAME}"
        price_str = f"₹{final_price:,.0f}"

        long_stay_note = ""
        if nights >= 7:
            long_stay_note = f"""
            <p class="intro" style="background:#e8f5e9;border-left:4px solid #43a047;
               padding:12px 16px;border-radius:6px;font-size:13px;">
              💡 <strong>Did you know?</strong> For stays of 7+ nights in {city or hotel_address.split(',')[-1].strip()},
              many of our clients find that a short-term furnished apartment or
              service apartment works out more economical than a hotel.
              Ask our team for options!
            </p>"""

        body = f"""
        <p class="greeting">Dear {name},</p>
        <p class="intro">
          Warm greetings from <strong>{BRAND_NAME}</strong>! 🏨<br>
          Your hotel booking has been confirmed. We hope you have a wonderful and comfortable stay.
          Please find your reservation details below.
        </p>
        <div class="card">
          <h3>Hotel Booking Details</h3>
          {_row("Confirmation No.", f"<span style='font-size:16px;font-weight:800;letter-spacing:2px;color:{BRAND_COLOUR};'>{confirmation_number}</span>")}
          {_row("Booking ID", booking_id)}
          {_row("Hotel", hotel_name)}
          {_row("Address", hotel_address)}
          {_row("Room Type", room_type.title())}
          {_row("Check-in", check_in)}
          {_row("Check-out", check_out)}
          {_row("Duration", f"{nights} night{'s' if nights > 1 else ''}")}
          {_row("Guests", str(guests))}
          {_row("Total (incl. taxes)", price_str)}
          {_row("Booked via", provider)}
        </div>
        {long_stay_note}
        <hr class="divider">
        {_property_request_block(name, city)}
        <p class="intro" style="font-size:12px;color:#999;margin-top:20px;">
          For hotel-related queries, please contact {provider} support.
          To explore real estate in {city or 'this area'}, write to us at {SUPPORT_EMAIL}.
        </p>
        """
        html = _html_wrap("🏨", "Hotel Booking Confirmed",
                          f"Confirmation: {confirmation_number} | {hotel_name}", body)

        wa_text = (
            f"Hello {name}! 👋\n\n"
            f"*{BRAND_NAME}* — Hotel Booking Confirmed ✅\n\n"
            f"🏨 *{hotel_name}*\n"
            f"📍 {hotel_address}\n"
            f"🛏 Room: {room_type.title()}\n"
            f"📅 Check-in: {check_in}  |  Check-out: {check_out}\n"
            f"🌙 {nights} night{'s' if nights > 1 else ''}  |  👥 {guests} guest{'s' if guests > 1 else ''}\n"
            f"💰 Total: {price_str}\n"
            f"🎫 *Confirmation: {confirmation_number}*\n\n"
            + (f"💡 Staying {nights} nights? Ask us about short-term furnished apartments "
               f"in {city or 'this area'} — often more comfortable and economical!\n\n"
               if nights >= 7 else "")
            + f"━━━━━━━━━━━━━━━\n"
            f"🏡 *Interested in owning property in {city or 'this city'}?*\n"
            f"We would love to introduce you to some exciting real estate opportunities "
            f"through {BRAND_NAME}. May we arrange a brief, no-obligation consultation "
            f"with one of our property advisors at a time that suits you?\n\n"
            f"View listings: {BRAND_URL}/properties{('?city=' + city.lower().replace(' ', '-')) if city else ''}\n\n"
            f"Warm regards,\n{BRAND_NAME} Team\n{SUPPORT_EMAIL}"
        )

        tasks = []
        if email:
            tasks.append(self._send_email(email, subject, html))
        if phone:
            tasks.append(self._send_whatsapp(phone, wa_text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ── CANCELLATION notification ─────────────────────────────────────────────

    async def notify_cancellation(
        self,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        service_type: str,
        booking_id: str,
        refund_amount: Optional[float] = None,
        refund_note: Optional[str] = None
    ):
        """Cancellation acknowledgement with refund info."""
        subject = f"{service_type.title()} Booking Cancelled — {BRAND_NAME}"
        refund_block = ""
        if refund_amount is not None:
            refund_block = f"""
            <div class="card" style="border-left-color:#43a047;">
              <h3>Refund Information</h3>
              {_row("Refund Amount", f"₹{refund_amount:,.0f}")}
              {_row("Status", "Processing")}
              {_row("Note", refund_note or "Refund will be credited within 5–7 business days")}
            </div>"""

        body = f"""
        <p class="greeting">Dear {name},</p>
        <p class="intro">
          Greetings from <strong>{BRAND_NAME}</strong>.<br>
          We have successfully processed the cancellation for your {service_type} booking
          (ID: <strong>{booking_id}</strong>). We are sorry to see your plans change and
          hope to serve you again soon.
        </p>
        {refund_block}
        <hr class="divider">
        <div class="request-box">
          <h3>🏡 We Are Still Here for You</h3>
          <p>
            Even though your travel plans have changed, if you are considering exploring
            real estate opportunities or require any property-related guidance,
            <strong>{BRAND_NAME}</strong> is always at your service.
            We would be delighted to assist you at your convenience.
          </p>
        </div>
        <div class="cta">
          <a href="{BRAND_URL}" class="btn">Visit {BRAND_NAME}</a>
        </div>
        <p class="intro" style="font-size:12px;color:#999;margin-top:20px;">
          If you need further assistance, please contact us at {SUPPORT_EMAIL}.
        </p>
        """
        html = _html_wrap("✅", f"{service_type.title()} Booking Cancelled",
                          f"Booking ID: {booking_id}", body)

        wa_text = (
            f"Hello {name},\n\n"
            f"*{BRAND_NAME}* — {service_type.title()} Booking Cancelled ✅\n\n"
            f"📋 Booking ID: {booking_id}\n"
            + (f"💰 Refund: ₹{refund_amount:,.0f}\n"
               f"⏱ {refund_note or 'Refund within 5–7 business days'}\n" if refund_amount else "")
            + f"\nWe are sorry your plans changed. Should you wish to explore "
              f"property options or investment opportunities, we are always here to help.\n\n"
              f"Visit: {BRAND_URL}\n\n"
              f"Warm regards,\n{BRAND_NAME} Team"
        )

        tasks = []
        if email:
            tasks.append(self._send_email(email, subject, html))
        if phone:
            tasks.append(self._send_whatsapp(phone, wa_text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    # ── HOT LEAD follow-up notification ──────────────────────────────────────

    async def notify_hot_lead(
        self,
        name: str,
        email: Optional[str],
        phone: Optional[str],
        city: Optional[str],
        intent_tags: list,
        source: str
    ):
        """
        Sent when a travel activity signals high property intent
        (e.g. cab to DLF Phase, 7-night hotel stay).
        Warm personal outreach from the property team.
        """
        subject = f"We noticed your interest — {BRAND_NAME} Property Experts are here"
        city_str = f" in {city}" if city else ""
        tags_readable = ", ".join(
            t.replace("_", " ").title() for t in intent_tags[:4]
        )

        body = f"""
        <p class="greeting">Dear {name},</p>
        <p class="intro">
          Warm greetings from the <strong>{BRAND_NAME}</strong> Property Advisory Team! 🌟<br>
          We noticed that your recent travel activity{city_str} may align with an interest
          in exploring real estate opportunities. We hope this message finds you well.
        </p>
        <div class="card">
          <h3>Why We Are Reaching Out</h3>
          {_row("Your Activity", source.replace("_", " ").title())}
          {_row("Location Interest", city or "Multiple locations")}
          {_row("Signals Detected", tags_readable or "Property area visit")}
        </div>
        <div class="request-box">
          <h3>🏡 Personalised Property Consultation — Complimentary</h3>
          <p>
            Based on your travel patterns, our advisors believe there may be properties
            {city_str} that perfectly match your lifestyle and investment goals.
          </p>
          <p style="margin-top:10px;">
            We would be honoured to offer you a <strong>complimentary, no-obligation</strong>
            property consultation — at a time that is convenient for you.
            Simply reply to this message or click the button below to schedule a call.
          </p>
        </div>
        <div class="cta">
          <a href="{BRAND_URL}/contact?ref=travel_lead" class="btn">Schedule a Free Consultation</a>
        </div>
        <p class="intro" style="font-size:13px;color:#555;margin-top:4px;text-align:center;">
          No commitment. No pressure. Just honest guidance from our experts.
        </p>
        <hr class="divider">
        <p class="intro" style="font-size:12px;color:#999;">
          If you would prefer not to receive such recommendations, simply reply "STOP"
          and we will immediately remove you from our outreach list. We respect your privacy.
        </p>
        """
        html = _html_wrap("🌟", "A Personal Note from Our Property Team",
                          f"{BRAND_NAME} — {BRAND_TAGLINE}", body)

        wa_text = (
            f"Hello {name}! 👋\n\n"
            f"Warm greetings from *{BRAND_NAME}* Property Advisory Team! 🌟\n\n"
            f"We noticed your recent travel activity{city_str} and wanted to reach out personally.\n\n"
            f"🏡 *Are you exploring property options{city_str}?*\n\n"
            f"Our team has curated some excellent residential and investment opportunities "
            f"that may be of interest to you. We would love to offer you a "
            f"*complimentary, no-obligation consultation* with one of our senior advisors.\n\n"
            f"📅 May we schedule a brief call at your convenience?\n\n"
            f"View properties: {BRAND_URL}/properties{('?city=' + city.lower().replace(' ', '-')) if city else ''}\n"
            f"Contact us: {SUPPORT_EMAIL}  |  {SUPPORT_PHONE}\n\n"
            f"_(Reply STOP to opt out of property recommendations)_\n\n"
            f"Warm regards,\n*{BRAND_NAME} Property Advisory Team*"
        )

        tasks = []
        if email:
            tasks.append(self._send_email(email, subject, html))
        if phone:
            tasks.append(self._send_whatsapp(phone, wa_text))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)


# Singleton
travel_notification_service = TravelNotificationService()
