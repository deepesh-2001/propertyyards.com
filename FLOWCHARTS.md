# Business Flow Charts — Housing Platform

> All diagrams use [Mermaid](https://mermaid.js.org/) syntax — renders on GitHub, GitLab, Notion, and VS Code with the Mermaid plugin.

---

## 1. User Authentication Flow

```mermaid
flowchart TD
    START([User visits platform]) --> REG{Has account?}

    REG -->|No| REGISTER[POST /api/auth/register]
    REGISTER --> VALIDATE{Pydantic validation}
    VALIDATE -->|Fail| ERR400[400 Bad Request]
    VALIDATE -->|Pass| HASH[Hash password bcrypt]
    HASH --> SAVE_USER[(Save to users collection)]
    SAVE_USER --> ISSUE_TOKEN

    REG -->|Yes| LOGIN[POST /api/auth/login]
    LOGIN --> FIND_USER[(Lookup user by email)]
    FIND_USER -->|Not found| ERR401A[401 Unauthorized]
    FIND_USER -->|Found| CHECK_PW{Password match?}
    CHECK_PW -->|No| ERR401B[401 Unauthorized]
    CHECK_PW -->|Yes| ISSUE_TOKEN[Issue JWT access + refresh tokens]

    ISSUE_TOKEN --> STORE_REDIS[(Cache session in Redis)]
    STORE_REDIS --> RETURN_TOKEN[Return tokens to client]

    RETURN_TOKEN --> API_CALL[Authenticated API calls<br/>Authorization: Bearer token]
    API_CALL --> VERIFY_JWT{JWT valid & not expired?}
    VERIFY_JWT -->|No| ERR401C[401 Unauthorized]
    VERIFY_JWT -->|Yes| RBAC{Role allowed for endpoint?}
    RBAC -->|No| ERR403[403 Forbidden]
    RBAC -->|Yes| HANDLER[Route handler executes]
```

---

## 2. Property Listing Flow

```mermaid
flowchart TD
    SELLER([Seller / Agent]) --> CREATE[POST /api/properties]
    CREATE --> AUTH{Authenticated?}
    AUTH -->|No| E401[401 Unauthorized]
    AUTH -->|Yes| ROLE{Role = seller / agent / admin?}
    ROLE -->|No| E403[403 Forbidden]
    ROLE -->|Yes| VALIDATE{Pydantic schema valid?}
    VALIDATE -->|No| E400[400 Bad Request]
    VALIDATE -->|Yes| SAVE[(Insert into properties)]
    SAVE --> STATUS[status = pending]
    STATUS --> NOTIFY_ADMIN[Notify admin for moderation]

    NOTIFY_ADMIN --> ADMIN_REVIEW{Admin review}
    ADMIN_REVIEW -->|Approve| APPROVE[POST /api/admin/properties/id/approve]
    ADMIN_REVIEW -->|Reject| REJECT[POST /api/admin/properties/id/reject]
    APPROVE --> LISTED[status = listed · Visible on platform]
    REJECT --> REJECTED[status = rejected · Seller notified]

    LISTED --> BUYER([Buyer searches])
    BUYER --> SEARCH[GET /api/properties/search]
    SEARCH --> CACHE{Redis cache hit?}
    CACHE -->|Yes| RETURN_CACHED[Return cached results]
    CACHE -->|No| MONGO_QUERY[(MongoDB indexed query)]
    MONGO_QUERY --> CACHE_STORE[(Store in Redis 5 min)]
    CACHE_STORE --> RETURN_RESULTS[Return results]
    RETURN_RESULTS --> WISHLIST{Add to wishlist?}
    WISHLIST -->|Yes| POST_WISH[POST /api/properties/id/wishlist]
    WISHLIST -->|No| INQUIRY{Send inquiry?}
    INQUIRY -->|Yes| POST_INQ[POST /api/inquiries]
```

---

## 3. Commission Calculation & Payout Flow

```mermaid
flowchart TD
    DEAL([Deal Closed]) --> TYPE{Commission type?}

    TYPE -->|Property Sale| PROP_RULE[Lookup PROPERTY_SALE rule]
    TYPE -->|Builder Property| BUILD_RULE[Lookup BUILDER_PROPERTY rule<br/>base rate 3%]
    TYPE -->|Loan Commission| LOAN_RULE[Lookup LOAN_COMMISSION rule<br/>base rate 0.5%]
    TYPE -->|Referral| REF_RULE[Lookup REFERRAL rule]
    TYPE -->|Credit Card Cashback| CC_RULE[Lookup CREDIT_CARD_CASHBACK rule<br/>base rate 1%]

    PROP_RULE & BUILD_RULE & LOAN_RULE & REF_RULE & CC_RULE --> CALC[CommissionCalculator.calculate_commission]
    CALC --> TIERS{Tier rates defined?}
    TIERS -->|Yes| APPLY_TIERS[Apply highest matching tier]
    TIERS -->|No| APPLY_BASE[Apply base_rate × deal_amount]
    APPLY_TIERS & APPLY_BASE --> CONDITIONS{Conditions met?<br/>min_deal_value etc.}
    CONDITIONS -->|No| ZERO[calculated_amount = 0]
    CONDITIONS -->|Yes| AMOUNT[calculated_amount = rate × amount / 100]

    AMOUNT --> SAVE_COMM[(Insert commissions · status=pending)]
    SAVE_COMM --> APPROVE_COMM[PUT /commissions/id/approve]
    APPROVE_COMM --> PAYOUT[POST /payouts]

    PAYOUT --> INSERT_PAYOUT[(Insert payout · status=processing)]
    INSERT_PAYOUT --> UPDATE_COMMS[(Update commissions → status=paid)]
    UPDATE_COMMS --> NOTIFICATIONS[Send investment notifications]
    NOTIFICATIONS --> MARK_DONE[(Update payout → status=completed)]
    MARK_DONE --> SUCCESS([Payout complete])

    UPDATE_COMMS -->|Exception| ROLLBACK[(Update payout → status=failed)]
    ROLLBACK --> RETRY([Retry later])
```

---

## 4. Reimbursement Lifecycle Flow

```mermaid
flowchart TD
    EMP([Employee]) --> SUBMIT[POST /api/reimbursements<br/>category · amount · receipt_urls]
    SUBMIT --> VALIDATE{Valid expense?}
    VALIDATE -->|No| E400[400 Bad Request]
    VALIDATE -->|Yes| SAVE[(Insert · status=submitted)]
    SAVE --> MANAGER([Manager / HR])

    MANAGER --> REVIEW[GET /api/reimbursements/employees/id/reimbursements]
    REVIEW --> DECISION{Decision}

    DECISION -->|Approve| APPROVE[PUT /api/reimbursements/id/approve<br/>approved_amount]
    DECISION -->|Reject| REJECT[PUT /api/reimbursements/id/reject<br/>rejection_reason]

    APPROVE --> APPROVED[(status=approved)]
    REJECT --> REJECTED[(status=rejected · Notify employee)]

    APPROVED --> PAYROLL_RUN[POST /api/salary/periods/id/process]
    PAYROLL_RUN --> PULL[get_approved_for_employee]
    PULL --> ADD_TO_NET[net_salary += approved_amount]
    ADD_TO_NET --> INSERT_ENTRY[(Insert payroll_entry<br/>reimbursement_total recorded)]
    INSERT_ENTRY --> MARK_PAID[(status=paid · paid_at · payroll_period_id)]
    MARK_PAID --> SLIP[Generate salary slip<br/>reimbursement visible]
    SLIP --> EMP2([Employee receives payslip])
```

---

## 5. Claims Lifecycle Flow

```mermaid
flowchart TD
    FILER([Employee / HR]) --> OPEN[POST /api/claims<br/>claim_type · claimed_amount · priority]
    OPEN --> SAVE[(Insert · status=open · claim_number generated)]
    SAVE --> ASSIGN[PUT /api/claims/id/assign<br/>assigned_to investigator]
    ASSIGN --> INVESTIGATING[(status=under_investigation)]

    INVESTIGATING --> INVESTIGATE([Investigator reviews evidence])
    INVESTIGATE --> DECISION{Resolution decision}

    DECISION -->|Full approval| FULL[PUT /api/claims/id/resolve<br/>status=approved<br/>approved_amount = claimed_amount]
    DECISION -->|Partial approval| PARTIAL[PUT /api/claims/id/resolve<br/>status=partially_approved<br/>approved_amount < claimed_amount]
    DECISION -->|Reject| DENY[PUT /api/claims/id/resolve<br/>status=rejected]
    DECISION -->|Close without action| CLOSE[status=closed]

    FULL & PARTIAL --> PAYMENT[Approved amount disbursed<br/>via payroll or direct payment]
    DENY --> NOTIFY_DENY[Notify employee · reason provided]
    CLOSE --> ARCHIVE[(Archived)]

    PAYMENT --> RESOLVED([Claim resolved])
    NOTIFY_DENY --> APPEAL{Employee appeals?}
    APPEAL -->|Yes| OPEN
    APPEAL -->|No| ARCHIVE
```

---

## 6. Payroll Processing Flow (Full Integration)

```mermaid
flowchart TD
    HR([HR / Finance]) --> CREATE_PERIOD[POST /api/salary/periods<br/>name · start_date · end_date · frequency]
    CREATE_PERIOD --> PERIOD_DRAFT[(payroll_period · status=draft)]

    PERIOD_DRAFT --> ADD_COMPS[POST /api/salary/components<br/>per employee: basic · HRA · DA · bonus]
    ADD_COMPS --> RUN[POST /api/salary/periods/id/process]

    RUN --> FETCH_EMP[(Fetch active employees)]
    FETCH_EMP --> LOOP{For each employee}

    LOOP --> COMPS[(Fetch salary components)]
    COMPS --> CALC[SalaryCalculator.calculate_net_salary]
    CALC --> PF[PF = 12% of basic]
    CALC --> ESI[ESI = 1% if gross ≤ 21000]
    CALC --> TAX[Tax via TaxEngine<br/>new regime default]
    PF & ESI & TAX --> GROSS[gross_salary = basic + allowances + bonuses + overtime]
    GROSS --> NET[net_salary = gross − PF − ESI − tax − deductions]

    NET --> REIMB_FETCH[(Fetch approved reimbursements)]
    REIMB_FETCH --> REIMB_ADD[net_salary += reimbursement_total]
    REIMB_ADD --> INSERT_ENTRY[(Insert payroll_entry)]
    INSERT_ENTRY --> MARK_REIMB[(Mark reimbursements PAID)]
    MARK_REIMB --> LOOP

    LOOP -->|All done| UPDATE_PERIOD[(Update period<br/>status=processed · total_amount)]
    UPDATE_PERIOD --> SLIPS[POST /api/salary/slips<br/>Generate salary slips]
    SLIPS --> NOTIFY_EMP[Notify employees<br/>via notification service]
    NOTIFY_EMP --> DONE([Payroll complete])
```

---

## 7. Tax Computation Flow (Indian IT)

```mermaid
flowchart TD
    REQ([API Request<br/>POST /api/tax/compute]) --> INPUT[gross_annual_income · regime · deductions]

    INPUT --> REGIME{Tax Regime?}

    REGIME -->|New Regime| NEW_STD[Standard deduction ₹75,000<br/>Only 80CCD 1B up to ₹50,000]
    REGIME -->|Old Regime| OLD_STD[Standard deduction ₹50,000<br/>HRA + 80C max ₹1.5L<br/>80D max ₹75k · 80CCD ₹50k<br/>other deductions]

    NEW_STD & OLD_STD --> TAXABLE[taxable_income = gross − total_exemptions]
    TAXABLE --> SLABS[Apply slab tax rates]

    SLABS --> REBATE{Rebate 87A?}
    REBATE -->|New + taxable ≤ 7L| REBATE_25K[Subtract ₹25,000 rebate]
    REBATE -->|Old + taxable ≤ 5L| REBATE_12K[Subtract ₹12,500 rebate]
    REBATE -->|Not eligible| NO_REBATE[No rebate]

    REBATE_25K & REBATE_12K & NO_REBATE --> BASIC_TAX[basic_tax]
    BASIC_TAX --> SURCHARGE{Taxable income > ₹50L?}
    SURCHARGE -->|≤ 50L| S0[surcharge = 0]
    SURCHARGE -->|50L–1Cr| S10[surcharge = 10%]
    SURCHARGE -->|1Cr–2Cr| S15[surcharge = 15%]
    SURCHARGE -->|2Cr–5Cr| S25[surcharge = 25%]
    SURCHARGE -->|> 5Cr| S37[surcharge = 37%]

    S0 & S10 & S15 & S25 & S37 --> CESS[cess = 4% of basic_tax + surcharge]
    CESS --> TOTAL[total_tax = basic_tax + surcharge + cess]
    TOTAL --> TDS_DEDUCTED[Subtract TDS already deducted]
    TDS_DEDUCTED --> BALANCE[balance_tax_payable]
    BALANCE --> MONTHLY[monthly_tds = balance / 12]
    MONTHLY --> RESPONSE([TaxComputationResponse])

    RESPONSE -->|Annually| FORM16[POST /api/tax/form16/employee_id<br/>Generate Form-16]
```

---

## 8. Credit Card Rewards & Cashback Flow

```mermaid
flowchart TD
    USER([User]) --> SPEND[Spend on credit card]
    SPEND --> RECORD[POST /api/credit-cards/id/rewards<br/>transaction_type=EARNED<br/>amount · category]

    RECORD --> POINTS[RewardCalculator.calculate_points<br/>= amount × base_rate × category_multiplier]
    POINTS --> UPDATE_BAL[(Update card<br/>points_balance ↑<br/>total_points_earned ↑)]
    UPDATE_BAL --> TXN[(Insert reward_transaction · EARNED)]

    USER --> REDEEM_REQ[POST /api/credit-cards/id/cashback<br/>requested_cashback_amount]
    REDEEM_REQ --> CALC_PTS[points_needed = requested / point_value / cashback_rate]
    CALC_PTS --> CHECK{Sufficient balance?}
    CHECK -->|No| E400[400 Insufficient points]
    CHECK -->|Yes| CASHBACK_DOC[(Insert cashback record)]
    CASHBACK_DOC --> REDEEM_TXN[record_reward_transaction · REDEEMED]
    REDEEM_TXN --> UPDATE_BAL2[(points_balance ↓<br/>total_points_redeemed ↑)]

    USER --> COMPARE[GET /api/credit-cards/best-cashback<br/>spend_amount · category · cashback_rate]
    COMPARE --> SCORE_ALL[Score all sample cards<br/>effective_rate = reward_rate × category_multiplier]
    SCORE_ALL --> NET[net_cashback_after_fee = estimated_cashback − annual_fee]
    NET --> SORT[Sort by net_cashback_after_fee DESC]
    SORT --> TOP_N[Return top N cards]
```

---

## 9. Loan Calculation Flow

```mermaid
flowchart TD
    USER([User]) --> TYPE{Calculation type?}

    TYPE -->|Simple EMI| EMI[POST /api/loan/calculate<br/>principal · annual_rate · years]
    EMI --> PMT["monthly_payment = P×r×(1+r)^n / ((1+r)^n - 1)"]
    PMT --> TOTAL_COST[total_payment · total_interest · amortization_schedule]
    TOTAL_COST --> EMI_RESP([EMI Response])

    TYPE -->|Mortgage| MORT[POST /api/loan/mortgage<br/>+ down_payment · property_tax · insurance]
    MORT --> LOAN_AMT[loan_amount = principal − down_payment]
    LOAN_AMT --> BASE_PMT[Calculate base monthly payment]
    BASE_PMT --> ADD_COSTS[Add monthly property_tax / 12<br/>Add insurance / 12]
    ADD_COSTS --> TOTAL_MONTHLY[total_monthly_payment]
    TOTAL_MONTHLY --> MORT_RESP([Mortgage Response])

    TYPE -->|Affordability| AFF[POST /api/loan/affordability<br/>monthly_income · debt_to_income_ratio · annual_rate · years]
    AFF --> MAX_PMT[max_monthly = income × dti_ratio]
    MAX_PMT --> REVERSE["reverse-calculate principal from max_monthly"]
    REVERSE --> AFFORD_RESP([Max affordable price])
```

---

## 10. Referral & Reward Claim Flow

```mermaid
flowchart TD
    USER_A([Existing User A]) --> CREATE_CODE[POST /api/referral/codes]
    CREATE_CODE --> CODE[(Store referral code in DB)]
    CODE --> SHARE[User A shares code]

    USER_B([New User B]) --> APPLY[POST /api/referral/apply<br/>referral_code]
    APPLY --> FIND_CODE{Code exists & active?}
    FIND_CODE -->|No| E400[400 Invalid code]
    FIND_CODE -->|Yes| CHECK_USED{Already used by B?}
    CHECK_USED -->|Yes| E409[409 Already applied]
    CHECK_USED -->|No| RECORD_REF[(Insert referral record<br/>status=pending)]

    RECORD_REF --> B_ACTION{B completes qualifying action?<br/>purchase / registration}
    B_ACTION -->|No| PENDING[Reward stays pending]
    B_ACTION -->|Yes| CREATE_REWARD[(Insert reward record<br/>is_claimed=false)]
    CREATE_REWARD --> NOTIFY_A[Notify User A — reward earned]

    NOTIFY_A --> USER_A2([User A]) --> CLAIM[POST /api/referral/rewards/id/claim]
    CLAIM --> CHECK_CLAIMED{Already claimed?}
    CHECK_CLAIMED -->|Yes| E400B[400 Cannot claim]
    CHECK_CLAIMED -->|No| MARK_CLAIMED[(is_claimed=true · claimed_at=now)]
    MARK_CLAIMED --> DISBURSE[Reward disbursed]
    DISBURSE --> COMMISSION_ENTRY[(CommissionType=REFERRAL<br/>recorded in commissions)]
```
