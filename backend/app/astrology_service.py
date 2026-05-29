"""
Astrology Service
AI-powered astrology talking feature with birth chart analysis, predictions, and remedies
"""
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
import logging
import json

logger = logging.getLogger(__name__)

class Planet(Enum):
    """Planets in Vedic astrology"""
    SUN = "sun"
    MOON = "moon"
    MARS = "mars"
    MERCURY = "mercury"
    JUPITER = "jupiter"
    VENUS = "venus"
    SATURN = "saturn"
    RAHU = "rahu"
    KETU = "ketu"

class ZodiacSign(Enum):
    """Zodiac signs"""
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"

class House(Enum):
    """Houses in astrology"""
    FIRST = 1    # Self, personality
    SECOND = 2   # Wealth, family
    THIRD = 3    # Communication, siblings
    FOURTH = 4   # Home, mother
    FIFTH = 5    # Children, creativity
    SIXTH = 6    # Health, enemies
    SEVENTH = 7  # Marriage, partnerships
    EIGHTH = 8   # Transformation, longevity
    NINTH = 9    # Fortune, higher learning
    TENTH = 10   # Career, reputation
    ELEVENTH = 11 # Gains, social network
    TWELFTH = 12 # Losses, spirituality

class AstrologyCategory(Enum):
    """Categories of astrological advice"""
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    FINANCE = "finance"
    EDUCATION = "education"
    MARRIAGE = "marriage"
    PROPERTY = "property"
    BUSINESS = "business"
    TRAVEL = "travel"
    SPIRITUALITY = "spirituality"

@dataclass
class PlanetaryPosition:
    """Planetary position in birth chart"""
    planet: Planet
    zodiac_sign: ZodiacSign
    degree: float
    house: House
    is_retrograde: bool = False
    aspects: List[str] = None

@dataclass
class BirthChart:
    """Complete birth chart data"""
    user_id: str
    name: str
    birth_date: datetime
    birth_time: str
    birth_place: str
    latitude: float
    longitude: float
    timezone: str
    ascendant: ZodiacSign
    moon_sign: ZodiacSign
    sun_sign: ZodiacSign
    planetary_positions: List[PlanetaryPosition]
    dasha_period: str
    current_transits: Dict[str, Any]

@dataclass
class AstrologyInsight:
    """Astrological insight and prediction"""
    category: AstrologyCategory
    title: str
    description: str
    prediction: str
    confidence: float  # 0.0 to 1.0
    remedies: List[str]
    favorable_period: str
    challenges: List[str]
    recommendations: List[str]

class AstrologyService:
    """Service for astrology calculations and predictions"""
    
    def __init__(self):
        # Planetary characteristics
        self.planet_natures = {
            Planet.SUN: {"element": "fire", "quality": "masculine", "ruling_house": House.FIFTH},
            Planet.MOON: {"element": "water", "quality": "feminine", "ruling_house": House.FOURTH},
            Planet.MARS: {"element": "fire", "quality": "masculine", "ruling_house": House.FIRST},
            Planet.MERCURY: {"element": "earth", "quality": "neutral", "ruling_house": House.THIRD},
            Planet.JUPITER: {"element": "fire", "quality": "masculine", "ruling_house": House.NINTH},
            Planet.VENUS: {"element": "earth", "quality": "feminine", "ruling_house": House.SEVENTH},
            Planet.SATURN: {"element": "air", "quality": "masculine", "ruling_house": House.TENTH},
            Planet.RAHU: {"element": "air", "quality": "feminine", "ruling_house": None},
            Planet.KETU: {"element": "fire", "quality": "masculine", "ruling_house": None}
        }
        
        # Zodiac sign characteristics
        self.zodiac_characteristics = {
            ZodiacSign.ARIES: {"element": "fire", "ruler": Planet.MARS, "nature": "pioneer, warrior"},
            ZodiacSign.TAURUS: {"element": "earth", "ruler": Planet.VENUS, "nature": "builder, preserver"},
            ZodiacSign.GEMINI: {"element": "air", "ruler": Planet.MERCURY, "nature": "communicator, thinker"},
            ZodiacSign.CANCER: {"element": "water", "ruler": Planet.MOON, "nature": "nurturer, protector"},
            ZodiacSign.LEO: {"element": "fire", "ruler": Planet.SUN, "nature": "leader, performer"},
            ZodiacSign.VIRGO: {"element": "earth", "ruler": Planet.MERCURY, "nature": "analyst, healer"},
            ZodiacSign.LIBRA: {"element": "air", "ruler": Planet.VENUS, "nature": "diplomat, artist"},
            ZodiacSign.SCORPIO: {"element": "water", "ruler": Planet.MARS, "nature": "transformer, researcher"},
            ZodiacSign.SAGITTARIUS: {"element": "fire", "ruler": Planet.JUPITER, "nature": "explorer, philosopher"},
            ZodiacSign.CAPRICORN: {"element": "earth", "ruler": Planet.SATURN, "nature": "organizer, achiever"},
            ZodiacSign.AQUARIUS: {"element": "air", "ruler": Planet.SATURN, "nature": "innovator, humanitarian"},
            ZodiacSign.PISCES: {"element": "water", "ruler": Planet.JUPITER, "nature": "mystic, dreamer"}
        }
        
        # House meanings
        self.house_meanings = {
            House.FIRST: "Personality, appearance, self-expression",
            House.SECOND: "Wealth, possessions, family values",
            House.THIRD: "Communication, siblings, short journeys",
            House.FOURTH: "Home, mother, roots, property",
            House.FIFTH: "Children, creativity, romance, intelligence",
            House.SIXTH: "Health, service, enemies, obstacles",
            House.SEVENTH: "Partnerships, marriage, business relationships",
            House.EIGHTH: "Transformation, death, inheritance, longevity",
            House.NINTH: "Higher learning, fortune, spirituality, father",
            House.TENTH: "Career, reputation, achievements",
            House.ELEVENTH: "Gains, social network, elder siblings",
            House.TWELFTH: "Losses, expenses, spirituality, foreign lands"
        }
        
        # Remedies database
        self.remedies_database = {
            Planet.SUN: ["Offer water to Sun in copper vessel", "Chant Gayatri Mantra", "Wear ruby gemstone"],
            Planet.MOON: ["Offer milk to Shivling", "Chant Om Somaya Namah", "Wear pearl gemstone"],
            Planet.MARS: ["Offer red flowers to Hanuman", "Chant Om Ang Angarakaya Namah", "Wear red coral"],
            Planet.MERCURY: ["Feed green grass to cows", "Chant Om Budhaya Namah", "Wear emerald gemstone"],
            Planet.JUPITER: ["Feed Brahmins on Thursdays", "Chant Om Brihaspataye Namah", "Wear yellow sapphire"],
            Planet.VENUS: ["Offer white flowers to Lakshmi", "Chant Om Shukraya Namah", "Wear diamond gemstone"],
            Planet.SATURN: ["Light sesame oil lamp on Saturday", "Chant Om Shanicharaya Namah", "Wear blue sapphire"],
            Planet.RAHU: ["Donate black clothes on Wednesday", "Chant Om Rahave Namah", "Wear hessonite"],
            Planet.KETU: ["Donate blankets to poor", "Chant Om Ketave Namah", "Wear cat's eye"]
        }

    def calculate_birth_chart(self, birth_data: Dict[str, Any]) -> BirthChart:
        """Calculate birth chart from birth data"""
        try:
            # Parse birth data
            birth_date = datetime.strptime(birth_data["birth_date"], "%Y-%m-%d")
            birth_time = birth_data.get("birth_time", "12:00")
            birth_place = birth_data.get("birth_place", "Unknown")
            latitude = float(birth_data.get("latitude", 28.6139))  # Default Delhi
            longitude = float(birth_data.get("longitude", 77.2090))
            timezone = birth_data.get("timezone", "Asia/Kolkata")
            
            # Calculate zodiac signs (simplified calculation)
            sun_sign = self._calculate_zodiac_sign(birth_date, Planet.SUN)
            moon_sign = self._calculate_zodiac_sign(birth_date, Planet.MOON)
            ascendant = self._calculate_ascendant(birth_date, birth_time, latitude, longitude)
            
            # Calculate planetary positions (simplified)
            planetary_positions = []
            for planet in Planet:
                zodiac_sign = self._calculate_zodiac_sign(birth_date, planet)
                house = self._calculate_planet_house(zodiac_sign, ascendant)
                degree = self._calculate_planet_degree(birth_date, planet)
                is_retrograde = self._is_retrograde(planet, birth_date)
                
                position = PlanetaryPosition(
                    planet=planet,
                    zodiac_sign=zodiac_sign,
                    degree=degree,
                    house=house,
                    is_retrograde=is_retrograde
                )
                planetary_positions.append(position)
            
            # Calculate dasha period
            dasha_period = self._calculate_dasha_period(birth_date, moon_sign)
            
            # Calculate current transits
            current_transits = self._calculate_current_transits(datetime.utcnow())
            
            return BirthChart(
                user_id=birth_data.get("user_id", "unknown"),
                name=birth_data.get("name", "User"),
                birth_date=birth_date,
                birth_time=birth_time,
                birth_place=birth_place,
                latitude=latitude,
                longitude=longitude,
                timezone=timezone,
                ascendant=ascendant,
                moon_sign=moon_sign,
                sun_sign=sun_sign,
                planetary_positions=planetary_positions,
                dasha_period=dasha_period,
                current_transits=current_transits
            )
            
        except Exception as e:
            logger.error(f"Birth chart calculation error: {e}")
            raise ValueError(f"Failed to calculate birth chart: {str(e)}")

    def _calculate_zodiac_sign(self, birth_date: datetime, planet: Planet) -> ZodiacSign:
        """Calculate zodiac sign for planet (simplified)"""
        # This is a simplified calculation - in production, use ephemeris data
        day_of_year = birth_date.timetuple().tm_yday
        year = birth_date.year
        
        # Simplified zodiac calculation based on birth date
        zodiac_days = {
            ZodiacSign.ARIES: (80, 110),
            ZodiacSign.TAURUS: (110, 141),
            ZodiacSign.GEMINI: (141, 172),
            ZodiacSign.CANCER: (172, 204),
            ZodiacSign.LEO: (204, 235),
            ZodiacSign.VIRGO: (235, 266),
            ZodiacSign.LIBRA: (266, 296),
            ZodiacSign.SCORPIO: (296, 326),
            ZodiacSign.SAGITTARIUS: (326, 356),
            ZodiacSign.CAPRICORN: (356, 20),  # Wraps around
            ZodiacSign.AQUARIUS: (20, 50),
            ZodiacSign.PISCES: (50, 80)
        }
        
        for sign, (start_day, end_day) in zodiac_days.items():
            if start_day < end_day:
                if start_day <= day_of_year < end_day:
                    return sign
            else:  # Wraps around year end
                if day_of_year >= start_day or day_of_year < end_day:
                    return sign
        
        return ZodiacSign.ARIES  # Default

    def _calculate_ascendant(self, birth_date: datetime, birth_time: str, latitude: float, longitude: float) -> ZodiacSign:
        """Calculate ascendant (simplified)"""
        # Simplified ascendant calculation based on birth time
        try:
            hour, minute = map(int, birth_time.split(":"))
            total_minutes = hour * 60 + minute
            
            # Each zodiac sign rises approximately every 2 hours
            sign_index = int(total_minutes / 120) % 12
            signs = list(ZodiacSign)
            return signs[sign_index]
        except:
            return ZodiacSign.ARIES

    def _calculate_planet_house(self, zodiac_sign: ZodiacSign, ascendant: ZodiacSign) -> House:
        """Calculate which house a planet is in"""
        signs = list(ZodiacSign)
        ascendant_index = signs.index(ascendant)
        planet_sign_index = signs.index(zodiac_sign)
        
        house_number = (planet_sign_index - ascendant_index) % 12 + 1
        return House(house_number)

    def _calculate_planet_degree(self, birth_date: datetime, planet: Planet) -> float:
        """Calculate planet degree (simplified)"""
        # Simplified degree calculation
        base_degree = (birth_date.timetuple().tm_yday * 360) / 365
        planet_offset = {
            Planet.SUN: 0,
            Planet.MOON: 12,
            Planet.MARS: 45,
            Planet.MERCURY: 30,
            Planet.JUPITER: 120,
            Planet.VENUS: 60,
            Planet.SATURN: 180,
            Planet.RAHU: 90,
            Planet.KETU: 270
        }
        
        degree = (base_degree + planet_offset.get(planet, 0)) % 360
        return degree

    def _is_retrograde(self, planet: Planet, birth_date: datetime) -> bool:
        """Check if planet is retrograde (simplified)"""
        # Simplified retrograde calculation
        retrograde_periods = {
            Planet.MERCURY: [3, 7, 11],  # March, July, November
            Planet.VENUS: [6, 10],        # June, October
            Planet.MARS: [9],              # September
            Planet.SATURN: [4, 8, 12],    # April, August, December
            Planet.JUPITER: [1, 5, 9],    # January, May, September
        }
        
        return birth_date.month in retrograde_periods.get(planet, [])

    def _calculate_dasha_period(self, birth_date: datetime, moon_sign: ZodiacSign) -> str:
        """Calculate current dasha period (simplified)"""
        # Simplified dasha calculation
        dasha_sequence = [Planet.KETU, Planet.VENUS, Planet.SUN, Planet.MOON, 
                         Planet.MARS, Planet.RAHU, Planet.JUPITER, Planet.SATURN, Planet.MERCURY]
        
        current_age = (datetime.utcnow() - birth_date).days / 365.25
        dasha_index = int(current_age / 7) % len(dasha_sequence)
        
        return f"{dasha_sequence[dasha_index].value.title()} Dasha"

    def _calculate_current_transits(self, current_date: datetime) -> Dict[str, Any]:
        """Calculate current planetary transits (simplified)"""
        transits = {}
        for planet in Planet:
            # Simplified transit calculation
            transits[planet.value] = {
                "zodiac_sign": self._calculate_zodiac_sign(current_date, planet).value,
                "degree": self._calculate_planet_degree(current_date, planet),
                "is_retrograde": self._is_retrograde(planet, current_date)
            }
        return transits

    def generate_astrology_insights(self, birth_chart: BirthChart, categories: List[str] = None) -> List[AstrologyInsight]:
        """Generate astrological insights and predictions"""
        insights = []
        
        if not categories:
            categories = [cat.value for cat in AstrologyCategory]
        
        for category in categories:
            try:
                insight = self._generate_category_insight(birth_chart, AstrologyCategory(category))
                insights.append(insight)
            except Exception as e:
                logger.error(f"Error generating insight for {category}: {e}")
                continue
        
        return insights

    def _generate_category_insight(self, birth_chart: BirthChart, category: AstrologyCategory) -> AstrologyInsight:
        """Generate insight for specific category"""
        
        # Category-specific analysis logic
        if category == AstrologyCategory.CAREER:
            return self._analyze_career(birth_chart)
        elif category == AstrologyCategory.RELATIONSHIP:
            return self._analyze_relationship(birth_chart)
        elif category == AstrologyCategory.HEALTH:
            return self._analyze_health(birth_chart)
        elif category == AstrologyCategory.FINANCE:
            return self._analyze_finance(birth_chart)
        elif category == AstrologyCategory.PROPERTY:
            return self._analyze_property(birth_chart)
        elif category == AstrologyCategory.MARRIAGE:
            return self._analyze_marriage(birth_chart)
        elif category == AstrologyCategory.BUSINESS:
            return self._analyze_business(birth_chart)
        else:
            return self._generate_general_insight(birth_chart, category)

    def _analyze_career(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze career prospects"""
        # Find planets in 10th house (career)
        tenth_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.TENTH]
        
        # Check Sun and Saturn for career
        sun_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.SUN), None)
        saturn_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.SATURN), None)
        
        confidence = 0.7
        predictions = []
        remedies = []
        challenges = []
        recommendations = []
        
        if tenth_house_planets:
            main_planet = tenth_house_planets[0].planet
            predictions.append(f"Strong {main_planet.value} influence in 10th house indicates success in {self._get_career_field(main_planet)}")
            confidence += 0.2
        
        if sun_position and sun_position.zodiac_sign in [ZodiacSign.LEO, ZodiacSign.ARIES]:
            predictions.append("Leadership qualities prominent - suitable for management roles")
            confidence += 0.1
        
        if saturn_position and saturn_position.zodiac_sign in [ZodiacSign.CAPRICORN, ZodiacSign.AQUARIUS]:
            predictions.append("Hard work and perseverance will lead to long-term success")
            confidence += 0.1
        
        challenges = ["Career growth may be slow initially", "Need to maintain work-life balance"]
        remedies = self.remedies_database.get(Planet.SATURN, ["Chant mantras for career growth"])
        recommendations = ["Focus on skill development", "Network with professionals in your field"]
        
        favorable_period = f"Next {birth_chart.dasha_period} period will be favorable for career growth"
        
        return AstrologyInsight(
            category=AstrologyCategory.CAREER,
            title="Career Prospects Analysis",
            description="Analysis of your career potential based on planetary positions",
            prediction=". ".join(predictions) if predictions else "Career prospects look positive with steady growth",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period=favorable_period,
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_relationship(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze relationship prospects"""
        # Check 7th house (partnerships) and Venus
        seventh_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.SEVENTH]
        venus_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.VENUS), None)
        
        predictions = []
        confidence = 0.6
        
        if seventh_house_planets:
            main_planet = seventh_house_planets[0].planet
            predictions.append(f"{main_planet.value} in 7th house indicates {self._get_relationship_style(main_planet)} partnerships")
            confidence += 0.2
        
        if venus_position:
            if venus_position.zodiac_sign in [ZodiacSign.LIBRA, ZodiacSign.TAURUS]:
                predictions.append("Romantic and harmonious relationships indicated")
                confidence += 0.15
            elif venus_position.is_retrograde:
                predictions.append("Past relationship karma may influence current partnerships")
        
        challenges = ["Need to work on communication", "Avoid rushing into commitments"]
        remedies = self.remedies_database.get(Planet.VENUS, ["Wear rose quartz for love energy"])
        recommendations = ["Practice patience in relationships", "Focus on self-love first"]
        
        return AstrologyInsight(
            category=AstrologyCategory.RELATIONSHIP,
            title="Relationship Compatibility",
            description="Analysis of your relationship patterns and compatibility",
            prediction=". ".join(predictions) if predictions else "Relationships require patience and understanding",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Venus-ruled periods will be favorable for relationships",
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_health(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze health prospects"""
        # Check 6th house (health) and Saturn
        sixth_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.SIXTH]
        saturn_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.SATURN), None)
        
        predictions = []
        confidence = 0.6
        
        if sixth_house_planets:
            predictions.append("Regular health checkups recommended")
            confidence += 0.1
        
        if saturn_position and saturn_position.is_retrograde:
            predictions.append("Chronic health issues require attention")
            confidence += 0.15
        
        challenges = ["Stress may affect health", "Need to maintain healthy lifestyle"]
        remedies = self.remedies_database.get(Planet.SATURN, ["Practice yoga and meditation"])
        recommendations = ["Exercise regularly", "Maintain balanced diet"]
        
        return AstrologyInsight(
            category=AstrologyCategory.HEALTH,
            title="Health and Wellness",
            description="Analysis of your health tendencies and recommendations",
            prediction=". ".join(predictions) if predictions else "Overall health looks stable with proper care",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Saturn periods require extra health attention",
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_finance(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze financial prospects"""
        # Check 2nd house (wealth) and 11th house (gains)
        second_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.SECOND]
        eleventh_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.ELEVENTH]
        jupiter_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.JUPITER), None)
        
        predictions = []
        confidence = 0.6
        
        if jupiter_position and jupiter_position.zodiac_sign in [ZodiacSign.SAGITTARIUS, ZodiacSign.PISCES]:
            predictions.append("Jupiter blesses with financial wisdom and prosperity")
            confidence += 0.2
        
        if second_house_planets:
            predictions.append("Strong financial foundation indicated")
            confidence += 0.15
        
        if eleventh_house_planets:
            predictions.append("Good gains from investments and social network")
            confidence += 0.15
        
        challenges = ["Avoid speculative investments", "Need to budget carefully"]
        remedies = self.remedies_database.get(Planet.JUPITER, ["Donate to charities on Thursdays"])
        recommendations = ["Invest in long-term assets", "Maintain emergency fund"]
        
        return AstrologyInsight(
            category=AstrologyCategory.FINANCE,
            title="Financial Prosperity",
            description="Analysis of your financial potential and investment guidance",
            prediction=". ".join(predictions) if predictions else "Financial stability through careful planning",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Jupiter periods will bring financial opportunities",
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_property(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze property prospects"""
        # Check 4th house (property/home) and Mars
        fourth_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.FOURTH]
        mars_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.MARS), None)
        
        predictions = []
        confidence = 0.6
        
        if fourth_house_planets:
            main_planet = fourth_house_planets[0].planet
            predictions.append(f"{main_planet.value} in 4th house indicates favorable property prospects")
            confidence += 0.2
        
        if mars_position and mars_position.zodiac_sign in [ZodiacSign.CANCER, ZodiacSign.SCORPIO]:
            predictions.append("Good timing for property investment")
            confidence += 0.15
        
        challenges = ["Property disputes possible", "Need thorough documentation"]
        remedies = self.remedies_database.get(Planet.MARS, ["Perform Hanuman Chalisa on Tuesdays"])
        recommendations = ["Consult Vastu expert", "Choose properties with good energy"]
        
        return AstrologyInsight(
            category=AstrologyCategory.PROPERTY,
            title="Property and Real Estate",
            description="Analysis of property investment and home prospects",
            prediction=". ".join(predictions) if predictions else "Property investment requires careful timing",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Mars periods will be good for property matters",
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_marriage(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze marriage prospects"""
        # Check 7th house and Venus
        seventh_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.SEVENTH]
        venus_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.VENUS), None)
        jupiter_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.JUPITER), None)
        
        predictions = []
        confidence = 0.6
        
        if venus_position and venus_position.zodiac_sign in [ZodiacSign.LIBRA, ZodiacSign.TAURUS]:
            predictions.append("Harmonious marriage indicated")
            confidence += 0.2
        
        if jupiter_position and jupiter_position.house == House.SEVENTH:
            predictions.append("Beneficial marriage timing")
            confidence += 0.15
        
        challenges = ["Need to be patient in finding right partner", "Family approval important"]
        remedies = self.remedies_database.get(Planet.VENUS, ["Perform Lakshmi Puja on Fridays"])
        recommendations = ["Focus on self-development", "Choose compatible partner"]
        
        return AstrologyInsight(
            category=AstrologyCategory.MARRIAGE,
            title="Marriage and Partnership",
            description="Analysis of marriage timing and compatibility",
            prediction=". ".join(predictions) if predictions else "Marriage prospects look favorable with patience",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Venus periods will be auspicious for marriage",
            challenges=challenges,
            recommendations=recommendations
        )

    def _analyze_business(self, birth_chart: BirthChart) -> AstrologyInsight:
        """Analyze business prospects"""
        # Check 7th house (partnerships) and 10th house (career)
        seventh_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.SEVENTH]
        tenth_house_planets = [pos for pos in birth_chart.planetary_positions if pos.house == House.TENTH]
        mercury_position = next((pos for pos in birth_chart.planetary_positions if pos.planet == Planet.MERCURY), None)
        
        predictions = []
        confidence = 0.6
        
        if mercury_position and mercury_position.zodiac_sign in [ZodiacSign.GEMINI, ZodiacSign.VIRGO]:
            predictions.append("Strong business acumen and communication skills")
            confidence += 0.2
        
        if seventh_house_planets:
            predictions.append("Good for business partnerships")
            confidence += 0.15
        
        challenges = ["Business may face initial challenges", "Need proper planning"]
        remedies = self.remedies_database.get(Planet.MERCURY, ["Feed green grass to cows on Wednesdays"])
        recommendations = ["Start small and scale gradually", "Build strong business network"]
        
        return AstrologyInsight(
            category=AstrologyCategory.BUSINESS,
            title="Business and Entrepreneurship",
            description="Analysis of business potential and success factors",
            prediction=". ".join(predictions) if predictions else "Business success through hard work and planning",
            confidence=min(confidence, 0.95),
            remedies=remedies,
            favorable_period="Mercury periods will support business growth",
            challenges=challenges,
            recommendations=recommendations
        )

    def _generate_general_insight(self, birth_chart: BirthChart, category: AstrologyCategory) -> AstrologyInsight:
        """Generate general insight for category"""
        return AstrologyInsight(
            category=category,
            title=f"{category.title()} Analysis",
            description=f"General astrological analysis for {category.value}",
            prediction="Current planetary positions indicate favorable conditions",
            confidence=0.6,
            remedies=["Chant mantras regularly", "Meditate daily"],
            favorable_period=birth_chart.dasha_period,
            challenges=["Need to maintain positive attitude"],
            recommendations=["Focus on personal growth", "Stay optimistic"]
        )

    def _get_career_field(self, planet: Planet) -> str:
        """Get career field based on planet"""
        career_fields = {
            Planet.SUN: "leadership, government, politics",
            Planet.MOON: "healthcare, hospitality, creative fields",
            Planet.MARS: "military, sports, engineering",
            Planet.MERCURY: "communication, teaching, writing",
            Planet.JUPITER: "teaching, law, finance",
            Planet.VENUS: "arts, entertainment, fashion",
            Planet.SATURN: "administration, real estate, construction",
            Planet.RAHU: "technology, research, innovation",
            Planet.KETU: "spirituality, healing, psychology"
        }
        return career_fields.get(planet, "general field")

    def _get_relationship_style(self, planet: Planet) -> str:
        """Get relationship style based on planet"""
        relationship_styles = {
            Planet.SUN: "dominant and leadership-oriented",
            Planet.MOON: "nurturing and emotional",
            Planet.MARS: "passionate and assertive",
            Planet.MERCURY: "intellectual and communicative",
            Planet.JUPITER: "wise and expansive",
            Planet.VENUS: "romantic and harmonious",
            Planet.SATURN: "serious and committed",
            Planet.RAHU: "unconventional and intense",
            Planet.KETU: "spiritual and detached"
        }
        return relationship_styles.get(planet, "balanced")

    def get_daily_prediction(self, birth_chart: BirthChart, date: datetime = None) -> Dict[str, Any]:
        """Get daily prediction based on transits"""
        if date is None:
            date = datetime.utcnow()
        
        # Calculate transits for the day
        transits = self._calculate_current_transits(date)
        
        # Analyze significant aspects
        aspects = []
        for planet, transit_data in transits.items():
            # Check for favorable aspects
            if transit_data["zodiac_sign"] in [sign.value for sign in [ZodiacSign.CANCER, ZodiacSign.LEO, ZodiacSign.GEMINI]]:
                aspects.append(f"{planet} in favorable position")
        
        # Generate daily prediction
        prediction = {
            "date": date.strftime("%Y-%m-%d"),
            "day": date.strftime("%A"),
            "overall_rating": "Good" if len(aspects) > 3 else "Moderate",
            "key_aspects": aspects,
            "recommendations": ["Focus on positive energy", "Avoid important decisions if stressed"],
            "lucky_color": self._get_lucky_color(birth_chart.sun_sign),
            "lucky_number": self._get_lucky_number(birth_chart.birth_date.day),
            "mantra": self._get_daily_mantra(birth_chart.dasha_period)
        }
        
        return prediction

    def _get_lucky_color(self, sun_sign: ZodiacSign) -> str:
        """Get lucky color based on sun sign"""
        lucky_colors = {
            ZodiacSign.ARIES: "Red",
            ZodiacSign.TAURUS: "Green",
            ZodiacSign.GEMINI: "Yellow",
            ZodiacSign.CANCER: "White",
            ZodiacSign.LEO: "Orange",
            ZodiacSign.VIRGO: "Grey",
            ZodiacSign.LIBRA: "Pink",
            ZodiacSign.SCORPIO: "Maroon",
            ZodiacSign.SAGITTARIUS: "Purple",
            ZodiacSign.CAPRICORN: "Black",
            ZodiacSign.AQUARIUS: "Blue",
            ZodiacSign.PISCES: "Sea Green"
        }
        return lucky_colors.get(sun_sign, "Blue")

    def _get_lucky_number(self, birth_day: int) -> int:
        """Get lucky number based on birth day"""
        return ((birth_day - 1) % 9) + 1

    def _get_daily_mantra(self, dasha_period: str) -> str:
        """Get daily mantra based on dasha period"""
        mantras = {
            "Sun Dasha": "Om Suryaya Namah",
            "Moon Dasha": "Om Somaya Namah",
            "Mars Dasha": "Om Ang Angarakaya Namah",
            "Mercury Dasha": "Om Budhaya Namah",
            "Jupiter Dasha": "Om Brihaspataye Namah",
            "Venus Dasha": "Om Shukraya Namah",
            "Saturn Dasha": "Om Shanicharaya Namah",
            "Rahu Dasha": "Om Rahave Namah",
            "Ketu Dasha": "Om Ketave Namah"
        }
        return mantras.get(dasha_period, "Om Gam Ganapataye Namah")

# Global instance
astrology_service = AstrologyService()
