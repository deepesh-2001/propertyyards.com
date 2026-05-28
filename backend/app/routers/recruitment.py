"""
Recruitment Router
Endpoints for job postings, applications, and salary management
"""
from fastapi import APIRouter, Depends, HTTPException
from app.database import get_database
from app.recruitment import Recruitment, SalaryManagement, EmployeeReferral
from app.schemas import (
    JobPostingCreate, JobPostingUpdate, JobPostingResponse,
    JobApplicationCreate, JobApplicationUpdate, JobApplicationResponse,
    SalaryStructureCreate, SalaryStructureUpdate, SalaryStructureResponse, NetSalaryResponse,
    EmployeeReferralCreate, EmployeeReferralUpdate, EmployeeReferralResponse
)
from app.auth import decode_token
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/recruitment", tags=["Recruitment"])


def get_current_user(authorization: str = None) -> dict:
    """Extract current user from authorization header"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        token = authorization.split(" ")[1]
        token_data = decode_token(token)
        if token_data:
            return {"user_id": token_data.user_id, "email": token_data.email, "role": token_data.role}
    except Exception:
        pass

    raise HTTPException(status_code=401, detail="Invalid token")


# ========== Job Posting Endpoints ==========
@router.post("/jobs", response_model=JobPostingResponse)
async def create_job_posting(
    job_data: JobPostingCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create a new job posting"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    recruitment = Recruitment(db)
    job_id = await recruitment.create_job_posting(
        title=job_data.title,
        description=job_data.description,
        department=job_data.department,
        location=job_data.location,
        employment_type=job_data.employment_type,
        experience_level=job_data.experience_level,
        salary_min=job_data.salary_min,
        salary_max=job_data.salary_max,
        requirements=job_data.requirements,
        responsibilities=job_data.responsibilities,
        benefits=job_data.benefits,
        posted_by=current_user["user_id"],
        status=job_data.status
    )
    
    job = await recruitment.get_job_posting(job_id)
    return JobPostingResponse(**job)


@router.get("/jobs/{job_id}", response_model=JobPostingResponse)
async def get_job_posting(
    job_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get job posting by ID"""
    current_user = get_current_user(authorization)
    
    recruitment = Recruitment(db)
    job = await recruitment.get_job_posting(job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    # Increment view count
    await recruitment.update_job_posting(job_id, {"view_count": job.get("view_count", 0) + 1})
    
    return JobPostingResponse(**job)


@router.get("/jobs")
async def list_job_postings(
    status: str = None,
    department: str = None,
    employment_type: str = None,
    page: int = 1,
    limit: int = 50,
    authorization: str = None,
    db = Depends(get_database)
):
    """List job postings with filters"""
    current_user = get_current_user(authorization)
    
    recruitment = Recruitment(db)
    result = await recruitment.list_job_postings(
        status=status,
        department=department,
        employment_type=employment_type,
        skip=(page - 1) * limit,
        limit=limit
    )
    
    return result


@router.put("/jobs/{job_id}", response_model=JobPostingResponse)
async def update_job_posting(
    job_id: str,
    job_update: JobPostingUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update job posting"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    recruitment = Recruitment(db)
    update_data = job_update.dict(exclude_unset=True)
    
    updated = await recruitment.update_job_posting(job_id, update_data)
    if not updated:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    job = await recruitment.get_job_posting(job_id)
    return JobPostingResponse(**job)


@router.delete("/jobs/{job_id}")
async def delete_job_posting(
    job_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Delete job posting"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    recruitment = Recruitment(db)
    deleted = await recruitment.delete_job_posting(job_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Job posting not found")
    
    return {"message": "Job posting deleted successfully"}


# ========== Job Application Endpoints ==========
@router.post("/applications", response_model=JobApplicationResponse)
async def submit_application(
    application_data: JobApplicationCreate,
    db = Depends(get_database)
):
    """Submit job application"""
    recruitment = Recruitment(db)
    application_id = await recruitment.submit_application(
        job_id=application_data.job_id,
        applicant_name=application_data.applicant_name,
        applicant_email=application_data.applicant_email,
        applicant_phone=application_data.applicant_phone,
        resume_url=application_data.resume_url,
        cover_letter=application_data.cover_letter,
        skills=application_data.skills,
        experience_years=application_data.experience_years,
        expected_salary=application_data.expected_salary,
        referral_code=application_data.referral_code
    )
    
    application = await recruitment.get_application(application_id)
    return JobApplicationResponse(**application)


@router.get("/applications/{application_id}", response_model=JobApplicationResponse)
async def get_application(
    application_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get application by ID"""
    current_user = get_current_user(authorization)
    
    recruitment = Recruitment(db)
    application = await recruitment.get_application(application_id)
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return JobApplicationResponse(**application)


@router.get("/applications")
async def list_applications(
    job_id: str = None,
    status: str = None,
    page: int = 1,
    limit: int = 50,
    authorization: str = None,
    db = Depends(get_database)
):
    """List applications with filters"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    recruitment = Recruitment(db)
    result = await recruitment.list_applications(
        job_id=job_id,
        status=status,
        skip=(page - 1) * limit,
        limit=limit
    )
    
    return result


@router.put("/applications/{application_id}")
async def update_application_status(
    application_id: str,
    application_update: JobApplicationUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update application status"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    recruitment = Recruitment(db)
    updated = await recruitment.update_application_status(
        application_id,
        application_update.status,
        application_update.notes
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    
    return {"message": "Application status updated successfully"}


# ========== Salary Management Endpoints ==========
@router.post("/salaries", response_model=SalaryStructureResponse)
async def create_salary_structure(
    salary_data: SalaryStructureCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create salary structure for employee"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    salary_management = SalaryManagement(db)
    salary_id = await salary_management.create_salary_structure(
        employee_id=salary_data.employee_id,
        base_salary=salary_data.base_salary,
        bonus=salary_data.bonus,
        allowances=salary_data.allowances,
        deductions=salary_data.deductions,
        effective_date=salary_data.effective_date
    )
    
    return {"message": "Salary structure created", "salary_id": salary_id}


@router.get("/salaries/{employee_id}/net", response_model=NetSalaryResponse)
async def calculate_net_salary(
    employee_id: str,
    authorization: str = None,
    db = Depends(get_database)
):
    """Calculate net salary for employee"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    salary_management = SalaryManagement(db)
    result = await salary_management.calculate_net_salary(employee_id)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return NetSalaryResponse(**result)


@router.put("/salaries/{employee_id}")
async def update_salary(
    employee_id: str,
    salary_update: SalaryStructureUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update salary structure"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    salary_management = SalaryManagement(db)
    update_data = salary_update.dict(exclude_unset=True)
    
    updated = await salary_management.update_salary(
        employee_id,
        base_salary=update_data.get("base_salary"),
        bonus=update_data.get("bonus"),
        allowances=update_data.get("allowances"),
        deductions=update_data.get("deductions")
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Salary structure not found")
    
    return {"message": "Salary structure updated successfully"}


# ========== Employee Referral Endpoints ==========
@router.post("/referrals", response_model=EmployeeReferralResponse)
async def create_employee_referral(
    referral_data: EmployeeReferralCreate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Create employee referral"""
    current_user = get_current_user(authorization)
    
    employee_referral = EmployeeReferral(db)
    referral_id = await employee_referral.create_referral(
        referrer_id=referral_data.referrer_id,
        referred_name=referral_data.referred_name,
        referred_email=referral_data.referred_email,
        referred_phone=referral_data.referred_phone,
        job_id=referral_data.job_id,
        relationship=referral_data.relationship
    )
    
    referral = await employee_referral.get_referrals(referrer_id=referral_data.referrer_id)
    return EmployeeReferralResponse(**referral["items"][0])


@router.get("/referrals")
async def get_referrals(
    referrer_id: str = None,
    status: str = None,
    page: int = 1,
    limit: int = 50,
    authorization: str = None,
    db = Depends(get_database)
):
    """Get referrals with filters"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    employee_referral = EmployeeReferral(db)
    result = await employee_referral.get_referrals(
        referrer_id=referrer_id,
        status=status,
        skip=(page - 1) * limit,
        limit=limit
    )
    
    return result


@router.put("/referrals/{referral_id}")
async def update_referral_status(
    referral_id: str,
    referral_update: EmployeeReferralUpdate,
    authorization: str = None,
    db = Depends(get_database)
):
    """Update referral status"""
    current_user = get_current_user(authorization)
    
    if current_user["role"] not in ["admin", "hr"]:
        raise HTTPException(status_code=403, detail="HR or admin access required")
    
    employee_referral = EmployeeReferral(db)
    updated = await employee_referral.update_referral_status(
        referral_id,
        referral_update.status,
        referral_update.bonus_amount
    )
    
    if not updated:
        raise HTTPException(status_code=404, detail="Referral not found")
    
    return {"message": "Referral status updated successfully"}
