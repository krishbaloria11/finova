# Finova — Development & Demonstration Credentials

> [!NOTE]
> **DEVELOPMENT & SIMULATION USE ONLY**  
> These credentials are exclusively for academic evaluation, local testing, and system demonstrations of the Finova Banking and Loan Management System. No real-world banking secrets, production tokens, or personal identifiers are stored here.

---

## 1. Retail Customers (5 Demo Personas)

All customer accounts share the default development password: `Finova@2024`

| Username | Password | Full Name | Customer / CIF ID | Profile & Key Accounts | KYC Status |
|---|---|---|---|---|---|
| `sophia` | `Finova@2024` | Sophia Mehta | `CUST-482109` | Premier Banking · 3 Accounts (Savings #4821, Savings #1092, Current #9934) · Total Balance: ₹1,28,450.80 · Active Home Loan #HL-4091 | `VERIFIED` |
| `rohan` | `Finova@2024` | Rohan Deshmukh | `CUST-918231` | Retail Banking · Savings Account #482199001122 · Balance: ₹35,000.00 | `PENDING` |
| `aarav` | `Finova@2024` | Aarav Sharma | `CUST-331902` | Premier Banking · Savings #501234567890 (₹1,95,400.00) & Current #501234567891 (₹45,000.00) · Active Personal Loan #LN-PL-331902 | `VERIFIED` |
| `priya` | `Finova@2024` | Priya Patel | `CUST-552814` | Healthcare Salaried · Savings #601234567890 (₹64,250.00) · Pending Home Loan Application #LA-2024-5528 | `PENDING` (Assigned to Officer Ananya) |
| `vikram` | `Finova@2024` | Vikram Malhotra | `CUST-774129` | Commercial Retail · Current Facility #701234567890 (₹88,700.00) & Savings #701234567891 (₹15,300.00) | `NEEDS_REVIEW` |

---

## 2. Bank Operations & Underwriting Officers (2 Demo Employees)

Both staff accounts share the development password: `Finova@2024`

| Username | Password | Officer Name | Employee ID | Branch & Operational Focus |
|---|---|---|---|---|
| `employee` | `Finova@2024` | Ramesh Iyer | `EMP-BLR-101` | **Senior Credit Underwriter** · Bengaluru Indiranagar Branch (`BLR01`) · Loan sanctioning, DTI underwriting, credit queue & KYC audit |
| `employee2` | `Finova@2024` | Ananya Rao | `EMP-MUM-102` | **KYC & Operations Officer** · Mumbai Bandra Kurla Complex Flagship (`MUM01`) · Customer onboarding, KYC verification queue & compliance reviews |

---

## 3. System Administrator & DBMS Manager (1 Admin Account)

| Username | Password | Role | Permissions & Operational Scope |
|---|---|---|---|
| `admin` | `FinovaAdmin@2024` | `ADMIN` / Superuser | Full system oversight, live DBMS aggregations, account freeze/unfreeze, compensating transaction reversals, credit facility suspension, branch facilities management, immutable regulatory audit trail |

---

## 4. Verification Check

All 8 accounts are seeded into `finova/backend/db.sqlite3` and tested against the Django Token Authentication endpoint (`POST /api/auth/login/`).
