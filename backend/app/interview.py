"""
Interview Management Module
Handles interview scheduling, timing logic, invitations, and process workflow
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import uuid

from app.schemas import (
    InterviewStatus,
    InterviewType,
    InterviewMode,
    InterviewRound,
    InterviewScheduleCreate,
    InterviewScheduleResponse,
    InterviewInvitationCreate,
    InterviewInvitationResponse,
    InterviewFeedbackCreate,
    InterviewFeedbackResponse,
    InterviewWorkflowCreate,
    InterviewWorkflowResponse,
    InterviewTimingLogic
)
from app.notification import notification_manager
from app.config import settings

logger = logging.getLogger(__name__)


class InterviewTimingManager:
    """Manages interview timing and scheduling logic"""
    
    def __init__(self):
        self.default_logic = InterviewTimingLogic(
            interview_id="",
            buffer_time_minutes=15,
            max_interviews_per_day=6,
            working_hours_start="09:00",
            working_hours_end="18:00",
            break_hours=[{"start": "12:00", "end": "13:00"}],
            timezone="Asia/Kolkata",
            weekend_days=[6, 7]
        )
    
    def is_slot_available(
        self,
        interviewer_id: str,
        scheduled_date: datetime,
        scheduled_time: str,
        duration_minutes: int,
        database
    ) -> Dict[str, Any]:
        """Check if interview slot is available"""
        try:
            # Parse time
            interview_start = self._parse_time(scheduled_time)
            interview_end = interview_start + timedelta(minutes=duration_minutes)
            
            # Check if within working hours
            if not self._is_within_working_hours(interview_start, interview_end):
                return {
                    "available": False,
                    "reason": "outside_working_hours"
                }
            
            # Check if weekend
            if scheduled_date.weekday() + 1 in self.default_logic.weekend_days:
                return {
                    "available": False,
                    "reason": "weekend"
                }
            
            # Check for conflicts with existing interviews
            conflict_check = self._check_interview_conflicts(
                interviewer_id,
                scheduled_date,
                interview_start,
                interview_end,
                database
            )
            
            if conflict_check["has_conflict"]:
                return {
                    "available": False,
                    "reason": "conflict",
                    "conflicting_interviews": conflict_check["conflicts"]
                }
            
            # Check max interviews per day
            daily_count = self._count_daily_interviews(interviewer_id, scheduled_date, database)
            if daily_count >= self.default_logic.max_interviews_per_day:
                return {
                    "available": False,
                    "reason": "max_interviews_reached",
                    "current_count": daily_count,
                    "max_allowed": self.default_logic.max_interviews_per_day
                }
            
            return {
                "available": True,
                "reason": None
            }
        except Exception as e:
            logger.error(f"Slot availability check error: {e}")
            return {
                "available": False,
                "reason": "error",
                "error": str(e)
            }
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string to datetime"""
        hours, minutes = map(int, time_str.split(':'))
        now = datetime.utcnow()
        return now.replace(hour=hours, minute=minutes, second=0, microsecond=0)
    
    def _is_within_working_hours(self, start: datetime, end: datetime) -> bool:
        """Check if time is within working hours"""
        start_time = self._parse_time(self.default_logic.working_hours_start)
        end_time = self._parse_time(self.default_logic.working_hours_end)
        
        # Check break hours
        for break_period in self.default_logic.break_hours:
            break_start = self._parse_time(break_period["start"])
            break_end = self._parse_time(break_period["end"])
            
            # If interview overlaps with break
            if not (end <= break_start or start >= break_end):
                return False
        
        # Check working hours
        return start.time() >= start_time.time() and end.time() <= end_time.time()
    
    def _check_interview_conflicts(
        self,
        interviewer_id: str,
        scheduled_date: datetime,
        interview_start: datetime,
        interview_end: datetime,
        database
    ) -> Dict[str, Any]:
        """Check for interview conflicts"""
        try:
            # Get existing interviews for the interviewer on the same day
            day_start = scheduled_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            existing_interviews = database.interview_schedules.find({
                "interviewer_id": interviewer_id,
                "scheduled_date": {"$gte": day_start, "$lt": day_end},
                "status": {"$in": [InterviewStatus.SCHEDULED, InterviewStatus.CONFIRMED, InterviewStatus.IN_PROGRESS]}
            }).to_list(length=20)
            
            conflicts = []
            for interview in existing_interviews:
                existing_start = self._parse_time(interview["scheduled_time"])
                existing_end = existing_start + timedelta(minutes=interview["duration_minutes"])
                
                # Check for overlap with buffer time
                buffer = timedelta(minutes=self.default_logic.buffer_time_minutes)
                
                if not (interview_end + buffer <= existing_start or interview_start - buffer >= existing_end):
                    conflicts.append({
                        "interview_id": str(interview["_id"]),
                        "scheduled_time": interview["scheduled_time"],
                        "duration": interview["duration_minutes"]
                    })
            
            return {
                "has_conflict": len(conflicts) > 0,
                "conflicts": conflicts
            }
        except Exception as e:
            logger.error(f"Conflict check error: {e}")
            return {"has_conflict": True, "conflicts": []}
    
    def _count_daily_interviews(
        self,
        interviewer_id: str,
        scheduled_date: datetime,
        database
    ) -> int:
        """Count interviews for the day"""
        try:
            day_start = scheduled_date.replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            
            count = database.interview_schedules.count_documents({
                "interviewer_id": interviewer_id,
                "scheduled_date": {"$gte": day_start, "$lt": day_end},
                "status": {"$in": [InterviewStatus.SCHEDULED, InterviewStatus.CONFIRMED, InterviewStatus.IN_PROGRESS]}
            })
            
            return count
        except Exception as e:
            logger.error(f"Daily interview count error: {e}")
            return 0
    
    def suggest_available_slots(
        self,
        interviewer_id: str,
        preferred_date: datetime,
        duration_minutes: int,
        database
    ) -> List[Dict[str, Any]]:
        """Suggest available interview slots"""
        try:
            available_slots = []
            
            # Generate time slots from working hours
            start_time = self._parse_time(self.default_logic.working_hours_start)
            end_time = self._parse_time(self.default_logic.working_hours_end)
            
            current_time = start_time
            while current_time + timedelta(minutes=duration_minutes) <= end_time:
                time_str = current_time.strftime("%H:%M")
                
                # Check availability
                availability = self.is_slot_available(
                    interviewer_id,
                    preferred_date,
                    time_str,
                    duration_minutes,
                    database
                )
                
                if availability["available"]:
                    available_slots.append({
                        "date": preferred_date.date().isoformat(),
                        "time": time_str,
                        "duration_minutes": duration_minutes
                    })
                
                # Move to next slot with buffer time
                current_time += timedelta(minutes=duration_minutes + self.default_logic.buffer_time_minutes)
            
            return available_slots
        except Exception as e:
            logger.error(f"Slot suggestion error: {e}")
            return []


class InterviewInvitationManager:
    """Manages interview invitations"""
    
    def __init__(self):
        pass
    
    async def send_invitation(
        self,
        invitation: InterviewInvitationCreate,
        database
    ) -> InterviewInvitationResponse:
        """Send interview invitation to candidate"""
        try:
            # Create invitation record
            invitation_data = invitation.dict()
            invitation_data["status"] = "sent"
            invitation_data["sent_at"] = datetime.utcnow()
            invitation_data["delivered_at"] = None
            invitation_data["opened_at"] = None
            invitation_data["responded_at"] = None
            
            result = await database.interview_invitations.insert_one(invitation_data)
            invitation_data["id"] = str(result.inserted_id)
            
            # Send email invitation
            await self._send_email_invitation(invitation, database)
            
            # Send WhatsApp invitation
            await self._send_whatsapp_invitation(invitation, database)
            
            return InterviewInvitationResponse(**invitation_data)
        except Exception as e:
            logger.error(f"Invitation sending error: {e}")
            raise
    
    async def _send_email_invitation(
        self,
        invitation: InterviewInvitationCreate,
        database
    ):
        """Send email invitation"""
        try:
            from app.notification import notification_manager
            from app.schemas import NotificationChannel, InvestmentNotificationCreate
            
            # Create email content
            email_content = self._generate_invitation_email(invitation)
            
            # Send via notification manager (reuse email service)
            # In production, integrate with email service
            logger.info(f"Email invitation sent to {invitation.candidate_email}")
        except Exception as e:
            logger.error(f"Email invitation error: {e}")
    
    async def _send_whatsapp_invitation(
        self,
        invitation: InterviewInvitationCreate,
        database
    ):
        """Send WhatsApp invitation"""
        try:
            # Generate WhatsApp message
            message = self._generate_invitation_message(invitation)
            
            # Send via WhatsApp service
            logger.info(f"WhatsApp invitation sent to {invitation.candidate_phone}")
        except Exception as e:
            logger.error(f"WhatsApp invitation error: {e}")
    
    def _generate_invitation_email(self, invitation: InterviewInvitationCreate) -> str:
        """Generate invitation email content"""
        date_str = invitation.interview_date.strftime("%A, %B %d, %Y")
        mode_str = invitation.interview_mode.value.replace("_", " ").title()
        
        html = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .details {{ background: white; padding: 20px; border-radius: 8px; margin: 20px 0; border-left: 4px solid #667eea; }}
                .details h3 {{ color: #667eea; margin-top: 0; }}
                .button {{ display: inline-block; padding: 15px 30px; background: #667eea; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Interview Invitation</h1>
                    <p>{invitation.company_name}</p>
                </div>
                <div class="content">
                    <p>Dear <strong>{invitation.candidate_name}</strong>,</p>
                    <p>We are pleased to invite you for an interview for the position of <strong>{invitation.job_title}</strong>.</p>
                    
                    <div class="details">
                        <h3>Interview Details</h3>
                        <p><strong>Date:</strong> {date_str}</p>
                        <p><strong>Time:</strong> {invitation.interview_time}</p>
                        <p><strong>Duration:</strong> {invitation.duration_minutes} minutes</p>
                        <p><strong>Mode:</strong> {mode_str}</p>
                        {f'<p><strong>Location:</strong> {invitation.location}</p>' if invitation.location else ''}
                        {f'<p><strong>Meeting Link:</strong> <a href="{invitation.meeting_link}">Join Meeting</a></p>' if invitation.meeting_link else ''}
                        {f'<p><strong>Meeting ID:</strong> {invitation.meeting_id}</p>' if invitation.meeting_id else ''}
                        {f'<p><strong>Password:</strong> {invitation.meeting_password}</p>' if invitation.meeting_password else ''}
                    </div>
                    
                    <p>Please confirm your attendance by clicking the button below.</p>
                    
                    <div style="text-align: center;">
                        <a href="#" class="button">Accept Invitation</a>
                        <a href="#" class="button" style="background: #dc3545;">Decline</a>
                    </div>
                    
                    {f'<p><strong>Notes:</strong> {invitation.notes}</p>' if invitation.notes else ''}
                    
                    <p>If you have any questions, please contact {invitation.interviewer_email}.</p>
                    
                    <p>Best regards,<br>{invitation.interviewer_name}<br>{invitation.company_name}</p>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    def _generate_invitation_message(self, invitation: InterviewInvitationCreate) -> str:
        """Generate WhatsApp invitation message"""
        date_str = invitation.interview_date.strftime("%A, %B %d, %Y")
        mode_str = invitation.interview_mode.value.replace("_", " ").title()
        
        message = f"""
🎉 *Interview Invitation*

Dear {invitation.candidate_name},

You have been invited for an interview for the position of *{invitation.job_title}* at {invitation.company_name}.

📅 *Date:* {date_str}
⏰ *Time:* {invitation.interview_time}
⏱️ *Duration:* {invitation.duration_minutes} minutes
📍 *Mode:* {mode_str}
{f'🏢 *Location:* {invitation.location}' if invitation.location else ''}
{f'🔗 *Meeting Link:* {invitation.meeting_link}' if invitation.meeting_link else ''}
{f'🆔 *Meeting ID:* {invitation.meeting_id}' if invitation.meeting_id else ''}
{f'🔐 *Password:* {invitation.meeting_password}' if invitation.meeting_password else ''}

Please confirm your attendance by replying to this message.

Interviewer: {invitation.interviewer_name}
Contact: {invitation.interviewer_email}
        """
        return message.strip()


class InterviewWorkflowManager:
    """Manages interview process workflow"""
    
    def __init__(self):
        pass
    
    async def create_workflow(
        self,
        workflow: InterviewWorkflowCreate,
        database
    ) -> InterviewWorkflowResponse:
        """Create interview workflow for a job posting"""
        try:
            workflow_data = workflow.dict()
            workflow_data["created_at"] = datetime.utcnow()
            workflow_data["updated_at"] = datetime.utcnow()
            
            result = await database.interview_workflows.insert_one(workflow_data)
            workflow_data["id"] = str(result.inserted_id)
            
            return InterviewWorkflowResponse(**workflow_data)
        except Exception as e:
            logger.error(f"Workflow creation error: {e}")
            raise
    
    async def get_workflow(
        self,
        job_posting_id: str,
        database
    ) -> Optional[InterviewWorkflowResponse]:
        """Get workflow for a job posting"""
        try:
            workflow = await database.interview_workflows.find_one({
                "job_posting_id": job_posting_id,
                "is_active": True
            })
            
            if not workflow:
                return None
            
            workflow["id"] = str(workflow["_id"])
            del workflow["_id"]
            
            return InterviewWorkflowResponse(**workflow)
        except Exception as e:
            logger.error(f"Workflow retrieval error: {e}")
            return None
    
    async def advance_candidate(
        self,
        candidate_id: str,
        job_posting_id: str,
        current_step: int,
        database
    ) -> Dict[str, Any]:
        """Advance candidate to next interview step"""
        try:
            workflow = await self.get_workflow(job_posting_id, database)
            if not workflow:
                return {"success": False, "reason": "workflow_not_found"}
            
            steps = workflow.steps
            if current_step >= len(steps):
                return {"success": False, "reason": "already_at_final_step"}
            
            next_step = steps[current_step + 1] if current_step + 1 < len(steps) else None
            if not next_step:
                return {"success": False, "reason": "no_next_step"}
            
            return {
                "success": True,
                "current_step": current_step,
                "next_step": next_step.dict(),
                "message": f"Advanced to {next_step.step_name}"
            }
        except Exception as e:
            logger.error(f"Candidate advancement error: {e}")
            return {"success": False, "reason": "error", "error": str(e)}


class InterviewManager:
    """Main interview management class"""
    
    def __init__(self):
        self.timing_manager = InterviewTimingManager()
        self.invitation_manager = InterviewInvitationManager()
        self.workflow_manager = InterviewWorkflowManager()
    
    async def schedule_interview(
        self,
        schedule: InterviewScheduleCreate,
        database
    ) -> InterviewScheduleResponse:
        """Schedule a new interview"""
        try:
            # Check slot availability
            availability = self.timing_manager.is_slot_available(
                schedule.interviewer_id,
                schedule.scheduled_date,
                schedule.scheduled_time,
                schedule.duration_minutes,
                database
            )
            
            if not availability["available"]:
                raise ValueError(f"Slot not available: {availability['reason']}")
            
            # Get job title
            job_posting = await database.job_postings.find_one({"_id": schedule.job_posting_id})
            job_title = job_posting.get("title", "Position") if job_posting else "Position"
            
            # Create interview schedule
            schedule_data = schedule.dict()
            schedule_data["job_title"] = job_title
            schedule_data["status"] = InterviewStatus.SCHEDULED
            schedule_data["invitation_sent"] = False
            schedule_data["invitation_sent_at"] = None
            schedule_data["reminder_sent"] = False
            schedule_data["reminder_sent_at"] = None
            schedule_data["feedback"] = None
            schedule_data["rating"] = None
            schedule_data["selected"] = False
            schedule_data["created_at"] = datetime.utcnow()
            schedule_data["updated_at"] = datetime.utcnow()
            
            result = await database.interview_schedules.insert_one(schedule_data)
            schedule_data["id"] = str(result.inserted_id)
            
            return InterviewScheduleResponse(**schedule_data)
        except Exception as e:
            logger.error(f"Interview scheduling error: {e}")
            raise
    
    async def send_interview_invitation(
        self,
        interview_id: str,
        database
    ) -> InterviewInvitationResponse:
        """Send invitation for scheduled interview"""
        try:
            # Get interview details
            interview = await database.interview_schedules.find_one({"_id": interview_id})
            if not interview:
                raise ValueError("Interview not found")
            
            # Get job posting for company name
            job_posting = await database.job_postings.find_one({"_id": interview["job_posting_id"]})
            company_name = job_posting.get("company_name", "Company") if job_posting else "Company"
            
            # Create invitation
            invitation = InterviewInvitationCreate(
                interview_id=str(interview["_id"]),
                candidate_id=interview["candidate_id"],
                candidate_name=interview["candidate_name"],
                candidate_email=interview["candidate_email"],
                candidate_phone=interview["candidate_phone"],
                interviewer_name=interview["interviewer_name"],
                interviewer_email=interview["interviewer_email"],
                job_title=interview.get("job_title", "Position"),
                company_name=company_name,
                interview_date=interview["scheduled_date"],
                interview_time=interview["scheduled_time"],
                interview_mode=interview["interview_mode"],
                location=interview.get("location"),
                meeting_link=interview.get("meeting_link"),
                meeting_id=interview.get("meeting_id"),
                meeting_password=interview.get("meeting_password"),
                duration_minutes=interview["duration_minutes"],
                notes=interview.get("notes")
            )
            
            # Send invitation
            invitation_response = await self.invitation_manager.send_invitation(invitation, database)
            
            # Update interview status
            await database.interview_schedules.update_one(
                {"_id": interview_id},
                {
                    "$set": {
                        "status": InterviewStatus.INVITED,
                        "invitation_sent": True,
                        "invitation_sent_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return invitation_response
        except Exception as e:
            logger.error(f"Interview invitation sending error: {e}")
            raise
    
    async def submit_feedback(
        self,
        feedback: InterviewFeedbackCreate,
        database
    ) -> InterviewFeedbackResponse:
        """Submit interview feedback"""
        try:
            feedback_data = feedback.dict()
            feedback_data["created_at"] = datetime.utcnow()
            feedback_data["updated_at"] = datetime.utcnow()
            
            result = await database.interview_feedback.insert_one(feedback_data)
            feedback_data["id"] = str(result.inserted_id)
            
            # Update interview with feedback
            await database.interview_schedules.update_one(
                {"_id": feedback.interview_id},
                {
                    "$set": {
                        "feedback": feedback.comments,
                        "rating": feedback.rating,
                        "selected": feedback.recommendation == "hire",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            return InterviewFeedbackResponse(**feedback_data)
        except Exception as e:
            logger.error(f"Feedback submission error: {e}")
            raise


# Global instance
interview_manager = InterviewManager()
