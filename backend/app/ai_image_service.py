"""
AI Image Generation Service
Generates property images, market visualizations, and social media content
"""
import asyncio
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import dataclass
import aiohttp
import base64
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class GeneratedImage:
    """Generated image metadata"""
    id: str
    prompt: str
    image_data: bytes
    created_at: datetime
    image_type: str  # 'property', 'market', 'social', 'future'
    metadata: Dict[str, Any]


class AIImageGenerator:
    """AI Image generation using external APIs (DALL-E, Stable Diffusion, etc.)"""

    def __init__(self):
        self.api_key = None  # Set from config
        self.api_endpoint = "https://api.openai.com/v1/images/generations"
        self.fallback_enabled = True
        self.generation_queue = asyncio.Queue()
        self.is_processing = False

    async def initialize(self, api_key: str):
        """Initialize with API key"""
        self.api_key = api_key
        logger.info("AI Image Generator initialized")

    async def generate_property_visualization(
        self,
        property_data: Dict[str, Any],
        style: str = "modern",
        size: str = "1024x1024"
    ) -> Optional[GeneratedImage]:
        """Generate AI property visualization"""
        prompt = self._build_property_prompt(property_data, style)
        return await self._generate_image(prompt, "property", property_data, size)

    async def generate_market_visualization(
        self,
        market_data: Dict[str, Any],
        chart_type: str = "trend"
    ) -> Optional[GeneratedImage]:
        """Generate market trend visualization"""
        prompt = self._build_market_prompt(market_data, chart_type)
        return await self._generate_image(prompt, "market", market_data)

    async def generate_future_prediction_visual(
        self,
        prediction_data: Dict[str, Any],
        property_type: str = "apartment"
    ) -> Optional[GeneratedImage]:
        """Generate future prediction visualization"""
        prompt = self._build_future_prompt(prediction_data, property_type)
        return await self._generate_image(prompt, "future", prediction_data)

    async def generate_social_media_image(
        self,
        content_type: str,
        text: str,
        theme: str = "professional"
    ) -> Optional[GeneratedImage]:
        """Generate social media post image"""
        prompt = self._build_social_prompt(content_type, text, theme)
        return await self._generate_image(prompt, "social", {"content_type": content_type, "text": text})

    def _build_property_prompt(self, property_data: Dict, style: str) -> str:
        """Build prompt for property visualization"""
        property_type = property_data.get('property_type', 'apartment')
        bedrooms = property_data.get('bedrooms', 2)
        location = property_data.get('city', 'modern city')
        price_range = property_data.get('price_category', 'luxury')

        prompts = {
            'modern': f"Ultra-modern {property_type} with {bedrooms} bedrooms, {price_range} style, "
                     f"located in {location}, architectural photography, golden hour lighting, "
                     f"high-end real estate listing photo, 4K, photorealistic",

            'classic': f"Elegant classic {property_type} in {location}, traditional architecture, "
                      f"beautiful landscaping, professional real estate photography, warm lighting",

            'minimalist': f"Minimalist modern {property_type}, clean lines, white interiors, "
                        f"{location} backdrop, Scandinavian design, architectural digest style"
        }

        return prompts.get(style, prompts['modern'])

    def _build_market_prompt(self, market_data: Dict, chart_type: str) -> str:
        """Build prompt for market visualization"""
        city = market_data.get('city', 'city')
        trend = market_data.get('trend', 'growing')

        if chart_type == 'trend':
            return f"Beautiful infographic showing real estate market {trend} in {city}, "
                   f"modern data visualization, upward trending graph, property icons, "
                   f"professional business graphic, clean design, blue and green colors"

        elif chart_type == 'comparison':
            return f"Real estate price comparison chart for different neighborhoods in {city}, "
                   f"colorful bar chart style, modern infographic design, professional"

        return f"Real estate market data visualization for {city}, modern infographic style"

    def _build_future_prompt(self, prediction_data: Dict, property_type: str) -> str:
        """Build prompt for future prediction"""
        location = prediction_data.get('location', 'smart city')
        year = prediction_data.get('year', 2030)
        growth = prediction_data.get('growth_rate', 15)

        return f"Futuristic {property_type} complex in {location} year {year}, "
               f"showing {growth}% growth and development, modern architecture, "
               f"smart city features, sustainable design, aerial view, "
               f"architectural visualization, vibrant colors"

    def _build_social_prompt(self, content_type: str, text: str, theme: str) -> str:
        """Build prompt for social media"""
        prompts = {
            'new_property': f"Eye-catching real estate Instagram post, new listing announcement, "
                          f"{text}, modern house photo background, professional graphic design, "
                          f"engaging layout, warm colors",

            'market_update': f"Professional LinkedIn style market update graphic, "
                           f"{text}, real estate market theme, data visualization elements, "
                           f"corporate design, blue and white",

            'promotion': f"Promotional real estate banner, {text}, attention-grabbing design, "
                        f"sale/campaign style, vibrant colors, call-to-action elements",

            'tip': f"Real estate tip social media card, {text}, educational infographic style, "
                  f"clean layout, helpful and professional"
        }

        return prompts.get(content_type, f"Real estate social media graphic: {text}")

    async def _generate_image(
        self,
        prompt: str,
        image_type: str,
        metadata: Dict,
        size: str = "1024x1024"
    ) -> Optional[GeneratedImage]:
        """Generate image using AI API"""
        if not self.api_key:
            logger.warning("No API key configured for image generation")
            return None

        try:
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "dall-e-3",
                    "prompt": prompt,
                    "n": 1,
                    "size": size,
                    "response_format": "b64_json"
                }

                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        image_b64 = data['data'][0]['b64_json']
                        image_data = base64.b64decode(image_b64)

                        return GeneratedImage(
                            id=f"img_{datetime.utcnow().timestamp()}",
                            prompt=prompt,
                            image_data=image_data,
                            created_at=datetime.utcnow(),
                            image_type=image_type,
                            metadata=metadata
                        )
                    else:
                        logger.error(f"Image generation failed: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Image generation error: {e}")
            return None

    async def queue_generation(self, task: Dict[str, Any]):
        """Queue image generation task for idle processing"""
        await self.generation_queue.put(task)
        logger.info(f"Image generation task queued: {task.get('type')}")

    async def process_queue_during_idle(self, max_concurrent: int = 2):
        """Process queued image generation during idle time"""
        if self.is_processing:
            return

        self.is_processing = True
        tasks = []

        try:
            while not self.generation_queue.empty() and len(tasks) < max_concurrent:
                task = await self.generation_queue.get()

                if task['type'] == 'property':
                    coro = self.generate_property_visualization(
                        task['data'], task.get('style', 'modern')
                    )
                elif task['type'] == 'market':
                    coro = self.generate_market_visualization(
                        task['data'], task.get('chart_type', 'trend')
                    )
                elif task['type'] == 'future':
                    coro = self.generate_future_prediction_visual(
                        task['data'], task.get('property_type', 'apartment')
                    )
                elif task['type'] == 'social':
                    coro = self.generate_social_media_image(
                        task['content_type'], task['text'], task.get('theme', 'professional')
                    )
                else:
                    continue

                tasks.append(asyncio.create_task(coro))

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                successful = sum(1 for r in results if isinstance(r, GeneratedImage))
                logger.info(f"Generated {successful}/{len(tasks)} images during idle time")

        finally:
            self.is_processing = False


class ImageCacheManager:
    """Manages cached AI-generated images"""

    def __init__(self):
        self.cache_prefix = "ai_image:"
        self.max_cache_size = 1000

    async def store_image(self, image: GeneratedImage, database) -> str:
        """Store generated image to database and cache"""
        try:
            # Store in database
            image_doc = {
                "id": image.id,
                "prompt": image.prompt,
                "image_type": image.image_type,
                "created_at": image.created_at,
                "metadata": image.metadata,
                "image_data": base64.b64encode(image.image_data).decode('utf-8')
            }

            await database.ai_images.insert_one(image_doc)

            # Cache metadata
            cache_key = f"{self.cache_prefix}{image.id}"
            from app.cache import set_in_cache
            await set_in_cache(cache_key, image_doc, ttl=86400)

            return image.id

        except Exception as e:
            logger.error(f"Image store error: {e}")
            return None

    async def get_image(self, image_id: str, database) -> Optional[GeneratedImage]:
        """Retrieve generated image"""
        try:
            # Check cache first
            from app.cache import get_from_cache
            cache_key = f"{self.cache_prefix}{image_id}"
            cached = await get_from_cache(cache_key)

            if cached:
                return self._doc_to_image(cached)

            # Fetch from database
            doc = await database.ai_images.find_one({"id": image_id})
            if doc:
                return self._doc_to_image(doc)

            return None

        except Exception as e:
            logger.error(f"Image retrieval error: {e}")
            return None

    def _doc_to_image(self, doc: Dict) -> GeneratedImage:
        """Convert document to GeneratedImage"""
        return GeneratedImage(
            id=doc["id"],
            prompt=doc["prompt"],
            image_data=base64.b64decode(doc["image_data"]),
            created_at=doc["created_at"],
            image_type=doc["image_type"],
            metadata=doc.get("metadata", {})
        )


# Global instances
ai_image_generator = AIImageGenerator()
image_cache_manager = ImageCacheManager()
