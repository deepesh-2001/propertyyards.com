"""
News Article Service
Fetches real estate news and generates AI-powered articles for PropertyYards
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import aiohttp
import feedparser
import json

logger = logging.getLogger(__name__)


class ArticleStatus(Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SCHEDULED = "scheduled"
    ARCHIVED = "archived"


class ArticleCategory(Enum):
    MARKET_TRENDS = "market_trends"
    PROPERTY_NEWS = "property_news"
    INVESTMENT = "investment"
    LEGAL = "legal"
    LIFESTYLE = "lifestyle"
    TECHNOLOGY = "technology"
    INTERVIEW = "interview"


@dataclass
class NewsArticle:
    """News article data structure"""
    id: str
    title: str
    content: str
    summary: str
    author: str
    category: ArticleCategory
    status: ArticleStatus
    tags: List[str] = field(default_factory=list)
    featured_image: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    views: int = 0
    likes: int = 0
    seo_meta: Dict[str, str] = field(default_factory=dict)
    original_source: Optional[str] = None
    is_ai_generated: bool = False


class NewsFetcher:
    """Fetches real estate news from various sources"""

    def __init__(self):
        self.sources = {
            "reuters": "https://www.reuters.com/real-estate/rss",
            "economic_times": "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
            "business_standard": "https://www.business-standard.com/rss/real-estate-106.rss",
            "moneycontrol": "https://www.moneycontrol.com/rss/real-estate.xml",
            "housing": "https://housing.com/news/feed"
        }
        self.session = None

    async def initialize(self):
        """Initialize HTTP session"""
        self.session = aiohttp.ClientSession()

    async def fetch_from_rss(self, source_name: str, rss_url: str) -> List[Dict[str, Any]]:
        """Fetch news from RSS feed"""
        try:
            async with self.session.get(rss_url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status == 200:
                    content = await response.text()
                    feed = feedparser.parse(content)

                    articles = []
                    for entry in feed.entries[:10]:  # Top 10 articles
                        articles.append({
                            "source": source_name,
                            "title": entry.get("title", ""),
                            "link": entry.get("link", ""),
                            "published": entry.get("published", ""),
                            "summary": entry.get("summary", ""),
                            "content": entry.get("description", entry.get("summary", ""))
                        })

                    return articles
                else:
                    logger.warning(f"Failed to fetch from {source_name}: {response.status}")
                    return []

        except Exception as e:
            logger.error(f"RSS fetch error for {source_name}: {e}")
            return []

    async def fetch_all_sources(self) -> List[Dict[str, Any]]:
        """Fetch news from all configured sources"""
        all_articles = []

        tasks = [
            self.fetch_from_rss(name, url)
            for name, url in self.sources.items()
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_articles.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Source fetch error: {result}")

        # Sort by published date
        all_articles.sort(
            key=lambda x: x.get("published", ""),
            reverse=True
        )

        return all_articles

    async def close(self):
        """Close HTTP session"""
        if self.session:
            await self.session.close()


class AIArticleGenerator:
    """Generates AI-powered real estate articles"""

    def __init__(self):
        self.api_key = None
        self.api_endpoint = "https://api.openai.com/v1/chat/completions"
        self.author_name = "PropertyYards Editorial Team"

    async def initialize(self, api_key: str, author_name: str = "PropertyYards Team"):
        """Initialize with API key and author name"""
        self.api_key = api_key
        self.author_name = author_name
        logger.info("AI Article Generator initialized")

    async def generate_article(
        self,
        topic: str,
        category: ArticleCategory,
        keywords: List[str],
        tone: str = "professional",
        word_count: int = 800
    ) -> Optional[NewsArticle]:
        """Generate AI article on real estate topic"""
        if not self.api_key:
            logger.warning("No API key for AI article generation")
            return None

        try:
            prompt = self._build_generation_prompt(topic, category, keywords, tone, word_count)

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "gpt-4",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a professional real estate content writer for PropertyYards, India's leading property platform."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        generated_text = data['choices'][0]['message']['content']

                        # Parse generated content
                        article_data = self._parse_generated_content(generated_text, topic, category)

                        return NewsArticle(
                            id=f"article_{datetime.utcnow().timestamp()}",
                            title=article_data['title'],
                            content=article_data['content'],
                            summary=article_data['summary'],
                            author=self.author_name,
                            category=category,
                            status=ArticleStatus.DRAFT,
                            tags=keywords,
                            seo_meta=article_data.get('seo_meta', {}),
                            is_ai_generated=True
                        )
                    else:
                        error_text = await response.text()
                        logger.error(f"Article generation failed: {error_text}")
                        return None

        except Exception as e:
            logger.error(f"Article generation error: {e}")
            return None

    def _build_generation_prompt(
        self,
        topic: str,
        category: ArticleCategory,
        keywords: List[str],
        tone: str,
        word_count: int
    ) -> str:
        """Build prompt for article generation"""

        category_prompts = {
            ArticleCategory.MARKET_TRENDS: (
                f"Write a comprehensive real estate market analysis article about {topic}. "
                f"Include current trends, price movements, and expert insights. "
            ),
            ArticleCategory.PROPERTY_NEWS: (
                f"Write a news article about {topic} in the real estate sector. "
                f"Cover recent developments, project launches, and market impact. "
            ),
            ArticleCategory.INVESTMENT: (
                f"Write an investment guide about {topic}. "
                f"Include ROI analysis, risk factors, and expert recommendations. "
            ),
            ArticleCategory.LEGAL: (
                f"Write a legal guide about {topic} in real estate. "
                f"Explain regulations, compliance requirements, and important considerations. "
            ),
            ArticleCategory.LIFESTYLE: (
                f"Write a lifestyle article about {topic} in real estate. "
                f"Focus on living experiences, amenities, and community aspects. "
            ),
            ArticleCategory.TECHNOLOGY: (
                f"Write about technology trends in real estate related to {topic}. "
                f"Cover smart homes, proptech innovations, and future developments. "
            ),
            ArticleCategory.INTERVIEW: (
                f"Create an interview-style article with industry experts about {topic}. "
                f"Include insights, predictions, and professional opinions. "
            )
        }

        base_prompt = category_prompts.get(category, category_prompts[ArticleCategory.PROPERTY_NEWS])

        prompt = (
            f"{base_prompt}\n\n"
            f"Tone: {tone}\n"
            f"Target length: {word_count} words\n"
            f"Keywords to include: {', '.join(keywords)}\n\n"
            f"Requirements:\n"
            f"1. Start with an engaging headline (prefix with 'TITLE: ')\n"
            f"2. Write a compelling summary (prefix with 'SUMMARY: ')\n"
            f"3. Main content should be well-structured with subheadings\n"
            f"4. Include SEO meta title and description (prefix with 'SEO_TITLE:' and 'SEO_DESC:')\n"
            f"5. Suggest 5 relevant tags (prefix with 'TAGS:')\n"
            f"6. End with a compelling conclusion\n"
            f"7. Include a call-to-action for PropertyYards\n\n"
            f"Format the output clearly with the prefixes for easy parsing."
        )

        return prompt

    def _parse_generated_content(self, text: str, topic: str, category: ArticleCategory) -> Dict[str, Any]:
        """Parse generated article content"""
        lines = text.split('\n')

        result = {
            'title': topic,
            'summary': '',
            'content': text,
            'seo_meta': {},
            'tags': []
        }

        current_section = None
        sections = {
            'TITLE': [],
            'SUMMARY': [],
            'SEO_TITLE': [],
            'SEO_DESC': [],
            'TAGS': [],
            'CONTENT': []
        }

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check for section headers
            if line.startswith('TITLE:'):
                current_section = 'TITLE'
                sections['TITLE'].append(line.replace('TITLE:', '').strip())
            elif line.startswith('SUMMARY:'):
                current_section = 'SUMMARY'
                sections['SUMMARY'].append(line.replace('SUMMARY:', '').strip())
            elif line.startswith('SEO_TITLE:'):
                current_section = 'SEO_TITLE'
                sections['SEO_TITLE'].append(line.replace('SEO_TITLE:', '').strip())
            elif line.startswith('SEO_DESC:'):
                current_section = 'SEO_DESC'
                sections['SEO_DESC'].append(line.replace('SEO_DESC:', '').strip())
            elif line.startswith('TAGS:'):
                current_section = 'TAGS'
                tags_text = line.replace('TAGS:', '').strip()
                sections['TAGS'].extend([t.strip() for t in tags_text.split(',')])
            elif current_section and current_section != 'CONTENT':
                sections[current_section].append(line)
            else:
                sections['CONTENT'].append(line)

        # Extract values
        if sections['TITLE']:
            result['title'] = ' '.join(sections['TITLE'])
        if sections['SUMMARY']:
            result['summary'] = ' '.join(sections['SUMMARY'])
        if sections['SEO_TITLE']:
            result['seo_meta']['title'] = ' '.join(sections['SEO_TITLE'])
        if sections['SEO_DESC']:
            result['seo_meta']['description'] = ' '.join(sections['SEO_DESC'])
        if sections['TAGS']:
            result['tags'] = [t for t in sections['TAGS'] if t]

        # Clean up content
        content_lines = [l for l in sections['CONTENT'] if not l.startswith(('TITLE:', 'SUMMARY:', 'SEO_', 'TAGS:'))]
        result['content'] = '\n\n'.join(content_lines)

        return result

    async def rewrite_for_propertyyards(
        self,
        original_article: Dict[str, Any],
        user_name: str
    ) -> Optional[NewsArticle]:
        """Rewrite external article with PropertyYards branding and user name"""
        try:
            prompt = (
                f"Rewrite the following real estate article for PropertyYards, "
                f"India's premier property platform. Make it engaging, professional, "
                f"and include insights from {user_name}, real estate expert at PropertyYards.\n\n"
                f"Original Title: {original_article.get('title', '')}\n"
                f"Original Content: {original_article.get('content', '')[:500]}...\n\n"
                f"Requirements:\n"
                f"1. New headline with PropertyYards branding\n"
                f"2. Include expert commentary from {user_name}\n"
                f"3. Add PropertyYards-specific insights\n"
                f"4. Mention relevant PropertyYards listings or features\n"
                f"5. Include call-to-action to visit PropertyYards\n"
                f"6. Format with TITLE:, SUMMARY:, and CONTENT: sections"
            )

            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }

                payload = {
                    "model": "gpt-4",
                    "messages": [
                        {"role": "system", "content": "You are a professional content editor for PropertyYards."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 2000
                }

                async with session.post(
                    self.api_endpoint,
                    headers=headers,
                    json=payload
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        generated_text = data['choices'][0]['message']['content']

                        article_data = self._parse_generated_content(
                            generated_text,
                            original_article.get('title', ''),
                            ArticleCategory.PROPERTY_NEWS
                        )

                        return NewsArticle(
                            id=f"article_{datetime.utcnow().timestamp()}",
                            title=article_data['title'],
                            content=article_data['content'],
                            summary=article_data['summary'],
                            author=f"{user_name} | PropertyYards",
                            category=ArticleCategory.PROPERTY_NEWS,
                            status=ArticleStatus.DRAFT,
                            tags=article_data.get('tags', ['property', 'realestate']),
                            original_source=original_article.get('link'),
                            is_ai_generated=True
                        )

        except Exception as e:
            logger.error(f"Rewrite error: {e}")
            return None


class NewsArticleManager:
    """Manages news articles in database"""

    def __init__(self):
        self.collection_name = "news_articles"

    async def create_article(
        self,
        article: NewsArticle,
        database
    ) -> str:
        """Create new article in database"""
        try:
            doc = {
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "summary": article.summary,
                "author": article.author,
                "category": article.category.value,
                "status": article.status.value,
                "tags": article.tags,
                "featured_image": article.featured_image,
                "created_at": article.created_at,
                "published_at": article.published_at,
                "views": article.views,
                "likes": article.likes,
                "seo_meta": article.seo_meta,
                "original_source": article.original_source,
                "is_ai_generated": article.is_ai_generated
            }

            await database[self.collection_name].insert_one(doc)
            logger.info(f"Article created: {article.title[:50]}...")
            return article.id

        except Exception as e:
            logger.error(f"Create article error: {e}")
            return None

    async def get_article(self, article_id: str, database) -> Optional[NewsArticle]:
        """Get article by ID"""
        try:
            doc = await database[self.collection_name].find_one({"id": article_id})
            if doc:
                return self._doc_to_article(doc)
            return None
        except Exception as e:
            logger.error(f"Get article error: {e}")
            return None

    async def get_articles(
        self,
        database,
        category: Optional[ArticleCategory] = None,
        status: Optional[ArticleStatus] = None,
        limit: int = 20,
        skip: int = 0
    ) -> List[NewsArticle]:
        """Get articles with filters"""
        try:
            query = {}
            if category:
                query["category"] = category.value
            if status:
                query["status"] = status.value

            cursor = database[self.collection_name].find(query).sort("created_at", -1).skip(skip).limit(limit)
            docs = await cursor.to_list(length=limit)

            return [self._doc_to_article(doc) for doc in docs]

        except Exception as e:
            logger.error(f"Get articles error: {e}")
            return []

    async def update_article(
        self,
        article_id: str,
        updates: Dict[str, Any],
        database
    ) -> bool:
        """Update article"""
        try:
            result = await database[self.collection_name].update_one(
                {"id": article_id},
                {"$set": updates}
            )
            return result.modified_count > 0
        except Exception as e:
            logger.error(f"Update article error: {e}")
            return False

    async def publish_article(self, article_id: str, database) -> bool:
        """Publish article"""
        return await self.update_article(
            article_id,
            {
                "status": ArticleStatus.PUBLISHED.value,
                "published_at": datetime.utcnow()
            },
            database
        )

    async def delete_article(self, article_id: str, database) -> bool:
        """Delete article"""
        try:
            result = await database[self.collection_name].delete_one({"id": article_id})
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Delete article error: {e}")
            return False

    def _doc_to_article(self, doc: Dict) -> NewsArticle:
        """Convert document to NewsArticle"""
        return NewsArticle(
            id=doc["id"],
            title=doc["title"],
            content=doc["content"],
            summary=doc.get("summary", ""),
            author=doc.get("author", "PropertyYards"),
            category=ArticleCategory(doc.get("category", "property_news")),
            status=ArticleStatus(doc.get("status", "draft")),
            tags=doc.get("tags", []),
            featured_image=doc.get("featured_image"),
            created_at=doc.get("created_at", datetime.utcnow()),
            published_at=doc.get("published_at"),
            views=doc.get("views", 0),
            likes=doc.get("likes", 0),
            seo_meta=doc.get("seo_meta", {}),
            original_source=doc.get("original_source"),
            is_ai_generated=doc.get("is_ai_generated", False)
        )


# Global instances
news_fetcher = NewsFetcher()
ai_article_generator = AIArticleGenerator()
article_manager = NewsArticleManager()
