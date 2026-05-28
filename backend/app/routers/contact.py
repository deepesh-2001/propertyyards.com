"""
Contact Router
Endpoints for contact information and inquiries
"""
from fastapi import APIRouter, Depends, HTTPException
from app.config import settings
from app.schemas import ContactInfo, ContactInquiry
from app.database import get_database
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contact", tags=["Contact"])


@router.get("/info", response_model=ContactInfo)
async def get_contact_info():
    """Get company contact information"""
    contact_info = ContactInfo(
        company_name=settings.COMPANY_NAME,
        phone=settings.CONTACT_PHONE,
        email=settings.CONTACT_EMAIL,
        address=settings.CONTACT_ADDRESS,
        city=settings.CONTACT_CITY,
        state=settings.CONTACT_STATE,
        zip_code=settings.CONTACT_ZIP,
        country=settings.CONTACT_COUNTRY,
        website=settings.CONTACT_WEBSITE,
        support_hours=settings.SUPPORT_HOURS,
        emergency_contact=settings.EMERGENCY_CONTACT
    )
    return contact_info


@router.post("/inquiry")
async def submit_contact_inquiry(
    inquiry: ContactInquiry,
    db = Depends(get_database)
):
    """Submit a contact inquiry"""
    inquiry_data = {
        "name": inquiry.name,
        "email": inquiry.email,
        "phone": inquiry.phone,
        "subject": inquiry.subject,
        "message": inquiry.message,
        "inquiry_type": inquiry.inquiry_type,
        "status": "pending",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    result = await db.contact_inquiries.insert_one(inquiry_data)
    logger.info(f"Contact inquiry submitted: {result.inserted_id}")
    
    return {
        "message": "Inquiry submitted successfully",
        "inquiry_id": str(result.inserted_id)
    }


@router.get("/inquiries")
async def get_contact_inquiries(
    status: str = None,
    skip: int = 0,
    limit: int = 50,
    db = Depends(get_database)
):
    """Get contact inquiries (admin only)"""
    query_filter = {}
    if status:
        query_filter["status"] = status
    
    cursor = db.contact_inquiries.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
    inquiries = await cursor.to_list(length=limit)
    
    for inquiry in inquiries:
        inquiry["id"] = str(inquiry["_id"])
        del inquiry["_id"]
    
    total = await db.contact_inquiries.count_documents(query_filter)
    
    return {
        "items": inquiries,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/inquiries/{inquiry_id}")
async def update_inquiry_status(
    inquiry_id: str,
    status: str,
    db = Depends(get_database)
):
    """Update inquiry status"""
    result = await db.contact_inquiries.update_one(
        {"_id": inquiry_id},
        {
            "$set": {
                "status": status,
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Inquiry not found")
    
    return {"message": "Inquiry status updated successfully"}
