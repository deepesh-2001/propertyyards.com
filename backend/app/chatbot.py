"""
Chat Bot Module
AI-powered chat bot for property assistance
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import re

logger = logging.getLogger(__name__)


class IntentType(str, Enum):
    """Types of user intents"""
    PROPERTY_SEARCH = "property_search"
    PROPERTY_DETAILS = "property_details"
    PRICE_INQUIRY = "price_inquiry"
    CONTACT_BROKER = "contact_broker"
    SCHEDULE_VIEWING = "schedule_viewing"
    GENERAL_INFO = "general_info"
    UNKNOWN = "unknown"


class ChatBot:
    """AI-powered chat bot for property assistance"""
    
    def __init__(self, database):
        self.db = database
    
    def detect_intent(self, message: str) -> IntentType:
        """Detect user intent from message"""
        message_lower = message.lower()
        
        # Property search intent
        if any(keyword in message_lower for keyword in ['search', 'find', 'looking for', 'show me', 'properties', 'homes', 'apartments']):
            return IntentType.PROPERTY_SEARCH
        
        # Property details intent
        if any(keyword in message_lower for keyword in ['details', 'more info', 'tell me about', 'information about']):
            return IntentType.PROPERTY_DETAILS
        
        # Price inquiry intent
        if any(keyword in message_lower for keyword in ['price', 'cost', 'how much', 'rent', 'buy']):
            return IntentType.PRICE_INQUIRY
        
        # Contact broker intent
        if any(keyword in message_lower for keyword in ['contact', 'call', 'email', 'broker', 'agent', 'reach']):
            return IntentType.CONTACT_BROKER
        
        # Schedule viewing intent
        if any(keyword in message_lower for keyword in ['schedule', 'visit', 'viewing', 'see', 'tour']):
            return IntentType.SCHEDULE_VIEWING
        
        # General info intent
        return IntentType.GENERAL_INFO
    
    def extract_entities(self, message: str) -> Dict[str, Any]:
        """Extract entities from user message"""
        entities = {}
        message_lower = message.lower()
        
        # Extract price range
        price_pattern = r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+)(?:\s*(?:to|-|and)\s*\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?|\d+))?'
        price_matches = re.findall(price_pattern, message)
        if price_matches:
            entities['price_range'] = price_matches
        
        # Extract location
        location_keywords = ['in', 'at', 'near', 'around']
        for keyword in location_keywords:
            if keyword in message_lower:
                idx = message_lower.index(keyword)
                location = message[idx + len(keyword):].strip()
                entities['location'] = location
                break
        
        # Extract property type
        property_types = ['apartment', 'house', 'condo', 'townhouse', 'commercial']
        for prop_type in property_types:
            if prop_type in message_lower:
                entities['property_type'] = prop_type
                break
        
        # Extract bedrooms
        bedroom_pattern = r'(\d+)\s*(?:bedroom|bed|br)'
        bedroom_matches = re.findall(bedroom_pattern, message_lower)
        if bedroom_matches:
            entities['bedrooms'] = int(bedroom_matches[0])
        
        # Extract rental vs sale
        if 'rent' in message_lower or 'rental' in message_lower:
            entities['listing_type'] = 'rent'
        elif 'buy' in message_lower or 'sale' in message_lower or 'purchase' in message_lower:
            entities['listing_type'] = 'sale'
        
        return entities
    
    async def generate_response(
        self,
        message: str,
        session_id: str,
        user_id: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate chat bot response"""
        intent = self.detect_intent(message)
        entities = self.extract_entities(message)
        
        # Get conversation history
        conversation = await self.db.chat_conversations.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not conversation:
            # Create new conversation
            conversation_data = {
                "user_id": user_id,
                "session_id": session_id,
                "messages": [],
                "context": context or {},
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            await self.db.chat_conversations.insert_one(conversation_data)
            conversation = conversation_data
        
        # Add user message to conversation
        await self.db.chat_conversations.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$push": {
                    "messages": {
                        "role": "user",
                        "content": message,
                        "timestamp": datetime.utcnow()
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        # Generate response based on intent
        response = await self._generate_intent_response(intent, entities, context)
        
        # Add bot response to conversation
        await self.db.chat_conversations.update_one(
            {"session_id": session_id, "user_id": user_id},
            {
                "$push": {
                    "messages": {
                        "role": "assistant",
                        "content": response["message"],
                        "timestamp": datetime.utcnow()
                    }
                },
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "message": response["message"],
            "session_id": session_id,
            "context": entities,
            "intent": intent,
            "suggestions": response.get("suggestions", [])
        }
    
    async def _generate_intent_response(
        self,
        intent: IntentType,
        entities: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response based on intent"""
        
        if intent == IntentType.PROPERTY_SEARCH:
            return self._generate_search_response(entities)
        
        elif intent == IntentType.PROPERTY_DETAILS:
            return self._generate_details_response(entities)
        
        elif intent == IntentType.PRICE_INQUIRY:
            return self._generate_price_response(entities)
        
        elif intent == IntentType.CONTACT_BROKER:
            return self._generate_contact_response(entities)
        
        elif intent == IntentType.SCHEDULE_VIEWING:
            return self._generate_viewing_response(entities)
        
        else:
            return self._generate_general_response()
    
    def _generate_search_response(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate property search response"""
        response = "I can help you search for properties! "
        
        if entities.get('location'):
            response += f"You're looking for properties in {entities['location']}. "
        
        if entities.get('property_type'):
            response += f"Specifically {entities['property_type']}s. "
        
        if entities.get('bedrooms'):
            response += f"With {entities['bedrooms']} bedrooms. "
        
        if entities.get('listing_type') == 'rent':
            response += "For rental. "
        elif entities.get('listing_type') == 'sale':
            response += "For purchase. "
        
        response += "Would you like me to show you available properties matching your criteria?"
        
        return {
            "message": response,
            "suggestions": [
                "Yes, show me properties",
                "Refine my search",
                "Tell me about rental options",
                "What's the price range?"
            ]
        }
    
    def _generate_details_response(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate property details response"""
        return {
            "message": "I'd be happy to provide more details about a property. Could you please specify which property you're interested in? You can share the property ID or title.",
            "suggestions": [
                "Search for properties first",
                "I have a property ID",
                "Show me featured properties"
            ]
        }
    
    def _generate_price_response(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate price inquiry response"""
        response = "Pricing depends on various factors like location, property type, and amenities. "
        
        if entities.get('listing_type') == 'rent':
            response += "For rentals, prices typically range from $1,000 to $5,000 per month depending on the property. "
        elif entities.get('listing_type') == 'sale':
            response += "For purchases, prices can range from $100,000 to over $1,000,000. "
        
        response += "Would you like me to help you find properties within your budget?"
        
        return {
            "message": response,
            "suggestions": [
                "Show me properties under $2000/month",
                "Show me properties under $300,000",
                "What affects property prices?"
            ]
        }
    
    def _generate_contact_response(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate contact broker response"""
        return {
            "message": "I can help you contact a broker! Please let me know which property you're interested in, and I'll provide you with the broker's contact information. You can also reach our support team at +1-800-PROPERTY.",
            "suggestions": [
                "I want to contact a broker for a specific property",
                "Call support team",
                "Schedule a callback"
            ]
        }
    
    def _generate_viewing_response(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Generate viewing schedule response"""
        return {
            "message": "I'd be happy to help you schedule a property viewing! Please let me know which property you'd like to visit and your preferred date and time. Our team will confirm the appointment with you.",
            "suggestions": [
                "Schedule for tomorrow",
                "Schedule for this weekend",
                "I need to choose a property first"
            ]
        }
    
    def _generate_general_response(self) -> Dict[str, Any]:
        """Generate general response"""
        return {
            "message": "Hello! I'm your PropertyYards assistant. I can help you with:\n\n• Finding properties for sale or rent\n• Getting property details\n• Contacting brokers\n• Scheduling viewings\n• Price information\n\nHow can I assist you today?",
            "suggestions": [
                "Search for properties",
                "Tell me about rental options",
                "Contact a broker",
                "Schedule a viewing"
            ]
        }
    
    async def get_conversation_history(
        self,
        session_id: str,
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get conversation history"""
        conversation = await self.db.chat_conversations.find_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        if not conversation:
            return []
        
        return conversation.get("messages", [])
    
    async def clear_conversation(
        self,
        session_id: str,
        user_id: str
    ) -> bool:
        """Clear conversation history"""
        result = await self.db.chat_conversations.delete_one({
            "session_id": session_id,
            "user_id": user_id
        })
        
        return result.deleted_count > 0


class PropertySearchBot:
    """Specialized bot for property search"""
    
    def __init__(self, database):
        self.db = database
    
    async def search_properties(
        self,
        query: str,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """Search properties based on natural language query"""
        query_filter = {}
        
        # Parse query for filters
        query_lower = query.lower()
        
        # Location filter
        if 'in' in query_lower:
            location_idx = query_lower.index('in')
            location = query[location_idx + 3:].strip()
            query_filter["$or"] = [
                {"city": {"$regex": location, "$options": "i"}},
                {"location": {"$regex": location, "$options": "i"}},
                {"state": {"$regex": location, "$options": "i"}}
            ]
        
        # Property type filter
        property_types = ['apartment', 'house', 'condo', 'townhouse', 'commercial']
        for prop_type in property_types:
            if prop_type in query_lower:
                query_filter["property_type"] = prop_type
                break
        
        # Listing type filter
        if 'rent' in query_lower or 'rental' in query_lower:
            query_filter["listing_type"] = "rent"
        elif 'buy' in query_lower or 'sale' in query_lower:
            query_filter["listing_type"] = "sale"
        
        # Apply additional filters
        if filters:
            for key, value in filters.items():
                query_filter[key] = value
        
        # Search
        cursor = self.db.properties.find(query_filter).limit(10)
        properties = await cursor.to_list(length=10)
        
        for prop in properties:
            prop["id"] = str(prop["_id"])
            del prop["_id"]
        
        return properties
