"""
Attendance and Timing Module
Handles employee attendance tracking, check-in/check-out, and timing records
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging

from app.schemas import (
    AttendanceStatus,
    ShiftType
)

logger = logging.getLogger(__name__)


class AttendanceManager:
    """Attendance management engine"""
    
    def __init__(self):
        self.shift_hours = {
            ShiftType.MORNING: {"start": "09:00", "end": "18:00", "hours": 9},
            ShiftType.AFTERNOON: {"start": "12:00", "end": "21:00", "hours": 9},
            ShiftType.NIGHT: {"start": "21:00", "end": "06:00", "hours": 9},
            ShiftType.FLEXIBLE: {"start": "00:00", "end": "23:59", "hours": 8},
            ShiftType.ROTATING: {"start": "09:00", "end": "18:00", "hours": 9}
        }
        self.late_threshold_minutes = 30  # Mark as late if 30+ minutes late
        self.half_day_threshold_hours = 4  # Mark as half day if < 4 hours
    
    async def check_in(
        self,
        user_id: str,
        location: Optional[str] = None,
        device_id: Optional[str] = None,
        database
    ) -> Dict[str, Any]:
        """Record employee check-in"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Check if already checked in today
            today = datetime.utcnow().date()
            existing = await database.attendance_records.find_one({
                "user_id": user_id,
                "date": {"$gte": datetime.combine(today, datetime.min.time())}
            })
            
            if existing:
                raise ValueError("Already checked in today")
            
            # Determine shift type
            shift_type = user.get("shift_type", ShiftType.FLEXIBLE)
            
            # Create attendance record
            now = datetime.utcnow()
            attendance = {
                "user_id": user_id,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "date": now,
                "check_in_time": now,
                "check_out_time": None,
                "status": AttendanceStatus.PRESENT,
                "shift_type": shift_type,
                "work_hours": 0,
                "overtime_hours": 0,
                "notes": None,
                "location": location,
                "device_id": device_id,
                "created_at": now,
                "updated_at": now
            }
            
            result = await database.attendance_records.insert_one(attendance)
            attendance["id"] = str(result.inserted_id)
            
            return attendance
            
        except Exception as e:
            logger.error(f"Check-in error: {e}")
            raise
    
    async def check_out(
        self,
        user_id: str,
        location: Optional[str] = None,
        device_id: Optional[str] = None,
        database
    ) -> Dict[str, Any]:
        """Record employee check-out"""
        try:
            # Get today's attendance record
            today = datetime.utcnow().date()
            attendance = await database.attendance_records.find_one({
                "user_id": user_id,
                "date": {"$gte": datetime.combine(today, datetime.min.time())}
            })
            
            if not attendance:
                raise ValueError("No check-in record found for today")
            
            if attendance["check_out_time"]:
                raise ValueError("Already checked out today")
            
            # Calculate work hours
            now = datetime.utcnow()
            check_in = attendance["check_in_time"]
            work_hours = (now - check_in).total_seconds() / 3600
            
            # Determine status based on work hours
            shift_hours = self.shift_hours.get(attendance["shift_type"], {"hours": 8})["hours"]
            
            if work_hours < self.half_day_threshold_hours:
                status = AttendanceStatus.HALF_DAY
            elif work_hours >= shift_hours:
                overtime_hours = work_hours - shift_hours
                status = AttendanceStatus.PRESENT
            else:
                status = AttendanceStatus.PRESENT
                overtime_hours = 0
            
            # Update attendance record
            update_data = {
                "check_out_time": now,
                "status": status,
                "work_hours": work_hours,
                "overtime_hours": overtime_hours,
                "updated_at": now
            }
            
            if location:
                update_data["location"] = location
            if device_id:
                update_data["device_id"] = device_id
            
            await database.attendance_records.update_one(
                {"_id": attendance["_id"]},
                {"$set": update_data}
            )
            
            # Return updated record
            updated = await database.attendance_records.find_one({"_id": attendance["_id"]})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            
            return updated
            
        except Exception as e:
            logger.error(f"Check-out error: {e}")
            raise
    
    async def auto_mark_attendance(
        self,
        database
    ) -> Dict[str, Any]:
        """Auto-mark attendance for employees who didn't check in/out"""
        try:
            today = datetime.utcnow().date()
            start_of_day = datetime.combine(today, datetime.min.time())
            
            # Get all active employees
            employees = await database.users.find({"is_active": True}).to_list(length=1000)
            
            auto_marked = []
            
            for employee in employees:
                # Check if attendance exists for today
                existing = await database.attendance_records.find_one({
                    "user_id": str(employee["_id"]),
                    "date": {"$gte": start_of_day}
                })
                
                if not existing:
                    # Mark as absent
                    attendance = {
                        "user_id": str(employee["_id"]),
                        "user_name": f"{employee.get('first_name', '')} {employee.get('last_name', '')}",
                        "date": datetime.utcnow(),
                        "check_in_time": None,
                        "check_out_time": None,
                        "status": AttendanceStatus.ABSENT,
                        "shift_type": employee.get("shift_type", ShiftType.FLEXIBLE),
                        "work_hours": 0,
                        "overtime_hours": 0,
                        "notes": "Auto-marked as absent",
                        "location": None,
                        "device_id": None,
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    
                    result = await database.attendance_records.insert_one(attendance)
                    auto_marked.append(str(result.inserted_id))
            
            return {
                "auto_marked_count": len(auto_marked),
                "auto_marked_ids": auto_marked,
                "processed_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Auto-mark attendance error: {e}")
            raise
    
    async def calculate_attendance_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        database
    ) -> Dict[str, Any]:
        """Calculate attendance summary for a user"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": user_id})
            user_name = f"{user.get('first_name', '')} {user.get('last_name', '')}" if user else ""
            
            # Get attendance records
            records = await database.attendance_records.find({
                "user_id": user_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=1000)
            
            # Calculate summary
            total_days = len(records)
            present_days = sum(1 for r in records if r["status"] == AttendanceStatus.PRESENT)
            absent_days = sum(1 for r in records if r["status"] == AttendanceStatus.ABSENT)
            late_days = sum(1 for r in records if r["status"] == AttendanceStatus.LATE)
            half_days = sum(1 for r in records if r["status"] == AttendanceStatus.HALF_DAY)
            wfh_days = sum(1 for r in records if r["status"] == AttendanceStatus.WORK_FROM_HOME)
            leave_days = sum(1 for r in records if r["status"] == AttendanceStatus.ON_LEAVE)
            
            total_work_hours = sum(r["work_hours"] for r in records)
            total_overtime_hours = sum(r["overtime_hours"] for r in records)
            average_work_hours = total_work_hours / total_days if total_days > 0 else 0
            
            attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0
            
            return {
                "user_id": user_id,
                "user_name": user_name,
                "period_start": start_date,
                "period_end": end_date,
                "total_days": total_days,
                "present_days": present_days,
                "absent_days": absent_days,
                "late_days": late_days,
                "half_days": half_days,
                "work_from_home_days": wfh_days,
                "leave_days": leave_days,
                "total_work_hours": total_work_hours,
                "total_overtime_hours": total_overtime_hours,
                "average_work_hours": average_work_hours,
                "attendance_percentage": attendance_percentage
            }
            
        except Exception as e:
            logger.error(f"Attendance summary calculation error: {e}")
            raise


class TimingManager:
    """Timing and time tracking engine"""
    
    def __init__(self):
        pass
    
    async def start_timer(
        self,
        user_id: str,
        activity: str,
        project_id: Optional[str] = None,
        task_id: Optional[str] = None,
        description: Optional[str] = None,
        is_billable: bool = True,
        database
    ) -> Dict[str, Any]:
        """Start a timing record"""
        try:
            # Get user details
            user = await database.users.find_one({"_id": user_id})
            if not user:
                raise ValueError("User not found")
            
            # Check if there's an active timer
            active = await database.timing_records.find_one({
                "user_id": user_id,
                "end_time": None
            })
            
            if active:
                raise ValueError("Active timer already running")
            
            # Get project and task names
            project_name = None
            if project_id:
                project = await database.projects.find_one({"_id": project_id})
                project_name = project.get("name") if project else None
            
            task_name = None
            if task_id:
                task = await database.tasks.find_one({"_id": task_id})
                task_name = task.get("name") if task else None
            
            # Create timing record
            now = datetime.utcnow()
            timing = {
                "user_id": user_id,
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "date": now,
                "project_id": project_id,
                "project_name": project_name,
                "task_id": task_id,
                "task_name": task_name,
                "start_time": now,
                "end_time": None,
                "duration": 0,
                "activity": activity,
                "description": description,
                "is_billable": is_billable,
                "created_at": now,
                "updated_at": now
            }
            
            result = await database.timing_records.insert_one(timing)
            timing["id"] = str(result.inserted_id)
            
            return timing
            
        except Exception as e:
            logger.error(f"Start timer error: {e}")
            raise
    
    async def stop_timer(
        self,
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Stop the active timing record"""
        try:
            # Get active timer
            timing = await database.timing_records.find_one({
                "user_id": user_id,
                "end_time": None
            })
            
            if not timing:
                raise ValueError("No active timer found")
            
            # Calculate duration
            now = datetime.utcnow()
            start_time = timing["start_time"]
            duration = (now - start_time).total_seconds() / 3600  # in hours
            
            # Update timing record
            await database.timing_records.update_one(
                {"_id": timing["_id"]},
                {
                    "$set": {
                        "end_time": now,
                        "duration": duration,
                        "updated_at": now
                    }
                }
            )
            
            # Return updated record
            updated = await database.timing_records.find_one({"_id": timing["_id"]})
            updated["id"] = str(updated["_id"])
            del updated["_id"]
            
            return updated
            
        except Exception as e:
            logger.error(f"Stop timer error: {e}")
            raise
    
    async def get_timing_summary(
        self,
        user_id: str,
        start_date: datetime,
        end_date: datetime,
        database
    ) -> Dict[str, Any]:
        """Get timing summary for a user"""
        try:
            # Get timing records
            records = await database.timing_records.find({
                "user_id": user_id,
                "date": {"$gte": start_date, "$lte": end_date}
            }).to_list(length=1000)
            
            # Calculate summary
            total_records = len(records)
            total_hours = sum(r["duration"] for r in records)
            billable_hours = sum(r["duration"] for r in records if r["is_billable"])
            non_billable_hours = total_hours - billable_hours
            
            # Group by activity
            by_activity = {}
            for r in records:
                activity = r["activity"]
                by_activity[activity] = by_activity.get(activity, 0) + r["duration"]
            
            # Group by project
            by_project = {}
            for r in records:
                project = r.get("project_name", "No Project")
                by_project[project] = by_project.get(project, 0) + r["duration"]
            
            return {
                "user_id": user_id,
                "period_start": start_date,
                "period_end": end_date,
                "total_records": total_records,
                "total_hours": total_hours,
                "billable_hours": billable_hours,
                "non_billable_hours": non_billable_hours,
                "by_activity": by_activity,
                "by_project": by_project
            }
            
        except Exception as e:
            logger.error(f"Timing summary error: {e}")
            raise


# Global manager instances
attendance_manager = AttendanceManager()
timing_manager = TimingManager()
