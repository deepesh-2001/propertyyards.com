"""
Interview Router
Handles interview scheduling, invitations, feedback, and workflow management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    InterviewScheduleCreate,
    InterviewScheduleResponse,
    InterviewInvitationCreate,
    InterviewInvitationResponse,
    InterviewFeedbackCreate,
    InterviewFeedbackResponse,
    InterviewWorkflowCreate,
    InterviewWorkflowResponse,
    InterviewStatus,
    InterviewType,
    InterviewMode,
    InterviewRound
)
from app.interview import interview_manager
from app.auth import get_current_user

router = APIRouter(prefix="/api/interviews", tags=["interviews"])


# ========== Interview Scheduling Endpoints ==========

@router.post("/schedule", response_model=InterviewScheduleResponse, status_code=status.HTTP_201_CREATED)
async def schedule_interview(
    schedule: InterviewScheduleCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Schedule a new interview"""
    try:
        interview = await interview_manager.schedule_interview(schedule, database)
        return interview
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/schedule/{interview_id}", response_model=InterviewScheduleResponse)
async def get_interview_schedule(
    interview_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get interview schedule details"""
    interview = await database.interview_schedules.find_one({"_id": interview_id})
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview["id"] = str(interview["_id"])
    del interview["_id"]
    
    return InterviewScheduleResponse(**interview)


@router.get("/schedule/candidate/{candidate_id}")
async def get_candidate_interviews(
    candidate_id: str,
    status: Optional[InterviewStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get interviews for a candidate"""
    query = {"candidate_id": candidate_id}
    if status:
        query["status"] = status
    
    cursor = database.interview_schedules.find(query).sort("scheduled_date", -1)
    interviews = await cursor.to_list(length=50)
    
    for interview in interviews:
        interview["id"] = str(interview["_id"])
        del interview["_id"]
    
    return [InterviewScheduleResponse(**i) for i in interviews]


@router.get("/schedule/interviewer/{interviewer_id}")
async def get_interviewer_interviews(
    interviewer_id: str,
    status: Optional[InterviewStatus] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get interviews for an interviewer"""
    query = {"interviewer_id": interviewer_id}
    if status:
        query["status"] = status
    if start_date:
        query["scheduled_date"] = {"$gte": start_date}
    if end_date:
        query["scheduled_date"] = query.get("scheduled_date", {})
        query["scheduled_date"]["$lte"] = end_date
    
    cursor = database.interview_schedules.find(query).sort("scheduled_date", 1)
    interviews = await cursor.to_list(length=100)
    
    for interview in interviews:
        interview["id"] = str(interview["_id"])
        del interview["_id"]
    
    return [InterviewScheduleResponse(**i) for i in interviews]


@router.put("/schedule/{interview_id}/status")
async def update_interview_status(
    interview_id: str,
    new_status: InterviewStatus,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update interview status"""
    try:
        await database.interview_schedules.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "status": new_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"message": "Interview status updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/schedule/{interview_id}")
async def cancel_interview(
    interview_id: str,
    reason: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cancel an interview"""
    try:
        await database.interview_schedules.update_one(
            {"_id": interview_id},
            {
                "$set": {
                    "status": InterviewStatus.CANCELLED,
                    "notes": reason,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"message": "Interview cancelled successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Interview Invitation Endpoints ==========

@router.post("/invitations", response_model=InterviewInvitationResponse, status_code=status.HTTP_201_CREATED)
async def send_interview_invitation(
    interview_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Send interview invitation to candidate"""
    try:
        invitation = await interview_manager.send_interview_invitation(interview_id, database)
        return invitation
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/invitations/{invitation_id}", response_model=InterviewInvitationResponse)
async def get_invitation(
    invitation_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get invitation details"""
    invitation = await database.interview_invitations.find_one({"_id": invitation_id})
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    invitation["id"] = str(invitation["_id"])
    del invitation["_id"]
    
    return InterviewInvitationResponse(**invitation)


@router.put("/invitations/{invitation_id}/respond")
async def respond_to_invitation(
    invitation_id: str,
    response: str,  # accepted or declined
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Respond to interview invitation"""
    try:
        await database.interview_invitations.update_one(
            {"_id": invitation_id},
            {
                "$set": {
                    "status": response,
                    "responded_at": datetime.utcnow()
                }
            }
        )
        
        # Update interview status based on response
        interview = await database.interview_invitations.find_one({"_id": invitation_id})
        if interview:
            new_status = InterviewStatus.CONFIRMED if response == "accepted" else InterviewStatus.CANCELLED
            await database.interview_schedules.update_one(
                {"_id": interview["interview_id"]},
                {
                    "$set": {
                        "status": new_status,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        
        return {"message": f"Invitation {response} successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Interview Feedback Endpoints ==========

@router.post("/feedback", response_model=InterviewFeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_interview_feedback(
    feedback: InterviewFeedbackCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit interview feedback"""
    try:
        feedback_response = await interview_manager.submit_feedback(feedback, database)
        return feedback_response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/feedback/{feedback_id}", response_model=InterviewFeedbackResponse)
async def get_feedback(
    feedback_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get feedback details"""
    feedback = await database.interview_feedback.find_one({"_id": feedback_id})
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found")
    
    feedback["id"] = str(feedback["_id"])
    del feedback["_id"]
    
    return InterviewFeedbackResponse(**feedback)


@router.get("/feedback/interview/{interview_id}")
async def get_interview_feedback(
    interview_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all feedback for an interview"""
    cursor = database.interview_feedback.find({"interview_id": interview_id})
    feedback_list = await cursor.to_list(length=10)
    
    for feedback in feedback_list:
        feedback["id"] = str(feedback["_id"])
        del feedback["_id"]
    
    return [InterviewFeedbackResponse(**f) for f in feedback_list]


@router.get("/feedback/candidate/{candidate_id}")
async def get_candidate_feedback(
    candidate_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all feedback for a candidate"""
    cursor = database.interview_feedback.find({"candidate_id": candidate_id}).sort("created_at", -1)
    feedback_list = await cursor.to_list(length=20)
    
    for feedback in feedback_list:
        feedback["id"] = str(feedback["_id"])
        del feedback["_id"]
    
    return [InterviewFeedbackResponse(**f) for f in feedback_list]


# ========== Interview Workflow Endpoints ==========

@router.post("/workflows", response_model=InterviewWorkflowResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    workflow: InterviewWorkflowCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create interview workflow for a job posting"""
    try:
        if current_user["role"] not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Admin or HR access required")
        
        workflow_response = await interview_manager.workflow_manager.create_workflow(workflow, database)
        return workflow_response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workflows/job/{job_posting_id}", response_model=InterviewWorkflowResponse)
async def get_job_workflow(
    job_posting_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get workflow for a job posting"""
    workflow = await interview_manager.workflow_manager.get_workflow(job_posting_id, database)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return workflow


@router.post("/workflows/advance")
async def advance_candidate_workflow(
    candidate_id: str,
    job_posting_id: str,
    current_step: int,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Advance candidate to next interview step"""
    try:
        result = await interview_manager.workflow_manager.advance_candidate(
            candidate_id,
            job_posting_id,
            current_step,
            database
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Interview Timing and Availability Endpoints ==========

@router.get("/availability/{interviewer_id}")
async def check_interviewer_availability(
    interviewer_id: str,
    date: datetime,
    time: str,
    duration_minutes: int,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if interviewer is available for a slot"""
    try:
        availability = interview_manager.timing_manager.is_slot_available(
            interviewer_id,
            date,
            time,
            duration_minutes,
            database
        )
        return availability
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-slots/{interviewer_id}")
async def get_available_slots(
    interviewer_id: str,
    date: datetime,
    duration_minutes: int,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get available interview slots for an interviewer on a specific date"""
    try:
        slots = interview_manager.timing_manager.suggest_available_slots(
            interviewer_id,
            date,
            duration_minutes,
            database
        )
        return {"slots": slots}
    except Exception as e:
        raise HTTPException(status_code=500, detail(str(e))
