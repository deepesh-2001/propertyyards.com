"""
Attendance Router
Handles employee attendance tracking, check-in/check-out, and timing records
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    AttendanceRecordCreate,
    AttendanceRecordResponse,
    AttendanceSummary,
    TimingRecordCreate,
    TimingRecordResponse,
    AttendanceStatus,
    ShiftType
)
from app.attendance import attendance_manager, timing_manager
from app.auth import get_current_user

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


# ========== Attendance Endpoints ==========

@router.post("/check-in", response_model=AttendanceRecordResponse, status_code=status.HTTP_201_CREATED)
async def check_in(
    location: Optional[str] = None,
    device_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record employee check-in"""
    try:
        attendance = await attendance_manager.check_in(
            user_id=current_user["user_id"],
            location=location,
            device_id=device_id,
            database=database
        )
        return AttendanceRecordResponse(**attendance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/check-out", response_model=AttendanceRecordResponse)
async def check_out(
    location: Optional[str] = None,
    device_id: Optional[str] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Record employee check-out"""
    try:
        attendance = await attendance_manager.check_out(
            user_id=current_user["user_id"],
            location=location,
            device_id=device_id,
            database=database
        )
        return AttendanceRecordResponse(**attendance)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/auto-mark")
async def auto_mark_attendance(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Auto-mark attendance for employees who didn't check-in"""
    try:
        if current_user["role"] not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Admin or HR access required")
        
        result = await attendance_manager.auto_mark_attendance(database)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/records/{record_id}", response_model=AttendanceRecordResponse)
async def get_attendance_record(
    record_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific attendance record"""
    record = await database.attendance_records.find_one({"_id": record_id})
    if not record:
        raise HTTPException(status_code=404, detail="Attendance record not found")
    
    record["id"] = str(record["_id"])
    del record["_id"]
    
    return AttendanceRecordResponse(**record)


@router.get("/users/{user_id}/records", response_model=list[AttendanceRecordResponse])
async def get_user_attendance_records(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    status: Optional[AttendanceStatus] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get attendance records for a user"""
    query = {"user_id": user_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query["date"] = query.get("date", {})
        query["date"]["$lte"] = end_date
    if status:
        query["status"] = status
    
    cursor = database.attendance_records.find(query).sort("date", -1)
    records = await cursor.to_list(length=100)
    
    for record in records:
        record["id"] = str(record["_id"])
        del record["_id"]
    
    return [AttendanceRecordResponse(**r) for r in records]


@router.get("/users/{user_id}/summary", response_model=AttendanceSummary)
async def get_attendance_summary(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get attendance summary for a user"""
    try:
        summary = await attendance_manager.calculate_attendance_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            database=database
        )
        return AttendanceSummary(**summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Timing/Time Tracking Endpoints ==========

@router.post("/timing/start", response_model=TimingRecordResponse, status_code=status.HTTP_201_CREATED)
async def start_timer(
    activity: str,
    project_id: Optional[str] = None,
    task_id: Optional[str] = None,
    description: Optional[str] = None,
    is_billable: bool = True,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start a timing record"""
    try:
        timing = await timing_manager.start_timer(
            user_id=current_user["user_id"],
            activity=activity,
            project_id=project_id,
            task_id=task_id,
            description=description,
            is_billable=is_billable,
            database=database
        )
        return TimingRecordResponse(**timing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timing/stop", response_model=TimingRecordResponse)
async def stop_timer(
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Stop the active timing record"""
    try:
        timing = await timing_manager.stop_timer(
            user_id=current_user["user_id"],
            database=database
        )
        return TimingRecordResponse(**timing)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/timing/users/{user_id}/records", response_model=list[TimingRecordResponse])
async def get_timing_records(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get timing records for a user"""
    query = {"user_id": user_id}
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        query["date"] = query.get("date", {})
        query["date"]["$lte"] = end_date
    
    cursor = database.timing_records.find(query).sort("start_time", -1)
    records = await cursor.to_list(length=100)
    
    for record in records:
        record["id"] = str(record["_id"])
        del record["_id"]
    
    return [TimingRecordResponse(**r) for r in records]


@router.get("/timing/users/{user_id}/summary")
async def get_timing_summary(
    user_id: str,
    start_date: datetime,
    end_date: datetime,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get timing summary for a user"""
    try:
        summary = await timing_manager.get_timing_summary(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date,
            database=database
        )
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
