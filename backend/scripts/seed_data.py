"""
MongoDB Seed Data Script for Housing Platform
Run from backend/ directory:
    python scripts/seed_data.py
"""
import asyncio
import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── Sample Data ────────────────────────────────────────────────────────────────

CITIES = [
    ("Mumbai",      "Maharashtra", "India"),
    ("Delhi",       "Delhi",       "India"),
    ("Bangalore",   "Karnataka",   "India"),
    ("Hyderabad",   "Telangana",   "India"),
    ("Chennai",     "Tamil Nadu",  "India"),
    ("Pune",        "Maharashtra", "India"),
    ("Kolkata",     "West Bengal", "India"),
    ("Ahmedabad",   "Gujarat",     "India"),
    ("Noida",       "Uttar Pradesh","India"),
    ("Gurgaon",     "Haryana",     "India"),
]

PROPERTY_TYPES   = ["apartment", "villa", "house", "plot", "commercial", "studio"]
LISTING_TYPES    = ["sale", "rent"]
AMENITIES_POOL   = [
    "Swimming Pool", "Gym", "Parking", "Security", "Power Backup",
    "Lift", "Garden", "Club House", "24x7 Water Supply", "CCTV",
    "Intercom", "Fire Safety", "Rainwater Harvesting", "Solar Panel",
]
LOCATIONS = [
    "Bandra West", "Koramangala", "Sector 62", "Jubilee Hills",
    "Anna Nagar", "Hinjewadi", "Salt Lake", "SG Highway",
    "Sector 18", "DLF Phase 3", "Whitefield", "Powai",
    "Malviya Nagar", "Electronic City", "Madhapur",
]

PROPERTY_TITLES = [
    "Luxurious {bed}BHK Apartment in {loc}",
    "Spacious {bed}BHK Flat near Metro",
    "Modern {bed}BHK in Prime Location",
    "Affordable {bed}BHK for Sale",
    "Beautiful {bed}BHK with Sea View",
    "Ready to Move {bed}BHK in {loc}",
    "Premium Villa in {loc}",
    "Independent House with Garden",
    "Commercial Space in {loc}",
    "Studio Apartment in IT Hub",
]

FIRST_NAMES = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Anita", "Ravi", "Pooja", "Suresh", "Deepa"]
LAST_NAMES  = ["Sharma", "Verma", "Gupta", "Singh", "Kumar", "Patel", "Nair", "Reddy", "Joshi", "Mehta"]


def rnd_name():
    return f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"

def rnd_phone():
    return f"+91{random.randint(7000000000, 9999999999)}"

def rnd_email(name: str):
    slug = name.lower().replace(" ", ".") + str(random.randint(10, 99))
    return f"{slug}@example.com"

def rnd_title(beds: int, loc: str):
    tmpl = random.choice(PROPERTY_TITLES)
    return tmpl.format(bed=beds, loc=loc)

def rnd_amenities():
    return random.sample(AMENITIES_POOL, k=random.randint(3, 8))

def rnd_price(prop_type: str, listing: str):
    if listing == "rent":
        return round(random.uniform(8_000, 150_000), -3)       # ₹8k–1.5L/month
    if prop_type == "plot":
        return round(random.uniform(500_000, 10_000_000), -4)   # ₹5L–1Cr
    if prop_type == "commercial":
        return round(random.uniform(2_000_000, 50_000_000), -4) # ₹20L–5Cr
    return round(random.uniform(1_500_000, 30_000_000), -4)     # ₹15L–3Cr


# ── Seed Functions ─────────────────────────────────────────────────────────────

async def seed_users(db) -> list:
    """Create 15 users: 1 admin, 4 agents, 5 sellers, 5 buyers"""
    await db.users.delete_many({"email": {"$regex": "@example.com"}})

    users = []
    now = datetime.now(timezone.utc)

    def make_user(email, role, fname, lname, phone):
        return {
            "_id_str": str(uuid.uuid4()),
            "email": email,
            "first_name": fname,
            "last_name": lname,
            "phone_number": phone,
            "password_hash": pwd_context.hash("Test@1234"),
            "role": role,
            "is_active": True,
            "created_at": now,
            "updated_at": now,
        }

    # Admin
    users.append(make_user("admin@propertyyards.com", "admin", "Admin", "User", "+919000000001"))

    # Agents
    for i in range(4):
        n = rnd_name()
        users.append(make_user(rnd_email(n), "agent", n.split()[0], n.split()[1], rnd_phone()))

    # Sellers
    for i in range(5):
        n = rnd_name()
        users.append(make_user(rnd_email(n), "seller", n.split()[0], n.split()[1], rnd_phone()))

    # Buyers
    for i in range(5):
        n = rnd_name()
        users.append(make_user(rnd_email(n), "buyer", n.split()[0], n.split()[1], rnd_phone()))

    result = await db.users.insert_many(users)
    print(f"  ✅ Users seeded: {len(result.inserted_ids)}")

    # Reload with real _id
    return await db.users.find().to_list(length=100)


async def seed_properties(db, users: list) -> list:
    """Create 50 property listings"""
    await db.properties.delete_many({"description": {"$regex": "seed"}})

    sellers = [u for u in users if u["role"] in ("seller", "agent")]
    properties = []
    now = datetime.now(timezone.utc)

    for i in range(50):
        owner    = random.choice(sellers)
        city, state, country = random.choice(CITIES)
        loc      = random.choice(LOCATIONS)
        ptype    = random.choice(PROPERTY_TYPES)
        ltype    = random.choice(LISTING_TYPES)
        beds     = random.randint(1, 5) if ptype not in ("plot", "commercial") else 0
        baths    = random.randint(1, beds + 1) if beds > 0 else 0
        area     = round(random.uniform(300, 5000), 1)
        price    = rnd_price(ptype, ltype)
        amenities = rnd_amenities()
        created  = now - timedelta(days=random.randint(0, 180))

        prop = {
            "user_id":       str(owner["_id"]),
            "title":         rnd_title(beds, loc),
            "description":   f"seed - {beds}BHK {ptype} available for {ltype} in {loc}, {city}. "
                             f"Area {area} sq ft. Well maintained property with {', '.join(amenities[:3])}.",
            "location":      loc,
            "city":          city,
            "state":         state,
            "country":       country,
            "price":         price,
            "property_type": ptype,
            "listing_type":  ltype,
            "bedrooms":      beds,
            "bathrooms":     baths,
            "area":          area,
            "amenities":     amenities,
            "images":        [
                f"https://picsum.photos/seed/prop{i}a/800/600",
                f"https://picsum.photos/seed/prop{i}b/800/600",
                f"https://picsum.photos/seed/prop{i}c/800/600",
            ],
            "status":        random.choice(["listed", "listed", "listed", "sold", "rented"]),
            "furnished":     random.choice([True, False]),
            "pets_allowed":  random.choice([True, False]),
            "featured":      i < 5,
            "premium_listing": i < 10,
            "view_count":    random.randint(0, 500),
            "is_enabled":    True,
            "created_at":    created,
            "updated_at":    created,
        }

        if ltype == "rent":
            prop["rent_period"]    = random.choice(["monthly", "yearly"])
            prop["deposit_amount"] = price * random.randint(2, 6)
            prop["lease_duration"] = random.choice(["6 months", "11 months", "1 year", "2 years"])

        properties.append(prop)

    result = await db.properties.insert_many(properties)
    print(f"  ✅ Properties seeded: {len(result.inserted_ids)}")
    return await db.properties.find().to_list(length=100)


async def seed_inquiries(db, users: list, properties: list):
    """Create 30 inquiries from buyers"""
    await db.inquiries.delete_many({"message": {"$regex": "seed"}})

    buyers = [u for u in users if u["role"] == "buyer"]
    inquiries = []
    now = datetime.now(timezone.utc)

    for _ in range(30):
        buyer = random.choice(buyers)
        prop  = random.choice(properties)
        created = now - timedelta(days=random.randint(0, 60))
        inquiries.append({
            "user_id":     str(buyer["_id"]),
            "property_id": str(prop["_id"]),
            "message":     f"seed - I am interested in this property. Please share more details about "
                           f"pricing and availability. My budget is around ₹{int(prop['price']):,}.",
            "status":      random.choice(["pending", "responded", "closed"]),
            "created_at":  created,
            "updated_at":  created,
        })

    result = await db.inquiries.insert_many(inquiries)
    print(f"  ✅ Inquiries seeded: {len(result.inserted_ids)}")


async def seed_brokers(db):
    """Create 10 broker profiles"""
    await db.brokers.delete_many({"email": {"$regex": "@broker.com"}})

    brokers = []
    now = datetime.now(timezone.utc)
    for i in range(10):
        n    = rnd_name()
        city, state, _ = random.choice(CITIES)
        brokers.append({
            "name":            n,
            "email":           f"{n.lower().replace(' ', '.')}{i}@broker.com",
            "phone":           rnd_phone(),
            "city":            city,
            "state":           state,
            "license_number":  f"RERA-{random.randint(100000, 999999)}",
            "experience_years": random.randint(1, 20),
            "specialization":  random.sample(PROPERTY_TYPES, k=2),
            "rating":          round(random.uniform(3.5, 5.0), 1),
            "total_deals":     random.randint(5, 200),
            "bio":             f"Experienced real estate broker in {city} with {random.randint(5,20)} years of expertise.",
            "is_verified":     True,
            "is_active":       True,
            "created_at":      now,
            "updated_at":      now,
        })

    result = await db.brokers.insert_many(brokers)
    print(f"  ✅ Brokers seeded: {len(result.inserted_ids)}")


async def main():
    print("\n🌱 Seeding Housing Platform database...\n")

    client = AsyncIOMotorClient(settings.DATABASE_URL)
    db = client.get_default_database()

    try:
        users      = await seed_users(db)
        properties = await seed_properties(db, users)
        await seed_inquiries(db, users, properties)
        await seed_brokers(db)

        print("\n✅ Seed complete!")
        print("   Login credentials (all users): password = Test@1234")
        print("   Admin: admin@propertyyards.com / Test@1234\n")

    except Exception as e:
        print(f"\n❌ Seed failed: {e}")
        raise
    finally:
        client.close()


if __name__ == "__main__":
    asyncio.run(main())
