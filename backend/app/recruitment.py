"""
Recruitment Module
Handles job postings, applications, and salary management
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    """Job posting status"""
    DRAFT = "draft"
    OPEN = "open"
    CLOSED = "closed"
    ON_HOLD = "on_hold"
    FILLED = "filled"


class ApplicationStatus(str, Enum):
    """Application status"""
    PENDING = "pending"
    REVIEWED = "reviewed"
    SHORTLISTED = "shortlisted"
    INTERVIEW_SCHEDULED = "interview_scheduled"
    INTERVIEW_COMPLETED = "interview_completed"
    OFFER_EXTENDED = "offer_extended"
    OFFER_ACCEPTED = "offer_accepted"
    OFFER_DECLINED = "offer_declined"
    REJECTED = "rejected"
    HIRED = "hired"


class EmploymentType(str, Enum):
    """Employment types"""
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"


class ExperienceLevel(str, Enum):
    """Experience levels"""
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    EXECUTIVE = "executive"


class Recruitment:
    """Recruitment management service"""
    
    def __init__(self, database):
        self.db = database
        self.jobs_collection = database.job_postings
        self.applications_collection = database.job_applications
        self.employees_collection = database.employees
        self.salaries_collection = database.salaries
        self.referrals_collection = database.employee_referrals
    
    async def create_job_posting(
        self,
        title: str,
        description: str,
        department: str,
        location: str,
        employment_type: EmploymentType,
        experience_level: ExperienceLevel,
        salary_min: float,
        salary_max: float,
        requirements: List[str],
        responsibilities: List[str],
        benefits: List[str],
        posted_by: str,
        status: JobStatus = JobStatus.DRAFT
    ) -> str:
        """Create a new job posting"""
        job_posting = {
            "title": title,
            "description": description,
            "department": department,
            "location": location,
            "employment_type": employment_type,
            "experience_level": experience_level,
            "salary_min": salary_min,
            "salary_max": salary_max,
            "requirements": requirements,
            "responsibilities": responsibilities,
            "benefits": benefits,
            "posted_by": posted_by,
            "status": status,
            "application_count": 0,
            "view_count": 0,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.jobs_collection.insert_one(job_posting)
        logger.info(f"Job posting created: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_job_posting(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job posting by ID"""
        job = await self.jobs_collection.find_one({"_id": job_id})
        if job:
            job["id"] = str(job["_id"])
            del job["_id"]
        return job
    
    async def list_job_postings(
        self,
        status: Optional[JobStatus] = None,
        department: Optional[str] = None,
        employment_type: Optional[EmploymentType] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List job postings with filters"""
        query_filter = {}
        
        if status:
            query_filter["status"] = status
        if department:
            query_filter["department"] = {"$regex": department, "$options": "i"}
        if employment_type:
            query_filter["employment_type"] = employment_type
        
        total = await self.jobs_collection.count_documents(query_filter)
        cursor = self.jobs_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        jobs = await cursor.to_list(length=limit)
        
        for job in jobs:
            job["id"] = str(job["_id"])
            del job["_id"]
        
        return {
            "items": jobs,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def update_job_posting(
        self,
        job_id: str,
        update_data: Dict[str, Any]
    ) -> bool:
        """Update job posting"""
        update_data["updated_at"] = datetime.utcnow()
        result = await self.jobs_collection.update_one(
            {"_id": job_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def delete_job_posting(self, job_id: str) -> bool:
        """Delete job posting"""
        result = await self.jobs_collection.delete_one({"_id": job_id})
        return result.deleted_count > 0
    
    async def submit_application(
        self,
        job_id: str,
        applicant_name: str,
        applicant_email: str,
        applicant_phone: str,
        resume_url: str,
        cover_letter: str,
        skills: List[str],
        experience_years: int,
        expected_salary: float,
        referral_code: Optional[str] = None
    ) -> str:
        """Submit job application"""
        application = {
            "job_id": job_id,
            "applicant_name": applicant_name,
            "applicant_email": applicant_email,
            "applicant_phone": applicant_phone,
            "resume_url": resume_url,
            "cover_letter": cover_letter,
            "skills": skills,
            "experience_years": experience_years,
            "expected_salary": expected_salary,
            "referral_code": referral_code,
            "status": ApplicationStatus.PENDING,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.applications_collection.insert_one(application)
        
        # Increment application count for job
        await self.jobs_collection.update_one(
            {"_id": job_id},
            {"$inc": {"application_count": 1}}
        )
        
        logger.info(f"Application submitted: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get application by ID"""
        application = await self.applications_collection.find_one({"_id": application_id})
        if application:
            application["id"] = str(application["_id"])
            del application["_id"]
        return application
    
    async def list_applications(
        self,
        job_id: Optional[str] = None,
        status: Optional[ApplicationStatus] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """List applications with filters"""
        query_filter = {}
        
        if job_id:
            query_filter["job_id"] = job_id
        if status:
            query_filter["status"] = status
        
        total = await self.applications_collection.count_documents(query_filter)
        cursor = self.applications_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        applications = await cursor.to_list(length=limit)
        
        for application in applications:
            application["id"] = str(application["_id"])
            del application["_id"]
        
        return {
            "items": applications,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    
    async def update_application_status(
        self,
        application_id: str,
        status: ApplicationStatus,
        notes: Optional[str] = None
    ) -> bool:
        """Update application status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        if notes:
            update_data["notes"] = notes
        
        result = await self.applications_collection.update_one(
            {"_id": application_id},
            {"$set": update_data}
        )
        return result.modified_count > 0


class SalaryManagement:
    """Salary and compensation management"""
    
    def __init__(self, database):
        self.db = database
        self.salaries_collection = database.salaries
        self.payroll_collection = database.payroll
    
    async def create_salary_structure(
        self,
        employee_id: str,
        base_salary: float,
        bonus: float = 0,
        allowances: Dict[str, float] = None,
        deductions: Dict[str, float] = None,
        effective_date: datetime = None
    ) -> str:
        """Create salary structure for employee"""
        salary = {
            "employee_id": employee_id,
            "base_salary": base_salary,
            "bonus": bonus,
            "allowances": allowances or {},
            "deductions": deductions or {},
            "effective_date": effective_date or datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        result = await self.salaries_collection.insert_one(salary)
        logger.info(f"Salary structure created: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def calculate_net_salary(self, employee_id: str) -> Dict[str, Any]:
        """Calculate net salary for employee"""
        salary = await self.salaries_collection.find_one({"employee_id": employee_id})
        if not salary:
            return {"error": "Salary structure not found"}
        
        gross_salary = salary["base_salary"] + salary["bonus"]
        
        # Add allowances
        total_allowances = sum(salary.get("allowances", {}).values())
        gross_salary += total_allowances
        
        # Subtract deductions
        total_deductions = sum(salary.get("deductions", {}).values())
        net_salary = gross_salary - total_deductions
        
        return {
            "employee_id": employee_id,
            "base_salary": salary["base_salary"],
            "bonus": salary["bonus"],
            "total_allowances": total_allowances,
            "total_deductions": total_deductions,
            "gross_salary": gross_salary,
            "net_salary": net_salary
        }
    
    async def update_salary(
        self,
        employee_id: str,
        base_salary: Optional[float] = None,
        bonus: Optional[float] = None,
        allowances: Optional[Dict[str, float]] = None,
        deductions: Optional[Dict[str, float]] = None
    ) -> bool:
        """Update salary structure"""
        update_data = {"updated_at": datetime.utcnow()}
        
        if base_salary is not None:
            update_data["base_salary"] = base_salary
        if bonus is not None:
            update_data["bonus"] = bonus
        if allowances is not None:
            update_data["allowances"] = allowances
        if deductions is not None:
            update_data["deductions"] = deductions
        
        result = await self.salaries_collection.update_one(
            {"employee_id": employee_id},
            {"$set": update_data}
        )
        return result.modified_count > 0


class EmployeeReferral:
    """Employee referral system"""
    
    def __init__(self, database):
        self.db = database
        self.referrals_collection = database.employee_referrals
    
    async def create_referral(
        self,
        referrer_id: str,
        referred_name: str,
        referred_email: str,
        referred_phone: str,
        job_id: str,
        relationship: str
    ) -> str:
        """Create employee referral"""
        referral = {
            "referrer_id": referrer_id,
            "referred_name": referred_name,
            "referred_email": referred_email,
            "referred_phone": referred_phone,
            "job_id": job_id,
            "relationship": relationship,
            "status": "pending",
            "bonus_amount": 0,
            "bonus_paid": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        result = await self.referrals_collection.insert_one(referral)
        logger.info(f"Employee referral created: {result.inserted_id}")
        return str(result.inserted_id)
    
    async def update_referral_status(
        self,
        referral_id: str,
        status: str,
        bonus_amount: Optional[float] = None
    ) -> bool:
        """Update referral status"""
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }
        
        if bonus_amount is not None:
            update_data["bonus_amount"] = bonus_amount
            if status == "hired":
                update_data["bonus_paid"] = True
        
        result = await self.referrals_collection.update_one(
            {"_id": referral_id},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_referrals(
        self,
        referrer_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get referrals with filters"""
        query_filter = {}
        
        if referrer_id:
            query_filter["referrer_id"] = referrer_id
        if status:
            query_filter["status"] = status
        
        total = await self.referrals_collection.count_documents(query_filter)
        cursor = self.referrals_collection.find(query_filter).sort("created_at", -1).skip(skip).limit(limit)
        referrals = await cursor.to_list(length=limit)
        
        for referral in referrals:
            referral["id"] = str(referral["_id"])
            del referral["_id"]
        
        return {
            "items": referrals,
            "total": total,
            "skip": skip,
            "limit": limit
        }
