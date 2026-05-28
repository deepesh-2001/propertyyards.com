"""
Fraud Detection and RBI Compliance Module
Handles transaction monitoring, fraud detection, KYC verification, and secure payment processing
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import logging
import hashlib
import re

from app.schemas import (
    FraudRiskLevel,
    TransactionStatus,
    KYCStatus,
    FraudAlertCreate,
    FraudAlertResponse,
    TransactionMonitoringLog,
    KYCVerificationCreate,
    KYCVerificationResponse,
    TransactionLimitCheck,
    SecurePaymentRequest,
    SecurePaymentResponse
)
from app.config import settings

logger = logging.getLogger(__name__)


class FraudDetectionEngine:
    """Fraud detection engine with RBI compliance rules"""
    
    def __init__(self):
        self.rules = self._initialize_rbi_rules()
    
    def _initialize_rbi_rules(self) -> List[Dict[str, Any]]:
        """Initialize RBI compliance fraud detection rules"""
        return [
            {
                "rule_id": "amount_threshold",
                "rule_name": "High Amount Transaction",
                "rule_type": "amount_threshold",
                "threshold_value": settings.MAX_TRANSACTION_AMOUNT,
                "severity": FraudRiskLevel.HIGH,
                "is_active": True
            },
            {
                "rule_id": "velocity_check",
                "rule_name": "High Transaction Velocity",
                "rule_type": "velocity_check",
                "threshold_value": 5,  # max 5 transactions in 10 minutes
                "time_window_minutes": 10,
                "severity": FraudRiskLevel.MEDIUM,
                "is_active": True
            },
            {
                "rule_id": "daily_limit",
                "rule_name": "Daily Transaction Limit",
                "rule_type": "amount_threshold",
                "threshold_value": settings.MAX_DAILY_TRANSACTION_AMOUNT,
                "time_window_minutes": 1440,  # 24 hours
                "severity": FraudRiskLevel.HIGH,
                "is_active": True
            },
            {
                "rule_id": "monthly_limit",
                "rule_name": "Monthly Transaction Limit",
                "rule_type": "amount_threshold",
                "threshold_value": settings.MAX_MONTHLY_TRANSACTION_AMOUNT,
                "time_window_minutes": 43200,  # 30 days
                "severity": FraudRiskLevel.CRITICAL,
                "is_active": True
            },
            {
                "rule_id": "geo_anomaly",
                "rule_name": "Geolocation Anomaly",
                "rule_type": "geo_anomaly",
                "severity": FraudRiskLevel.HIGH,
                "is_active": settings.GEOLOCATION_VERIFICATION
            },
            {
                "rule_id": "device_anomaly",
                "rule_name": "Device Fingerprint Anomaly",
                "rule_type": "device_anomaly",
                "severity": FraudRiskLevel.MEDIUM,
                "is_active": settings.DEVICE_FINGERPRINTING
            }
        ]
    
    async def analyze_transaction(
        self,
        transaction_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Analyze transaction for fraud risk"""
        try:
            risk_score = 0.0
            risk_factors = []
            triggered_rules = []
            
            # Check each rule
            for rule in self.rules:
                if not rule["is_active"]:
                    continue
                
                rule_result = await self._check_rule(rule, transaction_data, database)
                if rule_result["triggered"]:
                    risk_score += rule_result["risk_score"]
                    risk_factors.extend(rule_result["risk_factors"])
                    triggered_rules.append(rule["rule_id"])
            
            # Determine risk level
            risk_level = self._calculate_risk_level(risk_score)
            
            return {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "risk_factors": risk_factors,
                "triggered_rules": triggered_rules,
                "blocked": risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL] and settings.AUTO_BLOCK_SUSPICIOUS_ACCOUNTS
            }
        except Exception as e:
            logger.error(f"Transaction analysis error: {e}")
            return {
                "risk_score": 0.0,
                "risk_level": FraudRiskLevel.LOW,
                "risk_factors": [],
                "triggered_rules": [],
                "blocked": False
            }
    
    async def _check_rule(
        self,
        rule: Dict[str, Any],
        transaction_data: Dict[str, Any],
        database
    ) -> Dict[str, Any]:
        """Check individual fraud detection rule"""
        triggered = False
        risk_score = 0.0
        risk_factors = []
        
        if rule["rule_type"] == "amount_threshold":
            triggered = transaction_data["amount"] > rule["threshold_value"]
            if triggered:
                risk_score = 50.0 if rule["severity"] == FraudRiskLevel.HIGH else 30.0
                risk_factors.append(f"Transaction amount exceeds {rule['rule_name']} threshold")
        
        elif rule["rule_type"] == "velocity_check":
            # Check transaction velocity
            time_window = datetime.utcnow() - timedelta(minutes=rule["time_window_minutes"])
            recent_transactions = await database.payments.count_documents({
                "user_id": transaction_data["user_id"],
                "created_at": {"$gte": time_window}
            })
            triggered = recent_transactions >= rule["threshold_value"]
            if triggered:
                risk_score = 25.0
                risk_factors.append(f"High transaction velocity: {recent_transactions} transactions in {rule['time_window_minutes']} minutes")
        
        elif rule["rule_type"] == "geo_anomaly":
            # Check geolocation anomaly
            if transaction_data.get("geolocation"):
                user_last_location = await database.users.find_one(
                    {"_id": transaction_data["user_id"]},
                    {"last_known_location": 1}
                )
                if user_last_location and user_last_location.get("last_known_location"):
                    distance = self._calculate_distance(
                        transaction_data["geolocation"],
                        user_last_location["last_known_location"]
                    )
                    if distance > 500:  # 500 km threshold
                        triggered = True
                        risk_score = 40.0
                        risk_factors.append(f"Geolocation anomaly: {distance} km from last known location")
        
        elif rule["rule_type"] == "device_anomaly":
            # Check device fingerprint anomaly
            if transaction_data.get("device_fingerprint"):
                user_last_device = await database.users.find_one(
                    {"_id": transaction_data["user_id"]},
                    {"last_device_fingerprint": 1}
                )
                if user_last_device and user_last_device.get("last_device_fingerprint"):
                    if transaction_data["device_fingerprint"] != user_last_device["last_device_fingerprint"]:
                        triggered = True
                        risk_score = 20.0
                        risk_factors.append("New device detected")
        
        return {
            "triggered": triggered,
            "risk_score": risk_score,
            "risk_factors": risk_factors
        }
    
    def _calculate_risk_level(self, risk_score: float) -> FraudRiskLevel:
        """Calculate risk level based on risk score"""
        if risk_score >= 75:
            return FraudRiskLevel.CRITICAL
        elif risk_score >= 50:
            return FraudRiskLevel.HIGH
        elif risk_score >= 25:
            return FraudRiskLevel.MEDIUM
        else:
            return FraudRiskLevel.LOW
    
    def _calculate_distance(self, loc1: Dict[str, Any], loc2: Dict[str, Any]) -> float:
        """Calculate distance between two geolocations (simplified)"""
        # Simplified distance calculation
        lat1 = loc1.get("latitude", 0)
        lon1 = loc1.get("longitude", 0)
        lat2 = loc2.get("latitude", 0)
        lon2 = loc2.get("longitude", 0)
        
        return abs(lat1 - lat2) + abs(lon1 - lon2)  # Simplified for demo


class TransactionMonitor:
    """Transaction monitoring with RBI compliance"""
    
    def __init__(self):
        self.fraud_engine = FraudDetectionEngine()
    
    async def check_transaction_limits(
        self,
        user_id: str,
        amount: float,
        transaction_type: str,
        database
    ) -> TransactionLimitCheck:
        """Check transaction limits as per RBI guidelines"""
        try:
            # Get daily total
            today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            daily_transactions = await database.payments.find({
                "user_id": user_id,
                "status": "completed",
                "created_at": {"$gte": today_start}
            }).to_list(length=100)
            daily_total = sum(t["amount"] for t in daily_transactions)
            
            # Get monthly total
            month_start = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            monthly_transactions = await database.payments.find({
                "user_id": user_id,
                "status": "completed",
                "created_at": {"$gte": month_start}
            }).to_list(length=100)
            monthly_total = sum(t["amount"] for t in monthly_transactions)
            
            # Check limits
            within_limits = True
            limit_type = None
            remaining_limit = None
            
            if amount > settings.MAX_TRANSACTION_AMOUNT:
                within_limits = False
                limit_type = "transaction"
                remaining_limit = settings.MAX_TRANSACTION_AMOUNT
            elif daily_total + amount > settings.MAX_DAILY_TRANSACTION_AMOUNT:
                within_limits = False
                limit_type = "daily"
                remaining_limit = settings.MAX_DAILY_TRANSACTION_AMOUNT - daily_total
            elif monthly_total + amount > settings.MAX_MONTHLY_TRANSACTION_AMOUNT:
                within_limits = False
                limit_type = "monthly"
                remaining_limit = settings.MAX_MONTHLY_TRANSACTION_AMOUNT - monthly_total
            
            # Check KYC requirement
            kyc_required = amount >= settings.TRANSACTION_LIMIT_FOR_KYC
            pan_required = amount >= settings.PAN_REQUIRED_ABOVE_AMOUNT
            two_factor_required = settings.TWO_FACTOR_AUTHENTICATION_REQUIRED
            
            return TransactionLimitCheck(
                user_id=user_id,
                transaction_amount=amount,
                transaction_type=transaction_type,
                daily_total=daily_total,
                monthly_total=monthly_total,
                within_limits=within_limits,
                limit_type=limit_type,
                remaining_limit=remaining_limit,
                kyc_required=kyc_required,
                pan_required=pan_required,
                two_factor_required=two_factor_required
            )
        except Exception as e:
            logger.error(f"Transaction limit check error: {e}")
            raise
    
    async def log_transaction(
        self,
        transaction_data: Dict[str, Any],
        database
    ) -> TransactionMonitoringLog:
        """Log transaction for monitoring"""
        try:
            # Analyze transaction for fraud
            fraud_analysis = await self.fraud_engine.analyze_transaction(transaction_data, database)
            
            # Create monitoring log
            log_data = {
                "transaction_id": transaction_data.get("transaction_id", ""),
                "user_id": transaction_data["user_id"],
                "transaction_amount": transaction_data["amount"],
                "transaction_type": transaction_data.get("transaction_type", "payment"),
                "payment_method": transaction_data.get("payment_method", ""),
                "merchant_id": transaction_data.get("merchant_id"),
                "ip_address": transaction_data.get("ip_address"),
                "device_fingerprint": transaction_data.get("device_fingerprint"),
                "geolocation": transaction_data.get("geolocation"),
                "risk_score": fraud_analysis["risk_score"],
                "risk_level": fraud_analysis["risk_level"],
                "status": TransactionStatus.PROCESSING,
                "blocked": fraud_analysis["blocked"],
                "block_reason": fraud_analysis["blocked"] and "Fraud risk detected" or None,
                "additional_checks_performed": fraud_analysis["triggered_rules"],
                "created_at": datetime.utcnow()
            }
            
            result = await database.transaction_monitoring_logs.insert_one(log_data)
            log_data["id"] = str(result.inserted_id)
            
            # Create fraud alert if high risk
            if fraud_analysis["risk_level"] in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
                await self._create_fraud_alert(transaction_data, fraud_analysis, database)
            
            return TransactionMonitoringLog(**log_data)
        except Exception as e:
            logger.error(f"Transaction logging error: {e}")
            raise
    
    async def _create_fraud_alert(
        self,
        transaction_data: Dict[str, Any],
        fraud_analysis: Dict[str, Any],
        database
    ):
        """Create fraud alert"""
        try:
            alert_data = FraudAlertCreate(
                transaction_id=transaction_data.get("transaction_id", ""),
                user_id=transaction_data["user_id"],
                risk_level=fraud_analysis["risk_level"],
                rule_triggered=fraud_analysis["triggered_rules"][0] if fraud_analysis["triggered_rules"] else "unknown",
                risk_factors=fraud_analysis["risk_factors"],
                transaction_amount=transaction_data["amount"],
                transaction_currency=transaction_data.get("currency", "INR"),
                ip_address=transaction_data.get("ip_address"),
                device_id=transaction_data.get("device_fingerprint"),
                location=transaction_data.get("geolocation", {}).get("city") if transaction_data.get("geolocation") else None
            )
            
            await database.fraud_alerts.insert_one(alert_data.dict())
            logger.warning(f"Fraud alert created for transaction {transaction_data.get('transaction_id')}")
        except Exception as e:
            logger.error(f"Fraud alert creation error: {e}")


class KYCVerifier:
    """KYC verification service"""
    
    def __init__(self):
        self.document_validators = {
            "pan_card": self._validate_pan,
            "aadhaar_card": self._validate_aadhaar,
            "passport": self._validate_passport,
            "driving_license": self._validate_driving_license
        }
    
    async def submit_kyc(
        self,
        kyc_data: KYCVerificationCreate,
        database
    ) -> KYCVerificationResponse:
        """Submit KYC verification request"""
        try:
            user = await database.users.find_one({"_id": kyc_data.user_id})
            if not user:
                raise ValueError("User not found")
            
            # Validate document
            validator = self.document_validators.get(kyc_data.document_type.value)
            if validator:
                is_valid = validator(kyc_data.document_number)
                if not is_valid:
                    raise ValueError(f"Invalid {kyc_data.document_type.value} number")
            
            # Create KYC record
            kyc_record = {
                **kyc_data.dict(),
                "user_name": f"{user.get('first_name', '')} {user.get('last_name', '')}",
                "status": KYCStatus.PENDING,
                "verification_score": None,
                "verified_by": None,
                "verified_at": None,
                "rejection_reason": None,
                "expiry_date": None,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = await database.kyc_verifications.insert_one(kyc_record)
            kyc_record["id"] = str(result.inserted_id)
            
            return KYCVerificationResponse(**kyc_record)
        except Exception as e:
            logger.error(f"KYC submission error: {e}")
            raise
    
    def _validate_pan(self, pan_number: str) -> bool:
        """Validate PAN card number format"""
        # PAN format: 5 letters + 4 digits + 1 letter
        pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]{1}$'
        return bool(re.match(pattern, pan_number.upper()))
    
    def _validate_aadhaar(self, aadhaar_number: str) -> bool:
        """Validate Aadhaar number format"""
        # Aadhaar format: 12 digits
        pattern = r'^[0-9]{12}$'
        return bool(re.match(pattern, aadhaar_number))
    
    def _validate_passport(self, passport_number: str) -> bool:
        """Validate passport number format"""
        # Passport format: varies by country, simplified check
        pattern = r'^[A-Z0-9]{6,9}$'
        return bool(re.match(pattern, passport_number.upper()))
    
    def _validate_driving_license(self, dl_number: str) -> bool:
        """Validate driving license number format"""
        # DL format: varies by state, simplified check
        pattern = r'^[A-Z]{2}[0-9]{13}$'
        return bool(re.match(pattern, dl_number.upper()))
    
    async def verify_user_kyc_status(
        self,
        user_id: str,
        database
    ) -> Dict[str, Any]:
        """Check user KYC verification status"""
        try:
            kyc_records = await database.kyc_verifications.find({
                "user_id": user_id,
                "status": KYCStatus.VERIFIED
            }).to_list(length=10)
            
            if not kyc_records:
                return {
                    "kyc_verified": False,
                    "status": KYCStatus.NOT_STARTED,
                    "documents_verified": []
                }
            
            documents_verified = [r["document_type"] for r in kyc_records]
            
            return {
                "kyc_verified": True,
                "status": KYCStatus.VERIFIED,
                "documents_verified": documents_verified,
                "last_verified": kyc_records[0]["verified_at"]
            }
        except Exception as e:
            logger.error(f"KYC status check error: {e}")
            return {
                "kyc_verified": False,
                "status": KYCStatus.NOT_STARTED,
                "documents_verified": []
            }


class SecurePaymentProcessor:
    """Secure payment processing with RBI compliance"""
    
    def __init__(self):
        self.transaction_monitor = TransactionMonitor()
        self.kyc_verifier = KYCVerifier()
    
    async def process_secure_payment(
        self,
        payment_request: SecurePaymentRequest,
        database
    ) -> SecurePaymentResponse:
        """Process payment with RBI compliance checks"""
        try:
            # Check transaction limits
            limit_check = await self.transaction_monitor.check_transaction_limits(
                payment_request.user_id,
                payment_request.amount,
                "payment",
                database
            )
            
            if not limit_check.within_limits:
                return SecurePaymentResponse(
                    transaction_id="",
                    status=TransactionStatus.BLOCKED,
                    amount=payment_request.amount,
                    currency=payment_request.currency,
                    risk_score=100.0,
                    risk_level=FraudRiskLevel.CRITICAL,
                    kyc_verified=False,
                    pan_verified=False,
                    two_factor_verified=False,
                    requires_additional_verification=True,
                    verification_required=["limit_exceeded"],
                    blocked=True,
                    block_reason=f"Transaction limit exceeded: {limit_check.limit_type}",
                    created_at=datetime.utcnow()
                )
            
            # Check KYC status
            kyc_status = await self.kyc_verifier.verify_user_kyc_status(payment_request.user_id, database)
            kyc_verified = kyc_status["kyc_verified"]
            
            # Verify PAN if required
            pan_verified = True
            if limit_check.pan_required:
                pan_verified = payment_request.pan_number is not None
            
            # Verify 2FA if required
            two_factor_verified = True
            if limit_check.two_factor_required:
                two_factor_verified = payment_request.two_factor_otp is not None
            
            # Log transaction for monitoring
            transaction_data = payment_request.dict()
            transaction_data["transaction_type"] = "payment"
            await self.transaction_monitor.log_transaction(transaction_data, database)
            
            # Determine if additional verification required
            verification_required = []
            if limit_check.kyc_required and not kyc_verified:
                verification_required.append("kyc")
            if limit_check.pan_required and not pan_verified:
                verification_required.append("pan")
            if limit_check.two_factor_required and not two_factor_verified:
                verification_required.append("two_factor")
            
            requires_additional_verification = len(verification_required) > 0
            
            # Calculate initial risk score
            risk_score = 0.0
            if not kyc_verified:
                risk_score += 20.0
            if not pan_verified and limit_check.pan_required:
                risk_score += 15.0
            if not two_factor_verified and limit_check.two_factor_required:
                risk_score += 10.0
            
            risk_level = FraudRiskLevel.LOW if risk_score < 25 else FraudRiskLevel.MEDIUM
            
            return SecurePaymentResponse(
                transaction_id=f"txn_{datetime.utcnow().timestamp()}",
                status=TransactionStatus.PENDING if not requires_additional_verification else TransactionStatus.UNDER_REVIEW,
                amount=payment_request.amount,
                currency=payment_request.currency,
                risk_score=risk_score,
                risk_level=risk_level,
                kyc_verified=kyc_verified,
                pan_verified=pan_verified,
                two_factor_verified=two_factor_verified,
                requires_additional_verification=requires_additional_verification,
                verification_required=verification_required,
                blocked=False,
                block_reason=None,
                created_at=datetime.utcnow()
            )
        except Exception as e:
            logger.error(f"Secure payment processing error: {e}")
            raise


# Global instances
fraud_detection_engine = FraudDetectionEngine()
transaction_monitor = TransactionMonitor()
kyc_verifier = KYCVerifier()
secure_payment_processor = SecurePaymentProcessor()
