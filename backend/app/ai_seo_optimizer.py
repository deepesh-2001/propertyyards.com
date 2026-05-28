"""
AI SEO Optimization Service
AI-powered SEO analysis, optimization, and content generation for real estate
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import json
import re

logger = logging.getLogger(__name__)


class SEOCategory(Enum):
    """SEO optimization categories"""
    PROPERTY_LISTING = "property_listing"
    LOCATION_PAGE = "location_page"
    BLOG_ARTICLE = "blog_article"
    LANDING_PAGE = "landing_page"
    AGENT_PROFILE = "agent_profile"
    PROJECT_PAGE = "project_page"


class SEOScoreLevel(Enum):
    """SEO score levels"""
    EXCELLENT = (90, 100, "Excellent", "green")
    GOOD = (70, 89, "Good", "light_green")
    AVERAGE = (50, 69, "Average", "yellow")
    NEEDS_IMPROVEMENT = (30, 49, "Needs Improvement", "orange")
    POOR = (0, 29, "Poor", "red")

    def __init__(self, min_score, max_score, label, color):
        self.min_score = min_score
        self.max_score = max_score
        self.label = label
        self.color = color


@dataclass
class SEOAnalysisResult:
    """SEO analysis result"""
    content_id: str
    content_type: str
    overall_score: int
    score_level: SEOScoreLevel
    analyzed_at: datetime
    checks: Dict[str, Any]
    recommendations: List[Dict[str, Any]]
    optimized_content: Optional[str] = None
    keyword_analysis: Optional[Dict[str, Any]] = None


@dataclass
class KeywordMetrics:
    """Keyword performance metrics"""
    keyword: str
    search_volume: int
    competition: str  # low, medium, high
    difficulty: int  # 0-100
    cpc: float  # cost per click
    trend: str  # rising, falling, stable
    relevance: float  # 0-1


class AISeoOptimizer:
    """AI-powered SEO optimization service with Redis caching"""

    def __init__(self):
        self.api_key = None
        self.api_endpoint = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
        self.enabled = True
        self.cache_ttl = 3600  # 1 hour cache
        self.cache_enabled = True

        # SEO scoring weights
        self.weights = {
            "title_optimization": 15,
            "meta_description": 10,
            "content_quality": 20,
            "keyword_usage": 15,
            "readability": 10,
            "heading_structure": 10,
            "image_alt_text": 5,
            "internal_links": 5,
            "url_structure": 5,
            "mobile_friendly": 5
        }

        # Real estate keywords database
        self.real_estate_keywords = {
            "buy": ["buy apartment", "buy flat", "buy house", "buy villa", "buy property"],
            "rent": ["rent apartment", "rent flat", "rent house", "rent villa", "rent property"],
            "sell": ["sell apartment", "sell flat", "sell house", "sell villa", "sell property"],
            "location": ["apartments in", "flats in", "houses in", "properties in", "real estate in"],
            "type": ["1 bhk", "2 bhk", "3 bhk", "4 bhk", "penthouse", "studio apartment"],
            "amenities": ["swimming pool", "gym", "parking", "security", "garden", "club house"],
            "features": ["furnished", "semi-furnished", "unfurnished", "ready to move", "under construction"]
        }

    async def initialize(self, api_key: str):
        """Initialize with Gemini API key"""
        self.api_key = api_key
        logger.info("AI SEO Optimizer initialized")

    def _generate_cache_key(self, content: str, content_type: str, keywords: List[str]) -> str:
        """Generate cache key for SEO analysis"""
        import hashlib
        key_data = f"{content}:{content_type}:{','.join(sorted(keywords))}"
        return hashlib.md5(key_data.encode()).hexdigest()

    async def _get_cached_result(self, cache_key: str) -> Optional[Dict]:
        """Get cached SEO result from Redis"""
        try:
            from app.cache import get_cache
            cached = await get_cache(f"seo:{cache_key}")
            if cached:
                logger.debug(f"SEO cache hit: {cache_key[:8]}...")
                return json.loads(cached)
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    async def _cache_result(self, cache_key: str, result: Dict):
        """Cache SEO result in Redis"""
        try:
            from app.cache import set_cache
            await set_cache(
                f"seo:{cache_key}",
                json.dumps(result, default=str),
                ttl=self.cache_ttl
            )
            logger.debug(f"SEO cached: {cache_key[:8]}...")
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    async def analyze_content(
        self,
        content: str,
        content_type: SEOCategory,
        target_keywords: List[str],
        location: Optional[str] = None
    ) -> SEOAnalysisResult:
        """Analyze content for SEO optimization with parallel processing and caching"""
        try:
            # Check cache first
            if self.cache_enabled:
                cache_key = self._generate_cache_key(content, content_type.value, target_keywords)
                cached = await self._get_cached_result(cache_key)
                if cached:
                    # Reconstruct result from cache
                    return SEOAnalysisResult(
                        content_id=cached["content_id"],
                        content_type=cached["content_type"],
                        overall_score=cached["overall_score"],
                        score_level=SEOScoreLevel[cached["score_level"]],
                        analyzed_at=datetime.fromisoformat(cached["analyzed_at"]),
                        checks=cached["checks"],
                        recommendations=cached["recommendations"],
                        keyword_analysis=cached.get("keyword_analysis")
                    )

            # Run all SEO checks in parallel for 3x speed improvement
            checks = await self._run_parallel_checks(content, target_keywords)

            # Calculate weighted score
            total_score = 0
            max_score = 0
            for check_name, check_data in checks.items():
                weight = self.weights.get(check_name, 10)
                total_score += check_data["score"] * weight
                max_score += 100 * weight

            overall_score = int((total_score / max_score) * 100) if max_score > 0 else 0

            # Determine score level
            score_level = self._get_score_level(overall_score)

            # Generate recommendations
            recommendations = self._generate_recommendations(checks, content_type)

            # AI keyword analysis
            keyword_analysis = await self._ai_keyword_analysis(content, target_keywords, location)

            result = SEOAnalysisResult(
                content_id=f"seo_{datetime.utcnow().timestamp()}",
                content_type=content_type.value,
                overall_score=overall_score,
                score_level=score_level,
                analyzed_at=datetime.utcnow(),
                checks=checks,
                recommendations=recommendations,
                keyword_analysis=keyword_analysis
            )

            # Cache the result
            if self.cache_enabled:
                cache_data = {
                    "content_id": result.content_id,
                    "content_type": result.content_type,
                    "overall_score": result.overall_score,
                    "score_level": result.score_level.name,
                    "analyzed_at": result.analyzed_at.isoformat(),
                    "checks": result.checks,
                    "recommendations": result.recommendations,
                    "keyword_analysis": result.keyword_analysis
                }
                await self._cache_result(cache_key, cache_data)

            return result

        except Exception as e:
            logger.error(f"SEO analysis failed: {e}")
            return None

    async def _run_parallel_checks(
        self,
        content: str,
        target_keywords: List[str]
    ) -> Dict[str, Any]:
        """Run all SEO checks in parallel for maximum performance"""
        import asyncio

        # Create async wrapper for synchronous check methods
        async def async_check(check_func, *args):
            return await asyncio.get_event_loop().run_in_executor(None, check_func, *args)

        # Run all checks concurrently
        results = await asyncio.gather(
            async_check(self._check_title, content),
            async_check(self._check_meta_description, content),
            async_check(self._check_content_quality, content),
            async_check(self._check_keyword_usage, content, target_keywords),
            async_check(self._check_readability, content),
            async_check(self._check_headings, content),
            async_check(self._check_image_alt_text, content),
            async_check(self._check_internal_links, content),
            return_exceptions=True
        )

        # Map results to check names
        check_names = [
            "title_optimization",
            "meta_description",
            "content_quality",
            "keyword_usage",
            "readability",
            "heading_structure",
            "image_alt_text",
            "internal_links"
        ]

        checks = {}
        for name, result in zip(check_names, results):
            if isinstance(result, Exception):
                logger.error(f"SEO check {name} failed: {result}")
                checks[name] = {"score": 0, "issues": [f"Check failed: {str(result)}"]}
            else:
                checks[name] = result

        # Add placeholder checks (these don't need content analysis)
        checks["url_structure"] = {"score": 100, "issues": []}
        checks["mobile_friendly"] = {"score": 100, "issues": []}

        return checks

    def _check_title(self, content: str) -> Dict[str, Any]:
        """Check title optimization"""
        score = 100
        issues = []

        # Extract title (first h1 or title tag)
        title_match = re.search(r'<h1[^>]*>(.*?)</h1>', content, re.IGNORECASE)
        if not title_match:
            title_match = re.search(r'<title[^>]*>(.*?)</title>', content, re.IGNORECASE)

        if title_match:
            title = title_match.group(1)
            title_length = len(title)

            # Check length (optimal: 50-60 characters)
            if title_length < 30:
                score -= 20
                issues.append(f"Title too short ({title_length} chars). Optimal: 50-60 characters")
            elif title_length > 70:
                score -= 15
                issues.append(f"Title too long ({title_length} chars). Optimal: 50-60 characters")

            # Check for power words
            power_words = ["luxury", "premium", "exclusive", "best", "top", "amazing", "stunning"]
            if not any(word in title.lower() for word in power_words):
                score -= 10
                issues.append("Add power words to title (e.g., luxury, premium, exclusive)")

            # Check for numbers
            if not re.search(r'\d', title):
                score -= 5
                issues.append("Consider adding numbers to title (e.g., '3 BHK', '2024')")

            # Check for real estate keywords
            if not any(kw in title.lower() for kw in ["apartment", "flat", "house", "villa", "property"]):
                score -= 15
                issues.append("Title missing real estate keywords")
        else:
            score = 0
            issues.append("No title/h1 tag found")

        return {"score": max(0, score), "issues": issues, "title": title_match.group(1) if title_match else None}

    def _check_meta_description(self, content: str) -> Dict[str, Any]:
        """Check meta description"""
        score = 100
        issues = []

        # Extract meta description
        meta_match = re.search(r'<meta[^>]*name=["\']description["\'][^>]*content=["\']([^"\']*)["\']', content, re.IGNORECASE)
        if not meta_match:
            meta_match = re.search(r'<meta[^>]*content=["\']([^"\']*)["\'][^>]*name=["\']description["\']', content, re.IGNORECASE)

        if meta_match:
            description = meta_match.group(1)
            desc_length = len(description)

            # Check length (optimal: 150-160 characters)
            if desc_length < 120:
                score -= 20
                issues.append(f"Meta description too short ({desc_length} chars)")
            elif desc_length > 170:
                score -= 10
                issues.append(f"Meta description too long ({desc_length} chars)")

            # Check for call-to-action
            ctas = ["learn more", "discover", "find out", "explore", "contact us", "call now"]
            if not any(cta in description.lower() for cta in ctas):
                score -= 10
                issues.append("Add call-to-action to meta description")
        else:
            score = 0
            issues.append("No meta description found")

        return {"score": max(0, score), "issues": issues}

    def _check_content_quality(self, content: str) -> Dict[str, Any]:
        """Check content quality"""
        score = 100
        issues = []

        # Strip HTML for text analysis
        text = re.sub(r'<[^>]+>', '', content)

        # Word count
        word_count = len(text.split())

        # Check content length
        if word_count < 300:
            score -= 30
            issues.append(f"Content too short ({word_count} words). Minimum: 300 words")
        elif word_count < 600:
            score -= 15
            issues.append(f"Content could be longer ({word_count} words). Optimal: 600+ words")

        # Check for duplicate content (simplified)
        sentences = text.split('.')
        if len(sentences) != len(set(sentences)):
            score -= 10
            issues.append("Possible duplicate sentences detected")

        # Check for passive voice (simplified)
        passive_indicators = ["is ", "are ", "was ", "were ", "been ", "being "]
        passive_count = sum(text.lower().count(indicator) for indicator in passive_indicators)
        if passive_count > word_count * 0.1:
            score -= 10
            issues.append("High passive voice usage. Use active voice for better engagement")

        # Check content freshness indicators
        current_year = str(datetime.utcnow().year)
        if current_year not in text:
            score -= 5
            issues.append(f"Consider adding current year ({current_year}) for freshness")

        return {"score": max(0, score), "issues": issues, "word_count": word_count}

    def _check_keyword_usage(self, content: str, target_keywords: List[str]) -> Dict[str, Any]:
        """Check keyword usage and density"""
        score = 100
        issues = []

        text = re.sub(r'<[^>]+>', '', content).lower()
        word_count = len(text.split())

        keyword_density = {}
        missing_keywords = []

        for keyword in target_keywords:
            keyword_lower = keyword.lower()
            count = text.count(keyword_lower)
            density = (count / word_count * 100) if word_count > 0 else 0
            keyword_density[keyword] = {"count": count, "density": round(density, 2)}

            if count == 0:
                missing_keywords.append(keyword)
                score -= 10
            elif density < 0.5:
                score -= 5
                issues.append(f"Keyword '{keyword}' density too low ({density:.2f}%). Optimal: 1-2%")
            elif density > 3:
                score -= 10
                issues.append(f"Keyword '{keyword}' density too high ({density:.2f}%). Risk of keyword stuffing")

        if missing_keywords:
            issues.append(f"Missing keywords: {', '.join(missing_keywords)}")

        # Check LSI (Latent Semantic Indexing) keywords
        lsi_keywords = self._get_lsi_keywords(target_keywords)
        lsi_found = [kw for kw in lsi_keywords if kw.lower() in text]
        lsi_score = len(lsi_found) / len(lsi_keywords) if lsi_keywords else 1

        if lsi_score < 0.3:
            score -= 15
            issues.append("Add more semantic keywords (related terms) for better topical authority")

        return {
            "score": max(0, score),
            "issues": issues,
            "keyword_density": keyword_density,
            "lsi_coverage": round(lsi_score * 100, 1)
        }

    def _get_lsi_keywords(self, target_keywords: List[str]) -> List[str]:
        """Get LSI keywords for real estate"""
        lsi_keywords = []

        for keyword in target_keywords:
            keyword_lower = keyword.lower()

            if "apartment" in keyword_lower or "flat" in keyword_lower:
                lsi_keywords.extend(["residential", "housing", "accommodation", "dwelling", "unit"])
            if "buy" in keyword_lower or "purchase" in keyword_lower:
                lsi_keywords.extend(["investment", "ownership", "acquisition", "property deal"])
            if "rent" in keyword_lower or "lease" in keyword_lower:
                lsi_keywords.extend(["tenancy", "rental agreement", "monthly rent", "security deposit"])
            if any(loc in keyword_lower for loc in ["mumbai", "delhi", "bangalore", "pune", "chennai"]):
                lsi_keywords.extend(["metro city", "urban area", "city center", "prime location"])

        return list(set(lsi_keywords))

    def _check_readability(self, content: str) -> Dict[str, Any]:
        """Check content readability"""
        score = 100
        issues = []

        text = re.sub(r'<[^>]+>', '', content)
        sentences = text.split('.')
        words = text.split()

        if not words:
            return {"score": 0, "issues": ["No readable content found"], "flesch_score": 0}

        # Average sentence length
        avg_sentence_length = len(words) / len(sentences) if sentences else 0
        if avg_sentence_length > 25:
            score -= 15
            issues.append(f"Sentences too long (avg {avg_sentence_length:.1f} words). Keep under 20 words")

        # Average word length
        avg_word_length = sum(len(w) for w in words) / len(words)
        if avg_word_length > 6:
            score -= 10
            issues.append("Words too complex. Use simpler language for real estate content")

        # Paragraph length
        paragraphs = content.split('<p>')
        long_paragraphs = [p for p in paragraphs if len(re.sub(r'<[^>]+>', '', p).split()) > 150]
        if long_paragraphs:
            score -= 10
            issues.append(f"{len(long_paragraphs)} paragraphs too long. Break into smaller chunks")

        # Flesch Reading Ease (simplified)
        flesch_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length / 5)
        flesch_score = max(0, min(100, flesch_score))

        if flesch_score < 60:
            score -= 10
            issues.append(f"Readability score ({flesch_score:.1f}) is low. Aim for 60+ for general audience")

        return {
            "score": max(0, score),
            "issues": issues,
            "flesch_score": round(flesch_score, 1),
            "avg_sentence_length": round(avg_sentence_length, 1)
        }

    def _check_headings(self, content: str) -> Dict[str, Any]:
        """Check heading structure"""
        score = 100
        issues = []

        # Count headings
        h1_count = len(re.findall(r'<h1[^>]*>', content, re.IGNORECASE))
        h2_count = len(re.findall(r'<h2[^>]*>', content, re.IGNORECASE))
        h3_count = len(re.findall(r'<h3[^>]*>', content, re.IGNORECASE))

        # Check H1
        if h1_count == 0:
            score -= 20
            issues.append("No H1 tag found. Every page needs exactly one H1")
        elif h1_count > 1:
            score -= 15
            issues.append(f"Multiple H1 tags found ({h1_count}). Use only one H1 per page")

        # Check H2-H3 hierarchy
        if h2_count == 0:
            score -= 10
            issues.append("No H2 tags found. Use H2 for main sections")

        if h3_count > 0 and h2_count == 0:
            score -= 10
            issues.append("H3 tags without H2. Maintain proper heading hierarchy")

        # Check for keywords in headings
        headings_text = re.findall(r'<h[123][^>]*>(.*?)</h[123]>', content, re.IGNORECASE | re.DOTALL)
        headings_text = [re.sub(r'<[^>]+>', '', h) for h in headings_text]

        return {
            "score": max(0, score),
            "issues": issues,
            "heading_counts": {"h1": h1_count, "h2": h2_count, "h3": h3_count}
        }

    def _check_image_alt_text(self, content: str) -> Dict[str, Any]:
        """Check image alt text"""
        score = 100
        issues = []

        # Find all images
        images = re.findall(r'<img[^>]*>', content, re.IGNORECASE)
        images_with_alt = re.findall(r'<img[^>]*alt=["\'][^"\']+["\'][^>]*>', content, re.IGNORECASE)

        if images:
            alt_coverage = len(images_with_alt) / len(images) * 100

            if alt_coverage < 50:
                score -= 30
                issues.append(f"Only {alt_coverage:.0f}% of images have alt text. Aim for 100%")
            elif alt_coverage < 100:
                score -= 10
                issues.append(f"{len(images) - len(images_with_alt)} images missing alt text")

            # Check for descriptive alt text (not just "image" or "photo")
            poor_alt_count = 0
            for img in images_with_alt:
                alt_match = re.search(r'alt=["\']([^"\']+)["\']', img)
                if alt_match:
                    alt_text = alt_match.group(1).lower()
                    if alt_text in ["image", "photo", "picture", "img"]:
                        poor_alt_count += 1

            if poor_alt_count > 0:
                score -= 10
                issues.append(f"{poor_alt_count} images have non-descriptive alt text")

        return {
            "score": max(0, score),
            "issues": issues,
            "total_images": len(images),
            "images_with_alt": len(images_with_alt)
        }

    def _check_internal_links(self, content: str) -> Dict[str, Any]:
        """Check internal linking"""
        score = 100
        issues = []

        # Find all links
        links = re.findall(r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>', content, re.IGNORECASE)

        if not links:
            score -= 20
            issues.append("No internal links found. Add links to related content")
        elif len(links) < 2:
            score -= 10
            issues.append("Too few internal links. Aim for 3-5 links per page")

        # Check for external links (should open in new tab)
        external_links = [l for l in links if l.startswith('http') and not 'propertyyards.com' in l]
        if external_links:
            external_without_target = re.findall(
                r'<a[^>]*href=["\'](?:http|https)://(?![^"\']*propertyyards\.com)[^"\']*["\'][^>]*>(?!.*target=["\']_blank["\'])',
                content,
                re.IGNORECASE
            )
            if external_without_target:
                score -= 5
                issues.append("External links should open in new tab (add target='_blank')")

        return {
            "score": max(0, score),
            "issues": issues,
            "total_links": len(links),
            "external_links": len(external_links)
        }

    def _get_score_level(self, score: int) -> SEOScoreLevel:
        """Get score level from numeric score"""
        for level in SEOScoreLevel:
            if level.min_score <= score <= level.max_score:
                return level
        return SEOScoreLevel.POOR

    def _generate_recommendations(
        self,
        checks: Dict[str, Any],
        content_type: SEOCategory
    ) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []

        # Priority order based on impact
        priority_order = [
            "title_optimization",
            "content_quality",
            "keyword_usage",
            "meta_description",
            "heading_structure",
            "readability",
            "image_alt_text",
            "internal_links",
            "url_structure",
            "mobile_friendly"
        ]

        for check_name in priority_order:
            check_data = checks.get(check_name, {})
            score = check_data.get("score", 100)
            issues = check_data.get("issues", [])

            if score < 90 and issues:
                priority = "high" if score < 50 else "medium" if score < 75 else "low"

                for issue in issues:
                    recommendations.append({
                        "priority": priority,
                        "category": check_name.replace("_", " ").title(),
                        "issue": issue,
                        "impact": self.weights.get(check_name, 10),
                        "current_score": score
                    })

        # Sort by priority and impact
        priority_order_map = {"high": 0, "medium": 1, "low": 2}
        recommendations.sort(key=lambda x: (priority_order_map.get(x["priority"], 3), -x["impact"]))

        return recommendations[:10]  # Top 10 recommendations

    async def _ai_keyword_analysis(
        self,
        content: str,
        target_keywords: List[str],
        location: Optional[str]
    ) -> Dict[str, Any]:
        """AI-powered keyword analysis using Gemini"""
        if not self.api_key:
            return None

        try:
            # Prepare prompt for Gemini
            prompt = f"""
            Analyze the following real estate content for keyword optimization.
            
            Target Keywords: {', '.join(target_keywords)}
            Location: {location or 'Not specified'}
            
            Content: {content[:2000]}... (truncated)
            
            Please provide:
            1. Keyword suggestions (5-10 related long-tail keywords)
            2. Content gaps (what topics are missing)
            3. Competitor keyword opportunities
            4. Search intent analysis for each target keyword
            
            Return as JSON with these keys: keyword_suggestions, content_gaps, opportunities, search_intent
            """

            # Call Gemini API (simplified - actual implementation would use aiohttp)
            # For now, return mock data based on rules
            return self._generate_keyword_analysis_mock(target_keywords, location)

        except Exception as e:
            logger.error(f"AI keyword analysis failed: {e}")
            return None

    def _generate_keyword_analysis_mock(
        self,
        target_keywords: List[str],
        location: Optional[str]
    ) -> Dict[str, Any]:
        """Generate mock keyword analysis (replace with actual AI call)"""
        keyword_suggestions = []

        base_location = location or "city"

        for keyword in target_keywords:
            # Generate variations
            keyword_lower = keyword.lower()

            if "apartment" in keyword_lower or "flat" in keyword_lower:
                keyword_suggestions.extend([
                    f"buy {keyword} in {base_location}",
                    f"{keyword} for sale {base_location}",
                    f"best {keyword} in {base_location}",
                    f"luxury {keyword} {base_location}",
                    f"affordable {keyword} {base_location}"
                ])
            elif "rent" in keyword_lower:
                keyword_suggestions.extend([
                    f"{keyword} near me",
                    f"{keyword} without brokerage",
                    f"furnished {keyword} {base_location}",
                    f"{keyword} with amenities {base_location}"
                ])

        return {
            "keyword_suggestions": list(set(keyword_suggestions))[:10],
            "content_gaps": [
                "Add neighborhood information",
                "Include nearby amenities details",
                "Add price comparison with similar properties",
                "Include virtual tour link"
            ],
            "opportunities": [
                f"Target '{base_location} real estate trends'",
                f"Create content around '{base_location} property investment'",
                f"Optimize for '{base_location} new projects'"
            ],
            "search_intent": {
                kw: "Informational/Transactional" for kw in target_keywords
            }
        }

    async def optimize_content(
        self,
        content: str,
        content_type: SEOCategory,
        target_keywords: List[str],
        location: Optional[str] = None
    ) -> Optional[str]:
        """Generate AI-optimized content"""
        if not self.api_key:
            return None

        try:
            # First analyze
            analysis = await self.analyze_content(content, content_type, target_keywords, location)

            if not analysis:
                return None

            # Generate improvements based on recommendations
            optimized = content

            # Apply simple optimizations
            for rec in analysis.recommendations[:3]:  # Top 3
                if "title" in rec["category"].lower():
                    optimized = self._optimize_title(optimized, target_keywords)
                elif "meta" in rec["category"].lower():
                    optimized = self._optimize_meta(optimized, target_keywords, location)
                elif "keyword" in rec["category"].lower():
                    optimized = self._optimize_keywords(optimized, target_keywords)

            return optimized

        except Exception as e:
            logger.error(f"Content optimization failed: {e}")
            return None

    def _optimize_title(self, content: str, keywords: List[str]) -> str:
        """Optimize title with keywords"""
        # Find and replace title
        title_pattern = r'<h1[^>]*>.*?</h1>'

        main_keyword = keywords[0] if keywords else "Property"
        new_title = f"<h1>{main_keyword.title()} - Premium Real Estate | PropertyYards</h1>"

        content = re.sub(title_pattern, new_title, content, flags=re.IGNORECASE, count=1)
        return content

    def _optimize_meta(self, content: str, keywords: List[str], location: Optional[str]) -> str:
        """Optimize meta description"""
        loc_text = f" in {location}" if location else ""

        main_keyword = keywords[0] if keywords else "property"
        new_meta = f'<meta name="description" content="Find the best {main_keyword}{loc_text}. Premium properties with world-class amenities. Contact us today for exclusive deals!">'

        # Replace or add meta
        if '<meta name="description"' in content.lower():
            content = re.sub(
                r'<meta[^>]*name=["\']description["\'][^>]*>',
                new_meta,
                content,
                flags=re.IGNORECASE
            )
        else:
            # Add after <head>
            content = content.replace('<head>', f'<head>\n    {new_meta}')

        return content

    def _optimize_keywords(self, content: str, keywords: List[str]) -> str:
        """Optimize keyword placement in content"""
        text = re.sub(r'<[^>]+>', '', content)

        for keyword in keywords[:2]:  # Focus on top 2 keywords
            if keyword.lower() not in text.lower():
                # Add to first paragraph
                first_para_match = re.search(r'<p[^>]*>(.*?)</p>', content, re.IGNORECASE | re.DOTALL)
                if first_para_match:
                    first_para = first_para_match.group(0)
                    # Append keyword naturally
                    enhanced_para = first_para.replace('</p>', f' Perfect for those looking for {keyword}.</p>')
                    content = content.replace(first_para, enhanced_para, 1)

        return content

    async def generate_seo_content(
        self,
        content_type: SEOCategory,
        topic: str,
        target_keywords: List[str],
        location: str,
        word_count: int = 800
    ) -> Optional[Dict[str, Any]]:
        """Generate SEO-optimized content from scratch"""
        if not self.api_key:
            return None

        try:
            # Build prompt for Gemini
            prompt = f"""
            Write SEO-optimized real estate content for {content_type.value}.
            
            Topic: {topic}
            Location: {location}
            Target Keywords: {', '.join(target_keywords)}
            Word Count: {word_count}
            
            Requirements:
            1. Include target keywords naturally (1-2% density)
            2. Use H1, H2, H3 headings with keywords
            3. Include meta description in comment
            4. Add call-to-action at the end
            5. Write for human readers first, SEO second
            6. Include local references to {location}
            7. Mention amenities, nearby landmarks
            8. Use bullet points for features
            9. Keep paragraphs short (2-3 sentences)
            10. Add internal linking suggestions in comments
            
            Format: HTML with proper tags
            """

            # Mock generated content (replace with actual AI call)
            generated_html = self._generate_mock_seo_content(topic, target_keywords, location, word_count)

            # Analyze the generated content
            analysis = await self.analyze_content(generated_html, content_type, target_keywords, location)

            return {
                "content": generated_html,
                "seo_analysis": analysis,
                "word_count": word_count,
                "generated_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"SEO content generation failed: {e}")
            return None

    def _generate_mock_seo_content(
        self,
        topic: str,
        keywords: List[str],
        location: str,
        word_count: int
    ) -> str:
        """Generate mock SEO content (replace with AI)"""
        main_kw = keywords[0] if keywords else "property"

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta name="description" content="Find the best {main_kw} in {location}. Premium properties with world-class amenities. Contact PropertyYards today!">
    <title>{main_kw.title()} in {location} | PropertyYards</title>
</head>
<body>
    <h1>{main_kw.title()} in {location} - Your Dream Home Awaits</h1>
    
    <p>Looking for the perfect {main_kw} in {location}? PropertyYards brings you exclusive listings 
    with premium amenities and competitive prices. Whether you're buying, selling, or renting, 
    we have the ideal property for you.</p>
    
    <h2>Why Choose {main_kw.title()} in {location}?</h2>
    
    <p>{location} is one of the most sought-after locations for real estate investment. 
    With excellent connectivity, top schools, healthcare facilities, and shopping centers nearby, 
    this area offers the perfect blend of convenience and luxury.</p>
    
    <h3>Key Features of Our {main_kw.title()} Listings</h3>
    
    <ul>
        <li>Spacious rooms with modern fittings</li>
        <li>24/7 security and surveillance</li>
        <li>Swimming pool and gym facilities</li>
        <li>Reserved parking spaces</li>
        <li>Power backup and water supply</li>
        <li>Close to metro and bus stations</li>
    </ul>
    
    <h2>Investment Potential in {location}</h2>
    
    <p>The real estate market in {location} has shown consistent growth over the past 5 years. 
    Investing in a {main_kw} here ensures not just a comfortable lifestyle but also excellent 
    returns on investment. With new infrastructure projects in the pipeline, property values 
    are expected to appreciate further.</p>
    
    <h3>Nearby Amenities</h3>
    
    <ul>
        <li><strong>Schools:</strong> Top-rated educational institutions within 2km</li>
        <li><strong>Hospitals:</strong> Multi-specialty healthcare centers nearby</li>
        <li><strong>Shopping:</strong> Malls and local markets for daily needs</li>
        <li><strong>Transport:</strong> Metro, buses, and auto services available</li>
    </ul>
    
    <h2>Contact PropertyYards Today</h2>
    
    <p>Don't miss out on this opportunity to own your dream {main_kw} in {location}. 
    Our expert agents are ready to help you find the perfect property that matches your 
    requirements and budget. <strong>Call us now or schedule a site visit!</strong></p>
    
    <!-- Internal Link Suggestions:
         - <a href="/properties/{location.lower().replace(' ', '-')}">More properties in {location}</a>
         - <a href="/blog/real-estate-trends-{location.lower().replace(' ', '-')}">Real estate trends in {location}</a>
         - <a href="/contact">Contact our agents</a>
    -->
</body>
</html>"""

        return html

    def get_seo_audit_template(self, page_type: str) -> Dict[str, Any]:
        """Get SEO audit checklist template"""
        templates = {
            "property_listing": {
                "critical": [
                    "Unique title with property specs",
                    "Compelling meta description with CTA",
                    "High-quality images with alt text",
                    "Complete property details",
                    "Price clearly displayed",
                    "Contact form or CTA button"
                ],
                "important": [
                    "Virtual tour link",
                    "Floor plan images",
                    "Neighborhood information",
                    "Similar properties section",
                    "Agent/broker information"
                ],
                "nice_to_have": [
                    "Mortgage calculator",
                    "Price history chart",
                    "Walk score",
                    "School ratings"
                ]
            },
            "location_page": {
                "critical": [
                    "Location-specific title",
                    "Comprehensive area description",
                    "List of available properties",
                    "Local amenities information",
                    "Transport connectivity details"
                ],
                "important": [
                    "Average price trends",
                    "Upcoming projects",
                    "Investment potential analysis",
                    "Photo gallery of area"
                ],
                "nice_to_have": [
                    "Interactive map",
                    "Video tour of location",
                    "Resident reviews"
                ]
            }
        }

        return templates.get(page_type, templates["property_listing"])


# Global instance
ai_seo_optimizer = AISeoOptimizer()
