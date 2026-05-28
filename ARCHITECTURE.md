# Architecture — Housing Platform

> All diagrams use [Mermaid](https://mermaid.js.org/) syntax and render natively on GitHub, GitLab, and Notion.

---

## 1. High-Level System Architecture

```mermaid
graph TB
    subgraph Clients
        WEB[React Web App<br/>:3000]
        MOB[Mobile / PWA]
        EXT[External Integrations<br/>Webhooks / Partners]
    end

    subgraph Edge
        NGINX[Nginx<br/>TLS Termination<br/>Rate Limiting<br/>Load Balancer]
    end

    subgraph API["FastAPI Backend  :8000"]
        direction TB
        AUTH[Auth Layer<br/>JWT + RBAC]
        ROUTERS[30+ API Routers]
        ENGINES[Business Engines<br/>commission · salary · tax<br/>reimbursement · claims<br/>credit_card · notification]
    end

    subgraph Data
        MONGO[(MongoDB 6<br/>Primary + Read Replica)]
        REDIS[(Redis 6<br/>Cache + Sessions)]
    end

    subgraph Infra
        DOCKER[Docker Compose]
        CRON[APScheduler<br/>Cron Jobs]
        LOG[Structured Logging<br/>app.log]
    end

    WEB & MOB & EXT --> NGINX
    NGINX --> AUTH
    AUTH --> ROUTERS
    ROUTERS --> ENGINES
    ENGINES --> MONGO
    ENGINES --> REDIS
    CRON --> ENGINES
    DOCKER -.-> API & MONGO & REDIS
```

---

## 2. Backend Module Dependency Map

```mermaid
graph LR
    MAIN[main.py] --> AUTH_R[routers/auth]
    MAIN --> PROP_R[routers/properties]
    MAIN --> COMM_R[routers/commission]
    MAIN --> CC_R[routers/credit_card]
    MAIN --> SAL_R[routers/salary]
    MAIN --> REIMB_R[routers/reimbursement]
    MAIN --> CLAIM_R[routers/claims]
    MAIN --> TAX_R[routers/tax]
    MAIN --> PAY_R[routers/payments]

    COMM_R --> COMMISSION[commission.py]
    CC_R   --> CREDIT_CARD[credit_card.py]
    SAL_R  --> SALARY[salary.py]
    REIMB_R --> REIMBURSEMENT[reimbursement.py]
    CLAIM_R --> CLAIMS[claims.py]
    TAX_R  --> TAX[tax.py]

    SALARY --> TAX
    SALARY --> REIMBURSEMENT

    COMMISSION --> NOTIFICATION[notification.py]
    SALARY --> NOTIFICATION

    COMMISSION --> SCHEMAS[schemas.py]
    CREDIT_CARD --> SCHEMAS
    SALARY --> SCHEMAS
    REIMBURSEMENT --> SCHEMAS
    CLAIMS --> SCHEMAS
    TAX --> SCHEMAS

    SCHEMAS --> PYDANTIC[Pydantic V2]
    COMMISSION --> DB[(MongoDB)]
    CREDIT_CARD --> DB
    SALARY --> DB
    REIMBURSEMENT --> DB
    CLAIMS --> DB
    TAX --> DB
```

---

## 3. Data Model — MongoDB Collections

```mermaid
erDiagram
    users {
        string _id PK
        string email
        string role
        string first_name
        string last_name
        string pan_number
        bool   is_active
    }

    properties {
        string _id PK
        string user_id FK
        string title
        float  price
        string property_type
        string status
    }

    commissions {
        string _id PK
        string recipient_id FK
        string commission_rule_id FK
        string deal_id
        float  calculated_amount
        string status
    }

    commission_rules {
        string _id PK
        string commission_type
        float  base_rate
        object tier_rates
        bool   is_active
    }

    credit_cards {
        string _id PK
        string user_id FK
        int    points_balance
        float  credit_limit
        string card_type
    }

    reward_transactions {
        string _id PK
        string credit_card_id FK
        int    points
        string transaction_type
        string category
    }

    salary_components {
        string _id PK
        string employee_id FK
        string component_type
        float  amount
        bool   is_taxable
    }

    payroll_periods {
        string _id PK
        string name
        date   start_date
        date   end_date
        string status
        float  total_amount
    }

    payroll_entries {
        string _id PK
        string payroll_period_id FK
        string employee_id FK
        float  gross_salary
        float  net_salary
        float  tax_deduction
        float  reimbursement_total
    }

    reimbursements {
        string _id PK
        string employee_id FK
        string category
        float  amount
        float  approved_amount
        string status
        string payroll_period_id FK
    }

    claims {
        string _id PK
        string employee_id FK
        string claim_type
        float  claimed_amount
        float  approved_amount
        string status
        string priority
    }

    salary_slips {
        string _id PK
        string payroll_entry_id FK
        string employee_id FK
        float  gross_salary
        float  net_salary
        float  tax_deduction
        string slip_number
    }

    form16 {
        string _id PK
        string employee_id FK
        string financial_year
        float  total_tax
        float  tds_deducted
    }

    users ||--o{ properties : "owns"
    users ||--o{ commissions : "receives"
    users ||--o{ credit_cards : "holds"
    users ||--o{ salary_components : "has"
    users ||--o{ reimbursements : "submits"
    users ||--o{ claims : "files"
    users ||--o{ payroll_entries : "processed in"
    commission_rules ||--o{ commissions : "governs"
    credit_cards ||--o{ reward_transactions : "records"
    payroll_periods ||--o{ payroll_entries : "contains"
    payroll_entries ||--o{ salary_slips : "generates"
    users ||--o{ form16 : "receives"
    reimbursements }o--|| payroll_periods : "paid through"
```

---

## 4. Finance Module Integration

```mermaid
graph TD
    subgraph PayrollRun["Payroll Period Processing"]
        PR[Process Period<br/>PayrollProcessor]
        COMP[Fetch Salary Components]
        CALC[SalaryCalculator<br/>gross · PF · ESI · tax]
        REIMB_PULL[Pull Approved<br/>Reimbursements]
        REIMB_ADD[Add Reimbursement<br/>to Net Pay]
        ENTRY[Insert Payroll Entry]
        REIMB_MARK[Mark Reimbursements<br/>PAID]
        SLIP[Generate Salary Slip]
    end

    subgraph TaxEngine["Tax Engine (tax.py)"]
        SLAB[Apply Slab Tax]
        SURCHARGE[Add Surcharge]
        CESS[Add 4% Cess]
        REBATE[87A Rebate]
        TDS[Monthly TDS]
        F16[Form-16 Generation]
    end

    subgraph CommissionFlow["Commission Flow"]
        RULE[Commission Rule]
        TIER[Tiered Rate Check]
        PAYOUT[Payout Processing]
        NOTIF[Investment Notification]
    end

    PR --> COMP --> CALC
    CALC -->|"calculate_tax()"| SLAB --> SURCHARGE --> CESS --> REBATE --> TDS
    PR --> REIMB_PULL --> REIMB_ADD --> ENTRY
    ENTRY --> REIMB_MARK
    ENTRY --> SLIP
    ENTRY -->|"Annual"| F16

    RULE --> TIER --> PAYOUT --> NOTIF
    PAYOUT -->|"commission_type=CREDIT_CARD_CASHBACK"| CC[Credit Card Module]
```

---

## 5. Credit Card Rewards Architecture

```mermaid
graph LR
    TXN[Transaction] --> CALC[RewardCalculator]
    CALC -->|"base_rate × multiplier"| PTS[Points Earned]
    PTS --> CARD_BAL[Card points_balance ↑]

    REDEEM[Redeem Request] --> CB_CALC[Cashback = points × point_value × rate]
    CB_CALC --> RECORD[record_reward_transaction<br/>REDEEMED]
    RECORD --> CARD_BAL2[Card points_balance ↓]
    RECORD --> CASHBACK_DOC[Cashbacks Collection]

    COMPARE[CreditCardComparator] --> SCORE[Score each card<br/>net_cashback - annual_fee]
    SCORE --> RANK[Sorted by net_cashback_after_fee]
    RANK --> BEST[Best Cards Response]
```

---

## 6. Request Lifecycle (Sequence)

```mermaid
sequenceDiagram
    participant C as Client
    participant N as Nginx
    participant F as FastAPI
    participant A as Auth Middleware
    participant R as Router
    participant E as Engine
    participant DB as MongoDB
    participant RD as Redis

    C->>N: HTTPS Request
    N->>F: Forward (rate-limited)
    F->>A: Validate JWT
    A-->>F: User context
    F->>R: Route handler
    R->>RD: Cache lookup
    alt Cache hit
        RD-->>R: Cached response
    else Cache miss
        R->>E: Business logic
        E->>DB: Async query (Motor)
        DB-->>E: Result
        E-->>R: Processed data
        R->>RD: Store in cache (TTL)
    end
    R-->>F: Response
    F-->>N: JSON response
    N-->>C: HTTPS response
```

---

## 7. Deployment Architecture

```mermaid
graph TB
    subgraph Internet
        DNS[DNS / CDN]
    end

    subgraph Server["Production Server / K8s Cluster"]
        NGINX[Nginx :443<br/>TLS + LB]

        subgraph API_Pods["API Pods (×N)"]
            POD1[FastAPI Instance 1]
            POD2[FastAPI Instance 2]
            POD3[FastAPI Instance N]
        end

        subgraph DB_Cluster["Data Tier"]
            MONGO_P[(MongoDB Primary)]
            MONGO_S[(MongoDB Secondary<br/>Read Replica)]
            REDIS_C[(Redis Cluster)]
        end
    end

    DNS --> NGINX
    NGINX --> POD1 & POD2 & POD3
    POD1 & POD2 & POD3 --> MONGO_P
    POD1 & POD2 & POD3 -->|"reads"| MONGO_S
    POD1 & POD2 & POD3 --> REDIS_C
    MONGO_P -->|"replication"| MONGO_S
```
