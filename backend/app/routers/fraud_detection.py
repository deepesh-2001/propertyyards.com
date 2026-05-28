"""
Fraud Detection and RBI Compliance Router
Endpoints for transaction monitoring, fraud detection, KYC verification, and secure payment processing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.schemas import (
    FraudAlertCreate,
    FraudAlertResponse,
    TransactionMonitoringLog,
    KYCVerificationCreate,
    KYCVerificationResponse,
    TransactionLimitCheck,
    SecurePaymentRequest,
    SecurePaymentResponse,
    KYCStatus,
    FraudRiskLevel
)
from app.fraud_detection import (
    transaction_monitor,
    kyc_verifier,
    secure_payment_processor,
    fraud_detection_engine
)
from app.auth import get_current_user

router = APIRouter(prefix="/api/fraud-detection", tags=["fraud-detection"])


# ========== Transaction Monitoring Endpoints ==========

@router.post("/check-limits", response_model=TransactionLimitCheck)
async def check_transaction_limits(
    user_id: str,
    amount: float,
    transaction_type: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check transaction limits as per RBI guidelines"""
    try:
        limit_check = await transaction_monitor.check_transaction_limits(
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            database=database
        )
        return limit_check
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/log-transaction", response_model=TransactionMonitoringLog)
async def log_transaction(
    transaction_data: dict,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Log transaction for fraud monitoring"""
    try:
        log = await transaction_monitor.log_transaction(transaction_data, database)
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitoring-logs/{user_id}")
async def get_transaction_monitoring_logs(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    risk_level: Optional[FraudRiskLevel] = None,
    skip: int = 0,
    limit: int = 50,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get transaction monitoring logs for a user"""
    query = {"user_id": user_id}
    if start_date:
        query["created_at"] = {"$gte": start_date}
    if end_date:
        query["created_at"] = query.get("created_at", {})
        query["created_at"]["$lte"] = end_date
    if risk_level:
        query["risk_level"] = risk_level
    
    cursor = database.transaction_monitoring_logs.find(query).sort("created_at", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    
    for log in logs:
        log["id"] = str(log["_id"])
        del log["_id"]
    
    total = await database.transaction_monitoring_logs.count_documents(query)
    
    return {
        "items": logs,
        "total": total,
        "skip": skip,
        "limit": limit
    }


# ========== Fraud Alert Endpoints ==========

@router.post("/fraud-alerts", response_model=FraudAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_fraud_alert(
    alert: FraudAlertCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a fraud alert manually"""
    try:
        alert_data = alert.dict()
        alert_data["user_name"] = f"{current_user.get('first_name', '')} {current_user.get('last_name', '')}"
        alert_data["status"] = "open"
        alert_data["action_taken"] = None
        alert_data["resolved_by"] = None
        alert_data["resolved_at"] = None
        alert_data["created_at"] = datetime.utcnow()
        alert_data["updated_at"] = datetime.utcnow()
        
        result = await database.fraud_alerts.insert_one(alert_data)
        alert_data["id"] = str(result.inserted_id)
        
        return FraudAlertResponse(**alert_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fraud-alerts/{alert_id}", response_model=FraudAlertResponse)
async def get_fraud_alert(
    alert_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get fraud alert details"""
    alert = await database.fraud_alerts.find_one({"_id": alert_id})
    if not alert:
        raise HTTPException(status_code=404, detail="Fraud alert not found")
    
    alert["id"] = str(alert["_id"])
    del alert["_id"]
    
    return FraudAlertResponse(**alert)


@router.get("/fraud-alerts")
async def list_fraud_alerts(
    status: Optional[str] = None,
    risk_level: Optional[FraudRiskLevel] = None,
    skip: int = 0,
    limit: int = 50,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List fraud alerts with filters"""
    query = {}
    if status:
        query["status"] = status
    if risk_level:
        query["risk_level"] = risk_level
    
    cursor = database.fraud_alerts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    alerts = await cursor.to_list(length=limit)
    
    for alert in alerts:
        alert["id"] = str(alert["_id"])
        del alert["_id"]
    
    total = await database.fraud_alerts.count_documents(query)
    
    return {
        "items": alerts,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.put("/fraud-alerts/{alert_id}/resolve")
async def resolve_fraud_alert(
    alert_id: str,
    action_taken: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Resolve a fraud alert"""
    try:
        await database.fraud_alerts.update_one(
            {"_id": alert_id},
            {
                "$set": {
                    "status": "resolved",
                    "action_taken": action_taken,
                    "resolved_by": current_user["user_id"],
                    "resolved_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"message": "Fraud alert resolved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== KYC Verification Endpoints ==========

@router.post("/kyc/submit", response_model=KYCVerificationResponse, status_code=status.HTTP_201_CREATED)
async def submit_kyc(
    kyc_data: KYCVerificationCreate,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit KYC verification request"""
    try:
        kyc = await kyc_verifier.submit_kyc(kyc_data, database)
        return kyc
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kyc/user/{user_id}")
async def get_user_kyc_status(
    user_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user KYC verification status"""
    try:
        kyc_status = await kyc_verifier.verify_user_kyc_status(user_id, database)
        return kyc_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/kyc/verifications/{verification_id}", response_model=KYCVerificationResponse)
async def get_kyc_verification(
    verification_id: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get KYC verification details"""
    verification = await database.kyc_verifications.find_one({"_id": verification_id})
    if not verification:
        raise HTTPException(status_code=404, detail="KYC verification not found")
    
    verification["id"] = str(verification["_id"])
    del verification["_id"]
    
    return KYCVerificationResponse(**verification)


@router.put("/kyc/verifications/{verification_id}/approve")
async def approve_kyc(
    verification_id: str,
    verification_score: float,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Approve KYC verification"""
    try:
        if current_user["role"] not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Admin or HR access required")
        
        await database.kyc_verifications.update_one(
            {"_id": verification_id},
            {
                "$set": {
                    "status": KYCStatus.VERIFIED,
                    "verification_score": verification_score,
                    "verified_by": current_user["user_id"],
                    "verified_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"message": "KYC verification approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/kyc/verifications/{verification_id}/reject")
async def reject_kyc(
    verification_id: str,
    rejection_reason: str,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Reject KYC verification"""
    try:
        if current_user["role"] not in ["admin", "hr"]:
            raise HTTPException(status_code=403, detail="Admin or HR access required")
        
        await database.kyc_verifications.update_one(
            {"_id": verification_id},
            {
                "$set": {
                    "status": KYCStatus.REJECTED,
                    "rejection_reason": rejection_reason,
                    "verified_by": current_user["user_id"],
                    "verified_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        return {"message": "KYC verification rejected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ========== Secure Payment Processing Endpoints ==========

@router.post("/secure-payment", response_model=SecurePaymentResponse)
async def process_secure_payment(
    payment_request: SecurePaymentRequest,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Process payment with RBI compliance checks"""
    try:
        result = await secure_payment_processor.process_secure_payment(payment_request, database)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze-transaction")
async def analyze_transaction_fraud(
    transaction_data: dict,
    database=Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Analyze transaction for fraud risk"""
    try:
        analysis = await fraud_detection_engine.analyze_transaction(transaction_data, database)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
