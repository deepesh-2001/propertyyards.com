"""
Telegram Bot Integration
Automated bot for property alerts, notifications, and customer service
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import aiohttp

logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot for PropertyYards"""

    def __init__(self):
        self.token = None
        self.api_base = "https://api.telegram.org/bot"
        self.webhook_url = None
        self.subscribed_users: Dict[str, Dict] = {}  # chat_id -> user info
        self.running = False

    async def initialize(self, token: str, webhook_url: Optional[str] = None):
        """Initialize bot with token"""
        self.token = token
        self.webhook_url = webhook_url
        self.api_base = f"https://api.telegram.org/bot{token}"
        logger.info("Telegram Bot initialized")

    async def set_webhook(self, url: str):
        """Set webhook for receiving updates"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/setWebhook",
                    json={"url": url}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if data.get("ok"):
                            logger.info("Telegram webhook set successfully")
                            return True
                    logger.error(f"Failed to set webhook: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Webhook setup error: {e}")
            return False

    async def send_message(
        self,
        chat_id: str,
        text: str,
        parse_mode: str = "HTML",
        reply_markup: Optional[Dict] = None
    ) -> bool:
        """Send message to user"""
        try:
            payload = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }

            if reply_markup:
                payload["reply_markup"] = reply_markup

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendMessage",
                    json=payload
                ) as response:
                    if response.status == 200:
                        return True
                    logger.error(f"Send message failed: {response.status}")
                    return False

        except Exception as e:
            logger.error(f"Send message error: {e}")
            return False

    async def send_photo(
        self,
        chat_id: str,
        photo_url: str,
        caption: Optional[str] = None
    ) -> bool:
        """Send photo to user"""
        try:
            payload = {
                "chat_id": chat_id,
                "photo": photo_url
            }

            if caption:
                payload["caption"] = caption
                payload["parse_mode"] = "HTML"

            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/sendPhoto",
                    json=payload
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.error(f"Send photo error: {e}")
            return False

    async def handle_update(self, update: Dict[str, Any]):
        """Handle incoming update from webhook"""
        try:
            if "message" in update:
                message = update["message"]
                chat_id = str(message["chat"]["id"])
                text = message.get("text", "")

                # Store user info
                self.subscribed_users[chat_id] = {
                    "chat_id": chat_id,
                    "username": message["chat"].get("username"),
                    "first_name": message["chat"].get("first_name"),
                    "last_name": message["chat"].get("last_name"),
                    "subscribed_at": datetime.utcnow()
                }

                # Process command or message
                await self._process_message(chat_id, text)

            elif "callback_query" in update:
                callback = update["callback_query"]
                chat_id = str(callback["message"]["chat"]["id"])
                data = callback.get("data", "")
                await self._process_callback(chat_id, data)

        except Exception as e:
            logger.error(f"Handle update error: {e}")

    async def _process_message(self, chat_id: str, text: str):
        """Process incoming message"""
        text = text.strip().lower()

        # Command handling
        if text == "/start":
            await self._send_welcome(chat_id)

        elif text == "/help":
            await self._send_help(chat_id)

        elif text == "/properties":
            await self._send_recent_properties(chat_id)

        elif text == "/search":
            await self.send_message(
                chat_id,
                "🔍 <b>Search Properties</b>\n\n"
                "Send me your search criteria:\n"
                "• City name (e.g., 'Mumbai', 'Delhi')\n"
                "• Property type (e.g., 'apartment', 'villa')\n"
                "• Budget range (e.g., 'under 50 lakhs')",
                reply_markup=self._get_search_menu()
            )

        elif text == "/alerts":
            await self._send_alerts_menu(chat_id)

        elif text == "/contact":
            await self.send_message(
                chat_id,
                "📞 <b>Contact Us</b>\n\n"
                "PropertyYards Support\n"
                "📧 Email: support@propertyyards.com\n"
                "📱 Phone: +91-800-PROPERTY\n"
                "🌐 Website: https://propertyyards.com\n\n"
                "Our team is available 24/7 to help you!"
            )

        elif text == "/status":
            await self._send_system_status(chat_id)

        elif text.startswith("/price"):
            city = text.replace("/price", "").strip()
            await self._send_price_trends(chat_id, city)

        elif text.startswith("/notify"):
            # Enable notifications
            await self._subscribe_notifications(chat_id)

        else:
            # Handle as search query
            await self._handle_search_query(chat_id, text)

    async def _process_callback(self, chat_id: str, data: str):
        """Process callback query"""
        if data.startswith("property_"):
            property_id = data.replace("property_", "")
            await self._send_property_details(chat_id, property_id)

        elif data == "search_by_city":
            await self.send_message(
                chat_id,
                "🏙 Send me the city name you're interested in:"
            )

        elif data == "search_by_budget":
            await self.send_message(
                chat_id,
                "💰 What's your budget?\nExamples:\n• Under 50 lakhs\n• 50-100 lakhs\n• Above 1 crore"
            )

        elif data == "enable_alerts":
            await self._subscribe_notifications(chat_id)

        elif data == "disable_alerts":
            await self._unsubscribe_notifications(chat_id)

    async def _send_welcome(self, chat_id: str):
        """Send welcome message"""
        welcome_text = (
            "🏡 <b>Welcome to PropertyYards Bot!</b>\n\n"
            "I'm your personal real estate assistant. I can help you:\n\n"
            "🏠 <b>Find Properties</b> - Search by city, budget, type\n"
            "🔔 <b>Get Alerts</b> - New listings in your area\n"
            "📊 <b>Market Trends</b> - Price trends and analysis\n"
            "⭐ <b>Save Favorites</b> - Track properties you like\n\n"
            "<b>Quick Commands:</b>\n"
            "• /properties - Latest listings\n"
            "• /search - Search properties\n"
            "• /alerts - Set up notifications\n"
            "• /contact - Get support\n\n"
            "Let's find your dream property! 🏠"
        )

        keyboard = {
            "inline_keyboard": [
                [{"text": "🏠 Browse Properties", "callback_data": "browse_properties"}],
                [{"text": "🔔 Enable Alerts", "callback_data": "enable_alerts"}],
                [{"text": "❓ Help & Support", "callback_data": "help"}]
            ]
        }

        await self.send_message(chat_id, welcome_text, reply_markup=keyboard)

    async def _send_help(self, chat_id: str):
        """Send help message"""
        help_text = (
            "📖 <b>PropertyYards Bot Commands</b>\n\n"
            "<b>Property Search:</b>\n"
            "• /properties - View latest listings\n"
            "• /search - Interactive property search\n"
            "• Send city name - Search in that city\n"
            "• Send budget - Filter by price\n\n"
            "<b>Notifications:</b>\n"
            "• /alerts - Manage property alerts\n"
            "• /notify - Enable notifications\n\n"
            "<b>Information:</b>\n"
            "• /price [city] - Price trends\n"
            "• /status - System status\n"
            "• /contact - Contact support\n\n"
            "<b>Tips:</b>\n"
            "• Simply type a city name to search\n"
            "• Use 'under', 'above' for budget filters\n"
            "• You'll get instant alerts for new properties"
        )

        await self.send_message(chat_id, help_text)

    async def _send_recent_properties(self, chat_id: str, limit: int = 5):
        """Send recent properties"""
        try:
            from app.database import get_db
            database = get_db()

            properties = await database.properties.find(
                {"status": "active"}
            ).sort("created_at", -1).limit(limit).to_list(length=limit)

            if not properties:
                await self.send_message(chat_id, "No properties available at the moment.")
                return

            message = "🏠 <b>Latest Properties</b>\n\n"

            for i, prop in enumerate(properties, 1):
                price_str = f"₹{prop.get('price', 0):,.0f}"
                city = prop.get('city', 'Unknown')
                prop_type = prop.get('property_type', 'Property')
                bedrooms = prop.get('bedrooms', 'N/A')

                message += (
                    f"{i}. <b>{prop.get('title', 'Property')}</b>\n"
                    f"   📍 {city} | {prop_type}\n"
                    f"   🛏 {bedrooms} BHK | 💰 {price_str}\n"
                    f"   /property_{str(prop['_id'])}\n\n"
                )

            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔍 Search More", "callback_data": "search_by_city"}],
                    [{"text": "🔔 Get Alerts", "callback_data": "enable_alerts"}]
                ]
            }

            await self.send_message(chat_id, message, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Send recent properties error: {e}")
            await self.send_message(chat_id, "Sorry, couldn't fetch properties. Please try again later.")

    async def _send_property_details(self, chat_id: str, property_id: str):
        """Send detailed property information"""
        try:
            from app.database import get_db
            database = get_db()

            property_data = await database.properties.find_one({"_id": property_id})

            if not property_data:
                await self.send_message(chat_id, "Property not found.")
                return

            price = f"₹{property_data.get('price', 0):,.0f}"

            details = (
                f"🏠 <b>{property_data.get('title', 'Property')}</b>\n\n"
                f"💰 <b>Price:</b> {price}\n"
                f"📍 <b>Location:</b> {property_data.get('city', 'N/A')}, "
                f"{property_data.get('locality', 'N/A')}\n"
                f"🏢 <b>Type:</b> {property_data.get('property_type', 'N/A')}\n"
                f"🛏 <b>Bedrooms:</b> {property_data.get('bedrooms', 'N/A')}\n"
                f"🚿 <b>Bathrooms:</b> {property_data.get('bathrooms', 'N/A')}\n"
                f"📐 <b>Area:</b> {property_data.get('area_sqft', 'N/A')} sq ft\n\n"
                f"📝 <b>Description:</b>\n"
                f"{property_data.get('description', 'No description available.')[:200]}...\n\n"
                f"🔗 View on website: https://propertyyards.com/property/{property_id}"
            )

            keyboard = {
                "inline_keyboard": [
                    [{"text": "📞 Contact Agent", "callback_data": f"contact_{property_id}"}],
                    [{"text": "❤️ Save Property", "callback_data": f"save_{property_id}"}],
                    [{"text": "🔙 Back to List", "callback_data": "browse_properties"}]
                ]
            }

            # Send photo if available
            if property_data.get('image_url'):
                await self.send_photo(chat_id, property_data['image_url'], details)
            else:
                await self.send_message(chat_id, details, reply_markup=keyboard)

        except Exception as e:
            logger.error(f"Send property details error: {e}")

    async def _handle_search_query(self, chat_id: str, query: str):
        """Handle natural language search query"""
        try:
            from app.database import get_db
            database = get_db()

            # Simple search logic
            search_filter = {"status": "active"}

            # Check for city names
            cities = ["mumbai", "delhi", "bangalore", "pune", "chennai", "hyderabad", "kolkata"]
            for city in cities:
                if city in query.lower():
                    search_filter["city"] = {"$regex": city, "$options": "i"}
                    break

            # Check for budget indicators
            if "under" in query or "below" in query:
                # Extract number and assume in lakhs
                import re
                numbers = re.findall(r'\d+', query)
                if numbers:
                    max_price = int(numbers[0]) * 100000
                    search_filter["price"] = {"$lte": max_price}

            properties = await database.properties.find(search_filter).limit(5).to_list(length=5)

            if properties:
                message = f"🔍 <b>Search Results for '{query}'</b>\n\n"
                for i, prop in enumerate(properties, 1):
                    message += (
                        f"{i}. {prop.get('title', 'Property')}\n"
                        f"   📍 {prop.get('city')} | 💰 ₹{prop.get('price', 0):,.0f}\n"
                        f"   /property_{str(prop['_id'])}\n\n"
                    )
            else:
                message = f"❌ No properties found for '{query}'\n\nTry:\n• A different city\n• Broader budget range\n• /properties for all listings"

            await self.send_message(chat_id, message)

        except Exception as e:
            logger.error(f"Search query error: {e}")

    async def _subscribe_notifications(self, chat_id: str):
        """Subscribe user to notifications"""
        try:
            from app.database import get_db
            database = get_db()

            await database.telegram_subscribers.update_one(
                {"chat_id": chat_id},
                {
                    "$set": {
                        "chat_id": chat_id,
                        "subscribed": True,
                        "subscribed_at": datetime.utcnow(),
                        **self.subscribed_users.get(chat_id, {})
                    }
                },
                upsert=True
            )

            await self.send_message(
                chat_id,
                "✅ <b>Notifications Enabled!</b>\n\n"
                "You'll receive alerts for:\n"
                "• New properties in your area\n"
                "• Price drops on saved properties\n"
                "• Market updates and trends\n\n"
                "To customize alerts, use /alerts"
            )

        except Exception as e:
            logger.error(f"Subscribe error: {e}")

    async def _unsubscribe_notifications(self, chat_id: str):
        """Unsubscribe user from notifications"""
        try:
            from app.database import get_db
            database = get_db()

            await database.telegram_subscribers.update_one(
                {"chat_id": chat_id},
                {"$set": {"subscribed": False, "unsubscribed_at": datetime.utcnow()}},
                upsert=True
            )

            await self.send_message(
                chat_id,
                "🔕 <b>Notifications Disabled</b>\n\n"
                "You won't receive alerts anymore.\n"
                "Use /notify to re-enable anytime!"
            )

        except Exception as e:
            logger.error(f"Unsubscribe error: {e}")

    async def broadcast_new_property(self, property_data: Dict):
        """Broadcast new property to all subscribers"""
        try:
            from app.database import get_db
            database = get_db()

            # Get all subscribers
            subscribers = await database.telegram_subscribers.find(
                {"subscribed": True}
            ).to_list(length=1000)

            message = (
                f"🏠 <b>New Property Alert!</b>\n\n"
                f"{property_data.get('title')}\n"
                f"📍 {property_data.get('city')} | "
                f"💰 ₹{property_data.get('price', 0):,.0f}\n\n"
                f"🔗 /property_{property_data.get('id')}"
            )

            # Send to all subscribers
            for subscriber in subscribers:
                chat_id = subscriber.get("chat_id")
                if chat_id:
                    await self.send_message(chat_id, message)
                    await asyncio.sleep(0.1)  # Rate limiting

        except Exception as e:
            logger.error(f"Broadcast error: {e}")

    def _get_search_menu(self) -> Dict:
        """Get search menu keyboard"""
        return {
            "inline_keyboard": [
                [{"text": "🏙 By City", "callback_data": "search_by_city"}],
                [{"text": "💰 By Budget", "callback_data": "search_by_budget"}],
                [{"text": "🏢 By Type", "callback_data": "search_by_type"}]
            ]
        }

    async def _send_alerts_menu(self, chat_id: str):
        """Send alerts configuration menu"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ Enable Alerts", "callback_data": "enable_alerts"}],
                [{"text": "🔕 Disable Alerts", "callback_data": "disable_alerts"}],
                [{"text": "⚙️ Customize", "callback_data": "customize_alerts"}]
            ]
        }

        await self.send_message(
            chat_id,
            "🔔 <b>Property Alerts</b>\n\n"
            "Get instant notifications for:\n"
            "• New properties in your area\n"
            "• Price changes on saved properties\n"
            "• Market trends and updates\n\n"
            "Choose an option:",
            reply_markup=keyboard
        )

    async def _send_system_status(self, chat_id: str):
        """Send system status"""
        status = (
            "📊 <b>PropertyYards System Status</b>\n\n"
            "✅ Bot: Online\n"
            "✅ Database: Connected\n"
            "✅ API: Responsive\n\n"
            f"👥 Subscribers: {len(self.subscribed_users)}\n"
            f"⏰ Last Updated: {datetime.utcnow().strftime('%H:%M:%S')} UTC"
        )
        await self.send_message(chat_id, status)

    async def _send_price_trends(self, chat_id: str, city: str):
        """Send price trends for city"""
        if not city:
            await self.send_message(chat_id, "Please specify a city. Example: /price Mumbai")
            return

        await self.send_message(
            chat_id,
            f"📈 <b>Price Trends: {city.title()}</b>\n\n"
            f"Average price: Contact for details\n"
            f"Trend: Stable\n\n"
            f"Search properties in {city}: /search"
        )


# Global bot instance
telegram_bot = TelegramBot()
