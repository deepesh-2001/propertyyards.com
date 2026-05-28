# Swagger / OpenAPI Reference — Housing Platform

FastAPI auto-generates interactive docs at runtime. This file is the **human-readable companion** that documents every endpoint group, request/response schemas, auth requirements, and example `curl` calls.

## Live Docs (server must be running)

| Interface | URL |
|-----------|-----|
| **Swagger UI** (interactive) | http://localhost:8000/docs |
| **ReDoc** (readable) | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

> All endpoints except `/api/auth/register`, `/api/auth/login`, and `/health` require  
> `Authorization: Bearer <access_token>` in the request header.

---

## Global Conventions

### Authentication Header
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Standard Error Responses
| Code | Body |
|------|------|
| 400 | `{"detail": "Validation message"}` |
| 401 | `{"detail": "Not authenticated"}` |
| 403 | `{"detail": "Permission denied"}` |
| 404 | `{"detail": "Resource not found"}` |
| 500 | `{"detail": "Internal server error message"}` |

### Pagination (where applicable)
Query params: `page=1&limit=20` — Response includes `items`, `total`, `page`, `pages`.

---

## Auth  `/api/auth`

### POST `/api/auth/register`
Register a new user account.

**Request**
```json
{
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith",
  "phone_number": "+91-9876543210",
  "password": "Secure@123",
  "role": "buyer"
}
```
**Response `201`**
```json
{
  "id": "64f1a...",
  "email": "alice@example.com",
  "first_name": "Alice",
  "last_name": "Smith",
  "role": "buyer",
  "is_active": true,
  "created_at": "2024-05-01T10:00:00"
}
```

---

### POST `/api/auth/login`
**Request**
```json
{ "email": "alice@example.com", "password": "Secure@123" }
```
**Response `200`**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

---

### POST `/api/auth/refresh`
**Request**
```json
{ "refresh_token": "eyJ..." }
```
**Response `200`** — same as login.

---

## Properties  `/api/properties`

### GET `/api/properties`
List properties. Optional query: `status`, `city`, `min_price`, `max_price`, `property_type`, `page`, `limit`.

```bash
curl "http://localhost:8000/api/properties?city=Mumbai&min_price=5000000&status=listed"
```

### POST `/api/properties` *(auth: seller/agent/admin)*
```json
{
  "title": "3BHK Sea View",
  "description": "Luxury apartment with sea view",
  "location": "Marine Drive",
  "city": "Mumbai",
  "state": "MH",
  "country": "India",
  "price": 15000000,
  "property_type": "apartment",
  "bedrooms": 3,
  "bathrooms": 2,
  "area": 1800,
  "amenities": ["pool", "gym", "parking"],
  "images": ["https://cdn.example.com/img1.jpg"]
}
```

### PUT `/api/properties/{property_id}` *(auth: owner/admin)*
Partial update — all fields optional.

### DELETE `/api/properties/{property_id}` *(auth: owner/admin)*

### POST `/api/properties/{property_id}/wishlist` *(auth)*
Adds property to current user's wishlist.

---

## Commission  `/api/commission`

### POST `/api/commission/rules` *(auth)*
Create a commission rule.
```json
{
  "name": "Builder Premium",
  "commission_type": "builder_property",
  "base_rate": 3.0,
  "tier_rates": [
    {"min_amount": 5000000, "rate": 3.5},
    {"min_amount": 10000000, "rate": 4.0}
  ],
  "conditions": {"min_deal_value": 1000000},
  "is_active": true,
  "effective_date": "2024-01-01T00:00:00"
}
```

### POST `/api/commission/calculate` *(auth)*
```json
{
  "recipient_id": "emp-001",
  "recipient_type": "employee",
  "commission_rule_id": "rule-001",
  "deal_id": "deal-001",
  "deal_type": "builder_property",
  "deal_amount": 8000000
}
```
**Response `201`**
```json
{
  "id": "comm-001",
  "calculated_amount": 280000.0,
  "base_rate": 3.5,
  "status": "pending"
}
```

### POST `/api/commission/builder-property` *(auth)*
```json
{
  "property_id": "prop-001",
  "property_value": 10000000,
  "recipient_id": "emp-001",
  "recipient_type": "employee",
  "commission_rule_id": "rule-001"
}
```

### POST `/api/commission/loan` *(auth)*
```json
{
  "loan_id": "loan-001",
  "loan_amount": 5000000,
  "recipient_id": "emp-001",
  "recipient_type": "employee",
  "commission_rule_id": "rule-001"
}
```

### POST `/api/commission/credit-card-cashback` *(auth)*
```json
{
  "cashback_id": "cashback-001",
  "cashback_amount": 500,
  "recipient_id": "user-001",
  "recipient_type": "user",
  "commission_rule_id": "rule-001"
}
```

### PUT `/api/commission/commissions/{commission_id}/approve` *(auth)*

### POST `/api/commission/payouts` *(auth)*
```json
{
  "commission_ids": ["comm-001", "comm-002"],
  "payment_method_id": "bank-acc-001",
  "gateway": "bank_transfer"
}
```

### GET `/api/commission/analytics` *(auth)*
Query: `recipient_id`, `start_date`, `end_date`

**Response**
```json
{
  "total_commissions": 1500000.0,
  "paid_commissions": 1200000.0,
  "pending_commissions": 300000.0,
  "average_commission": 75000.0,
  "commission_by_type": {"builder_property": 900000, "property_sale": 600000},
  "top_performers": [{"recipient_id": "emp-001", "total": 500000}],
  "monthly_returns": [...],
  "quarterly_returns": [...],
  "yearly_returns": [...]
}
```

### GET `/api/commission/returns/monthly`
### GET `/api/commission/returns/quarterly`
### GET `/api/commission/returns/yearly`
### GET `/api/commission/returns/total?recipient_id=emp-001`

---

## Credit Cards  `/api/credit-cards`

### POST `/api/credit-cards` *(auth)*
```json
{
  "user_id": "user-001",
  "card_name": "HDFC Regalia",
  "bank_name": "HDFC Bank",
  "card_type": "credit",
  "card_tier": "premium",
  "card_number_last4": "4242",
  "credit_limit": 500000,
  "reward_rate": 4.0,
  "reward_categories": ["travel", "dining", "online"],
  "annual_fee": 2500
}
```

### POST `/api/credit-cards/{card_id}/rewards` *(auth)*
```json
{
  "credit_card_id": "card-001",
  "transaction_type": "earned",
  "points": 0,
  "amount": 5000,
  "category": "travel",
  "description": "Flight booking"
}
```
Points are auto-calculated from amount × reward_rate × category_multiplier.

### POST `/api/credit-cards/{card_id}/cashback` *(auth)*
```json
{
  "credit_card_id": "card-001",
  "cashback_amount": 500,
  "category": "travel",
  "description": "Monthly cashback"
}
```

### GET `/api/credit-cards/best-cashback` *(auth)*
Query params: `spend_amount=10000`, `category=travel`, `cashback_rate=1.0`, `limit=3`

**Response `200`**
```json
[
  {
    "card_name": "HDFC Infinia",
    "bank_name": "HDFC Bank",
    "card_type": "credit",
    "tier": "super_premium",
    "reward_rate": 5.0,
    "reward_categories": ["travel", "dining"],
    "estimated_points": 100000,
    "estimated_cashback": 1000.0,
    "net_cashback_after_fee": 750.0,
    "match_score": 80.0
  }
]
```

### GET `/api/credit-cards/compare` *(auth)*
Query: `card_ids=id1,id2`, `spend_amount`, `primary_category`

### GET `/api/credit-cards/analytics/{user_id}` *(auth)*
Returns: `total_points_earned`, `total_points_redeemed`, `points_balance`, `total_cashback_earned`, `monthly_returns`, `quarterly_returns`, `yearly_returns`

---

## Salary & Payroll  `/api/salary`

### POST `/api/salary/components` *(auth)*
```json
{
  "employee_id": "emp-001",
  "component_type": "basic",
  "name": "Basic Salary",
  "amount": 50000,
  "is_percentage": false,
  "is_taxable": true,
  "effective_date": "2024-01-01T00:00:00"
}
```
`component_type` values: `basic` · `hra` · `da` · `ta` · `ma` · `bonus` · `overtime` · `commission` · `deduction_tax` · `deduction_pf` · `deduction_esi` · `deduction_loan` · `deduction_other`

### POST `/api/salary/periods` *(auth)*
```json
{
  "name": "May 2024",
  "start_date": "2024-05-01T00:00:00",
  "end_date": "2024-05-31T23:59:59",
  "frequency": "monthly",
  "payment_date": "2024-06-05T00:00:00"
}
```

### POST `/api/salary/periods/{period_id}/process` *(auth)*
Triggers full payroll run:
1. Fetches active employees
2. Calculates gross/net salary (with PF, ESI, TDS)
3. Pulls & adds approved reimbursements to net pay
4. Inserts payroll entries
5. Marks reimbursements as PAID
6. Updates period status to `processed`

**Response**
```json
{
  "success": true,
  "payroll_period_id": "period-001",
  "processed_entries": 45,
  "total_amount": 2250000.0
}
```

### POST `/api/salary/slips` *(auth)*
```json
{ "payroll_entry_id": "entry-001" }
```
Generates a formatted salary slip with slip number `SLIP-202405-0001`.

### GET `/api/salary/employees/{employee_id}/slips` *(auth)*

---

## Reimbursements  `/api/reimbursements`

### POST `/api/reimbursements` *(auth)*
```json
{
  "employee_id": "emp-001",
  "category": "travel",
  "title": "Client visit to Pune",
  "description": "Train + auto + lunch",
  "amount": 3200,
  "expense_date": "2024-05-15T00:00:00",
  "receipt_urls": ["https://cdn.example.com/receipt1.jpg"]
}
```
`category` values: `travel` · `accommodation` · `meals` · `equipment` · `medical` · `training` · `communication` · `other`

**Response `201`** — full `ReimbursementResponse` with `status=submitted`.

### PUT `/api/reimbursements/{id}/approve` *(auth: manager/admin)*
```json
{ "approved_amount": 3000 }
```

### PUT `/api/reimbursements/{id}/reject` *(auth: manager/admin)*
```json
{ "rejection_reason": "Receipt not legible" }
```

### GET `/api/reimbursements/analytics/summary` *(auth)*
Query: `employee_id` (optional)

**Response**
```json
{
  "total_submitted": 45000.0,
  "total_approved": 38000.0,
  "total_paid": 30000.0,
  "total_pending": 7000.0,
  "by_category": {"travel": 20000, "meals": 8000},
  "by_status": {"submitted": 3, "approved": 2, "paid": 5},
  "average_processing_days": 2.5
}
```

---

## Claims  `/api/claims`

### POST `/api/claims` *(auth)*
```json
{
  "employee_id": "emp-001",
  "claim_type": "medical",
  "title": "Hospitalisation — appendectomy",
  "description": "Emergency surgery at Apollo Hospital",
  "claimed_amount": 75000,
  "incident_date": "2024-05-10T00:00:00",
  "priority": "high",
  "supporting_docs": ["https://cdn.example.com/discharge_summary.pdf"]
}
```
`claim_type` values: `medical` · `accident` · `life_insurance` · `property_damage` · `travel_insurance` · `commission_dispute` · `salary_dispute` · `other`  
`priority` values: `low` · `medium` · `high` · `urgent`

### PUT `/api/claims/{id}/assign` *(auth: HR/admin)*
Query param: `assigned_to=hr-user-001`

### PUT `/api/claims/{id}/resolve` *(auth: HR/admin)*
```json
{
  "status": "approved",
  "resolution_notes": "Claim verified against policy. Approved in full.",
  "approved_amount": 75000
}
```
`status` values: `approved` · `partially_approved` · `rejected` · `closed`

### GET `/api/claims/analytics/summary` *(auth)*
**Response**
```json
{
  "total_claims": 28,
  "open_claims": 5,
  "approved_claims": 18,
  "rejected_claims": 5,
  "total_claimed_amount": 1500000,
  "total_approved_amount": 1200000,
  "by_type": {"medical": 15, "accident": 4, "salary_dispute": 3},
  "by_priority": {"high": 10, "medium": 12, "low": 6},
  "average_resolution_days": 4.2
}
```

---

## Tax  `/api/tax`

### POST `/api/tax/compute` *(auth)*
```json
{
  "employee_id": "emp-001",
  "financial_year": "2024-25",
  "regime": "new",
  "gross_annual_income": 1200000,
  "hra_exemption": 0,
  "section_80c": 0,
  "section_80d": 0,
  "section_80ccd": 50000,
  "other_deductions": 0,
  "tds_already_deducted": 30000
}
```
`regime` values: `new` · `old`

**Response `200`**
```json
{
  "employee_id": "emp-001",
  "financial_year": "2024-25",
  "regime": "new",
  "gross_annual_income": 1200000,
  "total_exemptions": 125000,
  "taxable_income": 1075000,
  "basic_tax": 107500,
  "surcharge": 0,
  "cess": 4300,
  "total_tax_liability": 111800,
  "tds_already_deducted": 30000,
  "balance_tax_payable": 81800,
  "monthly_tds": 6816.67,
  "effective_tax_rate": 9.317,
  "computed_at": "2024-05-28T06:00:00"
}
```

### POST `/api/tax/form16/{employee_id}` *(auth)*
Query param: `financial_year=2024-25`

Aggregates all salary slips for the FY, computes tax, generates and persists Form-16.

**Response `200`** — `Form16Summary` with all fields.

### GET `/api/tax/tds/monthly-estimate` *(auth)*
Query: `monthly_gross=100000&regime=new`
```json
{ "monthly_gross": 100000, "regime": "new", "estimated_monthly_tds": 6816.67 }
```

### POST `/api/tax/slabs` *(auth: admin)*
Add custom slab (overrides built-in defaults for a given FY).
```json
{
  "regime": "new",
  "min_income": 0,
  "max_income": 400000,
  "rate": 0,
  "surcharge_rate": 0,
  "cess_rate": 4.0,
  "financial_year": "2025-26"
}
```

### GET `/api/tax/slabs` *(auth)*
Query: `regime=new&financial_year=2025-26`

---

## Onboarding & Offboarding  `/api/onboarding`

### POST `/api/onboarding/onboardings` *(auth)*
```json
{
  "employee_id": "emp-001",
  "employee_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+91-9876543210",
  "designation": "Software Engineer",
  "department": "Engineering",
  "reporting_manager_id": "mgr-001",
  "date_of_joining": "2024-06-01T00:00:00",
  "employment_type": "full_time",
  "work_location": "Mumbai",
  "salary_offered": 1200000,
  "epfo_details": {
    "uan_number": "100123456789",
    "pf_account_number": "MH/PUN/123456/123",
    "establishment_id": "EST123456",
    "epfo_office": "Mumbai",
    "pf_contribution_rate": 12.0,
    "status": "registered"
  },
  "esi_details": {
    "esi_number": "ESI1234567890",
    "establishment_id": "EST123456",
    "esi_office": "Mumbai",
    "esi_contribution_rate": 1.0,
    "status": "registered"
  },
  "bank_account": {
    "account_number": "1234567890",
    "bank_name": "HDFC Bank",
    "branch_name": "Andheri East",
    "ifsc_code": "HDFC0001234",
    "account_type": "savings",
    "is_primary": true
  },
  "documents": [],
  "checklist": [],
  "notes": "New hire for backend team"
}
```
**Response `201`** — `EmployeeOnboardingResponse` with auto-generated 15-item checklist.

### PUT `/api/onboarding/onboardings/{id}` *(auth)*
Update status, documents, checklist items, EPFO/ESI details.

### PUT `/api/onboarding/onboardings/{id}/approve` *(auth)*
### PUT `/api/onboarding/onboardings/{id}/reject` *(auth)*
Query param: `rejection_reason`

### GET `/api/onboarding/onboardings/analytics` *(auth)*
**Response**
```json
{
  "total_onboardings": 45,
  "pending_onboardings": 5,
  "in_progress_onboardings": 10,
  "completed_onboardings": 28,
  "rejected_onboardings": 2,
  "average_onboarding_days": 7.5,
  "by_department": {"Engineering": 20, "Sales": 15, "HR": 10},
  "by_status": {"pending": 5, "in_progress": 10, "completed": 28, "rejected": 2},
  "monthly_trend": [...]
}
```

### POST `/api/onboarding/offboardings` *(auth)*
```json
{
  "employee_id": "emp-001",
  "employee_name": "John Doe",
  "email": "john@example.com",
  "phone_number": "+91-9876543210",
  "designation": "Software Engineer",
  "department": "Engineering",
  "date_of_resignation": "2024-05-15T00:00:00",
  "last_working_day": "2024-06-15T00:00:00",
  "reason_for_leaving": "Better opportunity",
  "exit_type": "resignation",
  "is_eligible_rehire": true,
  "handover_to": "emp-002",
  "settlement_amount": 150000,
  "pending_leaves": 5,
  "encashable_leaves": 5,
  "assets_to_return": ["Laptop", "Access Card", "Monitor"],
  "clearance_checklist": [],
  "notes": "Standard resignation"
}
```
**Response `201`** — `EmployeeOffboardingResponse` with auto-generated 10-item clearance checklist.

### PUT `/api/onboarding/offboardings/{id}/approve` *(auth)*
### PUT `/api/onboarding/offboardings/{id}/complete` *(auth)*

### GET `/api/onboarding/offboardings/analytics` *(auth)*
**Response**
```json
{
  "total_offboardings": 12,
  "pending_offboardings": 2,
  "in_progress_offboardings": 3,
  "completed_offboardings": 7,
  "average_tenure_days": 730,
  "attrition_rate": 8.5,
  "by_department": {"Engineering": 5, "Sales": 4, "HR": 3},
  "by_reason": {"Better opportunity": 6, "Relocation": 3, "Other": 3},
  "by_exit_type": {"resignation": 10, "termination": 2},
  "monthly_trend": [...]
}
```

### POST `/api/onboarding/epfo/register` *(auth)*
```json
{
  "employee_id": "emp-001",
  "uan_number": "100123456789",
  "pf_account_number": "MH/PUN/123456/123",
  "establishment_id": "EST123456",
  "epfo_office": "Mumbai",
  "pf_contribution_rate": 12.0,
  "pension_contribution_rate": 8.33,
  "status": "registered"
}
```

### GET `/api/onboarding/epfo/{employee_id}` *(auth)*
### POST `/api/onboarding/epfo/{employee_id}/withdraw` *(auth)*
### POST `/api/onboarding/epfo/{employee_id}/transfer` *(auth)*
Query param: `new_establishment_id`

### POST `/api/onboarding/esi/register` *(auth)*
### GET `/api/onboarding/esi/{employee_id}` *(auth)*

---

## Loan Calculator  `/api/loan`

### POST `/api/loan/calculate`
```json
{ "principal": 5000000, "annual_rate": 8.5, "years": 20 }
```
**Response**
```json
{
  "principal": 5000000,
  "monthly_payment": 43391.16,
  "total_payment": 10413878.4,
  "total_interest": 5413878.4,
  "amortization_schedule": [...]
}
```

### POST `/api/loan/mortgage`
```json
{
  "principal": 5000000,
  "annual_rate": 8.5,
  "years": 20,
  "down_payment": 1000000,
  "property_tax": 60000,
  "insurance": 12000
}
```

### POST `/api/loan/affordability`
```json
{
  "monthly_income": 150000,
  "debt_to_income_ratio": 0.4,
  "annual_rate": 8.5,
  "years": 20
}
```

---

## Referral  `/api/referral`

### POST `/api/referral/codes` *(auth)*
Creates a unique referral code for the current user.

### POST `/api/referral/apply` *(auth)*
```json
{ "referral_code": "REF-ABC123", "user_id": "new-user-001" }
```

### POST `/api/referral/rewards/{reward_id}/claim` *(auth)*
Claims an earned referral reward. Sets `is_claimed=true`, records commission entry.

### GET `/api/referral/stats` *(auth)*
Returns `referral_code`, `total_referrals`, `successful_referrals`, `pending_rewards`, `claimed_rewards`.

---

## Admin  `/api/admin`

### GET `/api/admin/analytics` *(auth: admin)*
Platform-wide stats: users, properties, inquiries, wishlists, revenue.

### GET `/api/admin/users` *(auth: admin)*
Query: `role`, `page`, `limit`

### POST `/api/admin/users/{user_id}/deactivate` *(auth: admin)*

### DELETE `/api/admin/users/{user_id}` *(auth: admin)*

### GET `/api/admin/properties` *(auth: admin)*
Query: `status=pending`, `page`, `limit`

### POST `/api/admin/properties/{property_id}/approve` *(auth: admin)*
### POST `/api/admin/properties/{property_id}/reject` *(auth: admin)*

---

## Health  `/health`

### GET `/health`
No auth required.
```json
{ "status": "healthy", "environment": "production" }
```

---

## Curl Cheatsheet

```bash
# ── Set token ───────────────────────────────────────────────────────────────
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@housing.com","password":"Admin@123"}' | jq -r .access_token)

AUTH="Authorization: Bearer $TOKEN"

# ── Properties ───────────────────────────────────────────────────────────────
curl -H "$AUTH" "http://localhost:8000/api/properties?city=Mumbai&status=listed"

# ── Commission analytics ─────────────────────────────────────────────────────
curl -H "$AUTH" "http://localhost:8000/api/commission/analytics?start_date=2024-01-01T00:00:00"

# ── Best cashback cards ──────────────────────────────────────────────────────
curl -H "$AUTH" "http://localhost:8000/api/credit-cards/best-cashback?spend_amount=10000&category=travel&limit=3"

# ── Submit reimbursement ─────────────────────────────────────────────────────
curl -X POST -H "$AUTH" -H "Content-Type: application/json" \
  http://localhost:8000/api/reimbursements \
  -d '{"employee_id":"emp-001","category":"travel","title":"Client visit","amount":3200,"expense_date":"2024-05-15T00:00:00"}'

# ── Compute tax ──────────────────────────────────────────────────────────────
curl -X POST -H "$AUTH" -H "Content-Type: application/json" \
  http://localhost:8000/api/tax/compute \
  -d '{"employee_id":"emp-001","financial_year":"2024-25","regime":"new","gross_annual_income":1200000,"tds_already_deducted":30000}'

# ── Run payroll ──────────────────────────────────────────────────────────────
curl -X POST -H "$AUTH" "http://localhost:8000/api/salary/periods/period-001/process"

# ── Open claim ───────────────────────────────────────────────────────────────
curl -X POST -H "$AUTH" -H "Content-Type: application/json" \
  http://localhost:8000/api/claims \
  -d '{"employee_id":"emp-001","claim_type":"medical","title":"Surgery","description":"Emergency","claimed_amount":75000,"incident_date":"2024-05-10T00:00:00","priority":"high"}'

# ── Generate Form-16 ─────────────────────────────────────────────────────────
curl -X POST -H "$AUTH" "http://localhost:8000/api/tax/form16/emp-001?financial_year=2024-25"
```
