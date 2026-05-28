"""
Reports Module
Generate Excel reports for daily data
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
import logging
import io
import pandas as pd

logger = logging.getLogger(__name__)


class ReportType(str, Enum):
    """Types of reports"""
    DAILY_SUMMARY = "daily_summary"
    PROPERTY_LISTINGS = "property_listings"
    USER_ACTIVITY = "user_activity"
    INQUIRIES = "inquiries"
    LEADS = "leads"
    BROKER_PERFORMANCE = "broker_performance"
    SALES_REPORT = "sales_report"
    RENTAL_REPORT = "rental_report"


class ReportGenerator:
    """Generate Excel reports from database data"""
    
    def __init__(self, database):
        self.db = database
    
    async def generate_daily_summary_report(
        self,
        date: Optional[datetime] = None
    ) -> bytes:
        """Generate daily summary report"""
        if not date:
            date = datetime.utcnow()
        
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)
        
        # Collect data
        new_users = await self.db.users.count_documents({
            "created_at": {"$gte": start_date, "$lt": end_date}
        })
        
        new_properties = await self.db.properties.count_documents({
            "created_at": {"$gte": start_date, "$lt": end_date}
        })
        
        new_inquiries = await self.db.inquiries.count_documents({
            "created_at": {"$gte": start_date, "$lt": end_date}
        })
        
        new_leads = await self.db.crm_leads.count_documents({
            "created_at": {"$gte": start_date, "$lt": end_date}
        })
        
        # Create DataFrame
        data = {
            "Date": [date.strftime("%Y-%m-%d")],
            "New Users": [new_users],
            "New Properties": [new_properties],
            "New Inquiries": [new_inquiries],
            "New Leads": [new_leads]
        }
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Daily Summary', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_property_listings_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate property listings report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query_filter = {
            "created_at": {"$gte": start_date, "$lt": end_date}
        }
        
        cursor = self.db.properties.find(query_filter)
        properties = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for prop in properties:
            data.append({
                "ID": str(prop["_id"]),
                "Title": prop.get("title", ""),
                "Type": prop.get("property_type", ""),
                "Listing Type": prop.get("listing_type", ""),
                "Price": prop.get("price", 0),
                "Location": prop.get("location", ""),
                "City": prop.get("city", ""),
                "Bedrooms": prop.get("bedrooms", 0),
                "Bathrooms": prop.get("bathrooms", 0),
                "Area": prop.get("area", 0),
                "Status": prop.get("status", ""),
                "Created At": prop.get("created_at", "")
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Property Listings', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_user_activity_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate user activity report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query_filter = {
            "created_at": {"$gte": start_date, "$lt": end_date}
        }
        
        cursor = self.db.users.find(query_filter)
        users = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for user in users:
            data.append({
                "ID": str(user["_id"]),
                "Email": user.get("email", ""),
                "Name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "Phone": user.get("phone_number", ""),
                "Role": user.get("role", ""),
                "Active": user.get("is_active", False),
                "Created At": user.get("created_at", "")
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='User Activity', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_inquiries_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate inquiries report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query_filter = {
            "created_at": {"$gte": start_date, "$lt": end_date}
        }
        
        cursor = self.db.inquiries.find(query_filter)
        inquiries = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for inquiry in inquiries:
            data.append({
                "ID": str(inquiry["_id"]),
                "User ID": inquiry.get("user_id", ""),
                "Property ID": inquiry.get("property_id", ""),
                "Message": inquiry.get("message", ""),
                "Status": inquiry.get("status", ""),
                "Created At": inquiry.get("created_at", "")
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Inquiries', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_leads_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate CRM leads report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query_filter = {
            "created_at": {"$gte": start_date, "$lt": end_date}
        }
        
        cursor = self.db.crm_leads.find(query_filter)
        leads = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for lead in leads:
            data.append({
                "ID": str(lead["_id"]),
                "Name": lead.get("name", ""),
                "Email": lead.get("email", ""),
                "Phone": lead.get("phone", ""),
                "Source": lead.get("source", ""),
                "Status": lead.get("status", ""),
                "Pipeline Stage": lead.get("pipeline_stage", ""),
                "Created At": lead.get("created_at", "")
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='CRM Leads', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_broker_performance_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate broker performance report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        cursor = self.db.brokers.find({"is_active": True})
        brokers = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for broker in brokers:
            data.append({
                "ID": str(broker["_id"]),
                "Name": broker.get("name", ""),
                "Email": broker.get("email", ""),
                "Phone": broker.get("phone", ""),
                "Agency": broker.get("agency_name", ""),
                "Rating": broker.get("rating", 0),
                "Total Deals": broker.get("total_deals", 0),
                "Specialization": ", ".join(broker.get("specialization", [])),
                "Verified": broker.get("is_verified", False)
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Broker Performance', index=False)
        
        output.seek(0)
        return output.getvalue()
    
    async def generate_rental_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bytes:
        """Generate rental properties report"""
        if not start_date:
            start_date = datetime.utcnow() - timedelta(days=30)
        if not end_date:
            end_date = datetime.utcnow()
        
        query_filter = {
            "listing_type": "rent",
            "created_at": {"$gte": start_date, "$lt": end_date}
        }
        
        cursor = self.db.properties.find(query_filter)
        properties = await cursor.to_list(length=1000)
        
        # Prepare data
        data = []
        for prop in properties:
            data.append({
                "ID": str(prop["_id"]),
                "Title": prop.get("title", ""),
                "Type": prop.get("property_type", ""),
                "Price": prop.get("price", 0),
                "Rent Period": prop.get("rent_period", ""),
                "Deposit": prop.get("deposit_amount", 0),
                "Lease Duration": prop.get("lease_duration", ""),
                "Furnished": prop.get("furnished", False),
                "Pets Allowed": prop.get("pets_allowed", False),
                "Location": prop.get("location", ""),
                "City": prop.get("city", ""),
                "Bedrooms": prop.get("bedrooms", 0),
                "Bathrooms": prop.get("bathrooms", 0),
                "Status": prop.get("status", ""),
                "Broker": prop.get("broker_name", "")
            })
        
        df = pd.DataFrame(data)
        
        # Generate Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Rental Properties', index=False)
        
        output.seek(0)
        return output.getvalue()
