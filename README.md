# Finova — Silk & Glass Banking and Loan Management System

> **Academic College DBMS Capstone Project & Local Simulated Banking System**  
> *A high-fidelity full-stack financial platform demonstrating relational database engineering, ACID transaction compliance, role-based access control, and Glassmorphic UI aesthetics.*

---

## 1. Project Title
**Finova — Silk & Glass Banking and Loan Management System**

---

## 2. Project Description
**Finova** is an educational, full-stack banking and credit management simulator created as a College Database Management Systems (DBMS) capstone project. It bridges rigorous backend relational database design (Django ORM + SQLite/PostgreSQL) with a modern, high-aesthetic "Silk & Glass" interface inspired by contemporary fintech design systems.

### ⚠️ IMPORTANT NOTICE — SIMULATION PURPOSE ONLY
- **NO Real Money**: This system is purely educational and simulated.
- **NO Real Banking Infrastructure**: There is no link to the RBI, SWIFT, NEFT, RTGS, IMPS, or any sovereign financial network.
- **NO UPI or Payment Gateway**: Does not connect to Razorpay, Stripe, Paytm, UPI, or credit card processors.
- **NO External APIs**: All financial calculations, transfers, interest schedules, and credit approvals execute locally within an isolated SQLite database.
- **Fictional Data**: All account numbers, balances, Aadhaar/PAN references, customer names, and transactions are generated dummy records.

---

## 3. Features

### 👤 Customer Experience
- **Authentication & Persona Switching**: Secure token-based authentication (`/api/auth/login/`, `/api/auth/logout/`), session persistence, and instant demo persona switching.
- **Real-Time Glassmorphic Dashboard**: Total liquid net worth, consolidated primary/secondary account metrics, active loan summary, and CIBIL credit score badge.
- **Dynamic Cashflow Analytics**: Real-time visualization of monthly credits, debits, and net savings across 30-day, 90-day, and Year-to-Date (YTD) horizons.
- **Multi-Account Overview**: Dedicated views for Primary Savings, Secondary Savings, and Current Accounts displaying real-time available and ledger balances, IFSC, and branch details.
- **Atomic Fund Transfers**: Peer-to-peer simulated transfers with recipient validation, account number format checks, positive amount enforcement, review dialog, and atomic debit/credit updates.
- **Live Transaction Ledger & CSV Export**: Chronological transaction history with search, category filtering (Debit, Credit, Transfer, Loan, Salary), and instant one-click CSV export.
- **Loan Products & Dynamic EMI Calculator**: Interactive loan catalog (Home, Personal, Auto, Education) with real-time interest rate compounding and EMI estimations.
- **4-Step Loan Application Wizard**: Guided application workflow capturing desired amount, tenure, income documents, purpose, and instant validation.
- **Direct EMI Repayment Facility**: One-click simulated repayment debiting customer accounts, decrementing loan outstanding balances, and logging atomic transaction audit trails.
- **Notifications Hub**: In-app activity feed for incoming credits, debits, loan disbursements, and approvals with individual and bulk "mark-as-read" support.
- **Customer Profile & KYC**: View registered customer details, masked Aadhaar (`XXXX-XXXX-1234`), PAN (`ABCDE1234F`), phone, address, and quick Sign Out.

### 👔 Bank Employee (Credit Underwriter)
- **Credit Underwriting Queue**: Dedicated portal to inspect all submitted loan applications in real-time.
- **Application Evaluation**: Comprehensive review of applicant CIBIL scores, requested amount, interest rate, tenure, and purpose.
- **One-Click Approval & Disbursement**: Atomic approval that creates the active loan facility, disburses initial principal directly into the applicant's primary savings account, logs an audit record, and alerts the customer.
- **Application Rejection**: Ability to decline unqualified applications with logged underwriter notes.

### 🛡️ Bank Administrator
- **Executive Operations Dashboard**: High-level institutional metrics including total customers, active accounts, aggregate deposit vault, and total credit disbursed.
- **Comprehensive Audit Trail**: Immutable system-wide audit logging recording User ID, action types (`TRANSFER_SUCCESS`, `LOAN_APPROVED`, `USER_LOGIN`), client IP addresses, and timestamps.
- **Data Governance**: Strict server-side verification that prevents unauthorized data tampering.

---

## 4. Technology Stack

### Backend
- **Python 3.11+**: Core programming language.
- **Django 5.0+**: Enterprise Python web framework providing ORM, migrations, and core architecture.
- **Django REST Framework (DRF) 3.14+**: RESTful API serialization, viewsets, and token-based authentication.
- **django-cors-headers 4.0+**: Cross-Origin Resource Sharing handling for local frontend/backend communication.
- **python-dotenv 1.0+**: 12-factor application configuration and environment isolation.
- **python-dateutil 2.8+**: Precision calendar arithmetic for loan maturity and EMI payment calculations.

### Database
- **SQLite 3**: Default local database engine for development and academic evaluation.
- **PostgreSQL Ready**: Architectural compatibility with production relational database servers.

### Frontend
- **HTML5 & Vanilla JavaScript (ES6+)**: Component-driven SPA architecture without heavy node-based dependencies.
- **Tailwind CSS**: Utility-first styling configured with Finova Silk & Glass tokens.
- **Google Fonts**: Modern typography utilizing *Plus Jakarta Sans* and *Space Grotesk*.

### Security & Architecture
- **DRF Token Authentication**: Token lifecycle management with server-side validation and logout invalidation.
- **ACID Transactions**: Atomic database operations managed via `django.db.transaction.atomic()`.

---

## 5. Project Architecture

The directory tree reflects a clean separation of concerns between backend services, the frontend client, and project configuration:

```text
finova/
├── .env.example                     # Environment template for local configuration
├── .gitignore                       # Git exclusion rules (ignores .env, db.sqlite3, cache)
├── requirements.txt                 # Single project-wide runtime Python dependencies
├── README.md                        # Complete project manual & viva guide
│
├── backend/                         # Django Backend Core
│   ├── manage.py                    # Django management script (primary CLI entrypoint)
│   ├── db.sqlite3                   # Local SQLite database (ignored by git)
│   │
│   ├── finova_core/                 # Main project configuration
│   │   ├── __init__.py
│   │   ├── settings.py              # App settings, DB engine, CORS, installed apps
│   │   ├── urls.py                  # Master routing table mapping APIs and frontend
│   │   ├── wsgi.py                  # WSGI entry point
│   │   └── asgi.py                  # ASGI entry point
│   │
│   └── apps/                        # Modular Django Applications (3NF Domain Models)
│       ├── users/                   # Custom User, Customer, Employee & Auth views
│       │   ├── models.py            # User, Customer, Employee models
│       │   ├── serializers.py       # User, Customer serializers
│       │   ├── views.py             # Login, Logout, Register, Profile views
│       │   ├── dashboard_views.py   # Consolidated Customer & Admin stats APIs
│       │   ├── test_integration.py  # 25 comprehensive automated integration tests
│       │   └── management/commands/
│       │       ├── seed_demo_data.py   # Populates presentation demo records
│       │       └── reset_demo_data.py  # Safe development-only database reset command
│       ├── branches/                # Bank branches & IFSC routing
│       │   └── models.py            # Branch model (IFSC, MICR, address)
│       ├── accounts/                # Deposit accounts & balances
│       │   ├── models.py            # AccountType, Account models (balance check constraints)
│       │   └── views.py             # Account list, detail, and balance views
│       ├── transactions/            # Ledger records & atomic transfer service
│       │   ├── models.py            # Transaction, Beneficiary models
│       │   ├── services.py          # TransferService (ACID atomic debit/credit)
│       │   └── views.py             # Transfer execute, history, search, and CSV export
│       ├── loans/                   # Credit facilities, loan applications & EMI engine
│       │   ├── models.py            # LoanType, LoanApplication, Loan, LoanPayment models
│       │   ├── services.py          # LoanService (Disbursement & EMI amortization)
│       │   └── views.py             # Application wizard, underwriter review, EMI payment
│       ├── notifications/           # User alerts and system updates
│       │   ├── models.py            # Notification model
│       │   └── views.py             # Notification list and read status toggles
│       └── audit/                   # Security audit logs
│           ├── models.py            # AuditLog model (immutable event capture)
│           └── views.py             # Admin-only audit trail views
│
├── frontend/                        # Silk & Glass Client Interface
│   ├── index.html                   # Single Page Application HTML shell
│   ├── assets/                      # Static branding assets
│   │   └── logo.svg                 # Finova vector emblem
│   └── js/
│       ├── api.js                   # Centralized REST API client (Fetch + Token header)
│       └── app.js                   # UI state manager, event listeners, view switcher
│
└── stitch_export/                   # Original Stitch design exports and design tokens
```

---

## 6. Database Architecture

The schema adheres strictly to Relational Database Management System (RDBMS) design principles, using 14 normalized models:

| Model Name | Primary Key | Foreign Keys / Relationships | Core Attributes & Constraints |
| :--- | :--- | :--- | :--- |
| **Branch** | `id` | None | `name`, `code` (Unique), `ifsc` (11 chars, Unique), `address`, `city` |
| **User** | `id` | AbstractUser | `username` (Unique), `email`, `role` (`CUSTOMER`, `EMPLOYEE`, `ADMIN`) |
| **Customer** | `id` | `user_id` (1-to-1) | `customer_id` (Unique), `pan`, `aadhaar_hash`, `cibil_score` (300-900) |
| **Employee** | `id` | `user_id` (1-to-1), `branch_id` | `employee_id` (Unique), `department`, `designation` |
| **AccountType** | `id` | None | `code` (Unique), `name`, `interest_rate`, `min_balance` |
| **Account** | `id` | `customer_id`, `account_type_id`, `branch_id` | `account_number` (12 chars, Unique), `available_balance >= 0`, `ledger_balance >= 0` |
| **Transaction** | `id` | `account_id`, `destination_account_id` | `reference_id` (UUID, Unique), `txn_type`, `amount > 0`, `balance_after`, `timestamp` |
| **Beneficiary** | `id` | `customer_id` | `name`, `account_number`, `ifsc`, `Unique(customer_id, account_number)` |
| **LoanType** | `id` | None | `code` (Unique), `name`, `min_amount`, `max_amount`, `interest_rate` |
| **LoanApplication**| `id` | `customer_id`, `loan_type_id`, `reviewed_by` | `application_number` (Unique), `applied_amount`, `tenure_months`, `status` |
| **Loan** | `id` | `customer_id`, `application_id`, `loan_type_id` | `loan_account_number` (Unique), `principal`, `outstanding_balance >= 0`, `emi_amount` |
| **LoanPayment** | `id` | `loan_id`, `account_id` | `receipt_number` (Unique), `amount > 0`, `principal_component`, `interest_component` |
| **Notification** | `id` | `user_id` | `title`, `message`, `notification_type`, `is_read`, `created_at` |
| **AuditLog** | `id` | `user_id` (Nullable) | `action`, `ip_address`, `details` (JSON), `timestamp` |

---

## 7. DBMS Concepts Demonstrated

1. **Primary & Candidate Keys**: Every entity possesses an auto-incrementing integer surrogate primary key (`id`) alongside distinct natural candidate keys (e.g., `account_number`, `ifsc`, `application_number`, `reference_id`).
2. **Referential Integrity**: All relationships enforce database-level foreign key cascades (`on_delete=models.CASCADE` or `models.PROTECT`) to guarantee zero orphan records.
3. **Check Constraints**:
   - `available_balance >= 0` and `ledger_balance >= 0` on `Account` prevent negative balances.
   - `amount > 0` on `Transaction` and `LoanPayment` prevents zero or negative financial postings.
   - `outstanding_balance >= 0` on `Loan` ensures loans cannot be overpaid into an arbitrary credit balance.
4. **Unique Multi-Field Constraints**: `UniqueConstraint(fields=['customer', 'account_number'])` on `Beneficiary` eliminates duplicate payee records.
5. **Relational Normalization (3NF)**:
   - **1NF**: Every field holds atomic values.
   - **2NF**: No partial dependency on candidate keys; attributes depend wholly on model identifiers.
   - **3NF**: Non-key attributes are transitively independent (e.g., Branch address and IFSC are decoupled into `Branch` rather than duplicated in `Account`).
6. **ACID Transaction Compliance**:
   - **Atomicity**: Fund transfers execute within `transaction.atomic()`. Either both source debit and recipient credit succeed, or both roll back completely.
   - **Consistency**: Balance check constraints and balance invariants guarantee financial integrity before and after operations.
   - **Isolation**: Row-level locking via `.select_for_update()` protects account records against race conditions and concurrent access.
   - **Durability**: Once committed, state changes are written to disk journal storage.
7. **Role-Based Access Control (RBAC)**: Backend verification enforces strict boundary separation across Customer, Employee, and Administrator personas.
8. **Immutable Audit Trails**: High-importance events write tamper-evident logs capturing client IP, user identity, action, and serialized payload metadata.

---

## 8. Installation Requirements

Verify prerequisites on your local system (Windows 10/11 recommended):

- **Python**: Version 3.11 or higher
- **Git**: Installed and available in PATH
- **Web Browser**: Chrome, Edge, Firefox, or Brave
- **Code Editor**: VS Code (optional, but recommended)

Check your environment from PowerShell or CMD:
```powershell
python --version
pip --version
git --version
```

---

## 9. Clone or Download Instructions

### Option A: Using Git Clone
```powershell
git clone <repository-url>
cd AntiGravity/finova
```

### Option B: Local Project Folder
Navigate directly to the `finova` directory from your workspace root:
```powershell
cd finova
```

> **Directory Navigation Rule**:
> - Finova Root (`finova/`): Contains `requirements.txt`, `.env.example`, `.gitignore`, `README.md`, `frontend/`, `stitch_export/`.
> - Django Backend (`finova/backend/`): Contains `manage.py`, `finova_core/`, `apps/`, and `db.sqlite3`.

---

## 10. Virtual Environment Setup

Isolate your Python dependencies using a local virtual environment:

### Create Virtual Environment
```powershell
python -m venv .venv
```

### Activate Virtual Environment
- **Windows PowerShell**:
  ```powershell
  .\.venv\Scripts\Activate.ps1
  ```
  *(If execution policies block scripts, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first)*

- **Windows Command Prompt (CMD)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```

*When active, your terminal prompt will display `(.venv)`.*

---

## 11. Install Dependencies

Upgrade package management tools and install the verified runtime dependencies:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

---

## 12. Environment Configuration

1. In the `finova` directory, copy the template `.env.example` file to create your local `.env`:
   ```powershell
   Copy-Item .env.example .env
   ```
   *(Or in CMD: `copy .env.example .env`)*

2. Open `.env` and verify the development settings:
   ```env
   DJANGO_SECRET_KEY=finova-development-secret-key-do-not-use-in-production
   DJANGO_DEBUG=True
   DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0
   DB_ENGINE=sqlite
   CORS_ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000
   ```
   *(Note: Never commit your active `.env` file to version control. It is already excluded in `.gitignore`.)*

---

## 13. Database Setup & Migrations

Enter the `backend` directory where `manage.py` is located and initialize the SQLite database schema:

```powershell
# Navigate into backend directory:
cd backend

# Apply existing migrations to initialize tables and constraints:
python manage.py migrate
```

**What migrations do**:
Migrations translate Django's Python model definitions into executable SQL DDL statements (e.g., `CREATE TABLE`, `ADD CONSTRAINT`) and apply them to create `db.sqlite3`.

---

## 14. Seed Demo Data

Populate the database with realistic, fictional banking entities (branches, account types, customer accounts, loan facilities, and past transactions):

```powershell
python manage.py seed_demo_data
```

This creates the demonstration state without touching external services.

---

## 15. Safe Demo Reset Command

If you execute transfers, approve loans, or pay EMIs during a presentation, you can reset the database back to its clean starting state with a single command:

```powershell
python manage.py reset_demo_data
```

To skip the interactive confirmation prompt:
```powershell
python manage.py reset_demo_data --no-input
```

### Safety Features
- **Development Only**: Refuses to run if `DEBUG=False`.
- **Database Engine Guard**: Refuses to run against non-SQLite databases without an explicit `--force` flag.
- **Idempotent**: Running the command multiple times yields the exact same clean demo state without duplicate rows.
- **Zero Schema Disruption**: Does not delete migrations or drop database tables; clears and re-seeds data records atomically.

---

## 16. Run the Server (Manual Control)

Start the local Django development server:

```powershell
python manage.py runserver
```

Once running, access the application in your browser:
👉 **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

*`127.0.0.1` represents your local machine (`localhost`), running on port `8000`.*

---

## 17. Stop the Server (Manual Control)

To stop the server at any time:

Press:
```text
Ctrl + C
```

> **IMPORTANT**: The server is under your complete manual control. It never runs automatically in the background or upon system startup.

---

## 18. Django System Checks

Validate configuration integrity and model definitions:

```powershell
python manage.py check
```

Expected output:
```text
System check identified no issues (0 silenced).
```

---

## 19. Automated Integration Tests

Run the full automated test suite covering authentication, RBAC, atomic transfers, loan workflows, and demo reset idempotency:

```powershell
python manage.py test
```

Expected output:
```text
Ran 42 tests in ~35s
OK
```

---

## 20. API Endpoint Overview

All endpoints communicate using JSON and require token authentication (`Authorization: Token <key>`) except public auth routes:

### Authentication
- `POST /api/auth/login/`: Authenticate user and issue DRF auth token.
- `POST /api/auth/logout/`: Invalidate auth token and log logout event.
- `GET  /api/auth/me/`: Retrieve current user profile and role details.

### Banking & Accounts
- `GET  /api/dashboard/`: Consolidated balances, cashflow metrics, upcoming EMI, and CIBIL score.
- `GET  /api/accounts/`: List authenticated customer's deposit accounts.
- `GET  /api/accounts/<id>/`: Detail view of specific deposit account.
- `GET  /api/account-types/`: List available deposit account products.

### Transactions & Transfers
- `GET  /api/transactions/`: Filterable, searchable transaction history with debit/credit indicators.
- `POST /api/transfers/`: Execute ACID atomic peer-to-peer fund transfer.
- `GET  /api/beneficiaries/`: List verified payee accounts.

### Loans & EMI Management
- `GET  /api/loans/`: List customer's active and past loan facilities.
- `GET  /api/loan-types/`: List loan products (interest rates, limits).
- `POST /api/loan-applications/`: Submit a new loan application.
- `POST /api/loans/calculate-emi/`: Real-time loan interest and installment calculator.
- `POST /api/loans/pay-emi/`: Process an EMI payment against an active loan.

### Employee Underwriting & Administration
- `GET  /api/loan-applications/`: Queue of all pending loan applications.
- `POST /api/loan-applications/<id>/review/`: Approve & disburse or reject application.
- `GET  /api/admin/stats/`: High-level institutional deposit, customer, and loan metrics.
- `GET  /api/audit-logs/`: Security audit log records.

### Notifications
- `GET  /api/notifications/`: User alert inbox.
- `PATCH /api/notifications/<id>/`: Toggle notification read status.

---

## 21. Demo User Credentials (DEMO ONLY)

The demo database contains realistic, pre-seeded accounts across 5 Customers, 2 Bank Employees, and 1 Administrator:

### 👤 Demo Customers (5 Accounts)

| Customer Name | Username | Password | Customer ID | Primary Account | KYC Status | Facilities / Details |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Sophia Sterling** | `sophia` | `Finova@2024` | `CUST-1001` | `482190824821` | Approved | Active Home Loan (`#HL-4091`), Secondary Account (`482190824822`), Balance: ₹1,28,450.80 |
| **Rohan Sharma** | `rohan` | `Finova@2024` | `CUST-1002` | `482199001122` | Under Review | Pending Loan Application (`LA-2024-9182`), Balance: ₹45,200.00 |
| **Aarav Patel** | `aarav` | `Finova@2024` | `CUST-1003` | `482199001133` | Approved | Regular Salary & Utility Cashflow, Eligible for credit, Balance: ₹82,150.00 |
| **Priya Nair** | `priya` | `Finova@2024` | `CUST-1004` | `482199001144` | Under Review | Current Account, Commercial/Business transfers, Balance: ₹1,95,000.00 |
| **Vikram Malhotra** | `vikram` | `Finova@2024` | `CUST-1005` | `482199001155` | Pending | New Onboarding Savings Account, Balance: ₹24,800.00 |

### 👔 Demo Employees (2 Staff Members)

| Employee Name | Username | Password | Employee ID | Role / Designation | Branch | Permissions & Workload |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Elena Vance** | `employee` | `Finova@2024` | `EMP-2001` | Senior Credit Underwriter & KYC Officer | Downtown Head Office | Loan Application Queue, KYC Verification, Approve/Reject & Disburse |
| **Marcus Vance** | `employee2` | `Finova@2024` | `EMP-2002` | Compliance Officer & Risk Auditor | Downtown Head Office | Underwriting Audit, KYC Verification Review, Risk Assessment |

### 🛡️ System Administrator

| Account | Username | Password | Access Level & Scope |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin` | `FinovaAdmin@2024` | Executive DBMS Management, All Accounts, Transactions, Loans, KYC, Branches & System Audit Trail |

> **Note**: For instant login testing, use the **Persona Switcher** in the top navigation bar or the quick persona cards inside the **Sign In** modal on the frontend. Credentials will automatically populate.

---

## 22. Recommended Demo Walkthrough

### Step 1: Customer Banking Flow
1. Open `http://127.0.0.1:8000/`.
2. Click **Sign In** (or the quick persona button **Customer**) and login as `sophia`.
3. View **Dashboard**: Note total balance of `₹1,28,450.80`, active Home Loan `#HL-4091`, and CIBIL score `785`.
4. Navigate to **Transfer**: Select Primary Savings (`482190824821`), enter recipient `482199001122`, amount `₹5,000`, confirm transfer, and verify instant balance debit and toast notification.
5. Navigate to **Transactions**: View the newly created transfer record, search by keyword, and click **Export CSV** to download a local transaction statement.
6. Navigate to **Loans**: Check repayment schedule for `#HL-4091`, click **Pay EMI**, and confirm payment.
7. Click **Apply for Loan**: Complete the 4-step wizard for a `₹2,00,000` Personal Loan and submit.
8. Click **Sign Out** from the sidebar or profile menu.

### Step 2: Employee Underwriting Flow
1. Login as `employee` / `Finova@2024`.
2. Inspect the **Loan Application Queue**: Locate the newly submitted application or Rohan's pending application (`LA-2024-9182`).
3. Click **Review & Underwrite**: Inspect applicant CIBIL score and financials.
4. Click **Approve & Disburse**: Observe that funds are atomically credited to the applicant's account and an audit log is written.
5. Sign out.

### Step 3: Administrator Audit Flow
1. Login as `admin` / `FinovaAdmin@2024`.
2. Review **Administrative Statistics**: Total deposits, loans disbursed, and active customers.
3. Review **Audit Trail**: Confirm real-time entries for the transfer, loan approval, and logins with IP addresses and timestamps.
4. Sign out.

---

## 23. Git Workflow for Beginners

Basic commands for repository version management:

```powershell
# 1. Check which files were modified or added
git status

# 2. Stage changes for commit
git add .

# 3. Commit staged changes with a descriptive message
git commit -m "feat: complete step 4 final audit and stabilization"

# 4. Fetch and integrate remote updates
git pull origin main

# 5. Push local commits to remote repository
git push origin main
```

---

## 24. Troubleshooting Guide

| Issue | Root Cause | Solution |
| :--- | :--- | :--- |
| `'Invalid token.'` on Login Screen | DRF TokenAuthentication evaluated stale client `Authorization` headers before reaching login logic | Resolved in backend (`authentication_classes = []` on auth endpoints) and frontend (`api.js` excludes `Authorization` on login/register and auto-clears stale tokens). |
| `'python' is not recognized` | Python is not added to system PATH | Reinstall Python and check the box **"Add python.exe to PATH"**. |
| `'pip' is not recognized` | Script directory missing from PATH | Run using `python -m pip install ...` instead of `pip`. |
| Script execution disabled in PowerShell | PowerShell execution policy restriction | Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your terminal. |
| `Port 8000 already in use` | A previous Django server process is still bound | Stop the conflicting process via Task Manager or run on another port: `python manage.py runserver 8080`. |
| `No such table: accounts_account` | Migrations have not been applied | Run `python manage.py migrate` in the `backend/` directory. |
| API returns `401 Unauthorized` | Missing or expired auth token | Sign out, clear browser `localStorage`, and log in again. |
| API returns `403 Forbidden` | Current role lacks endpoint permissions | Verify you are logged into the correct persona (e.g. Employee for underwriting). |
| Empty balances or missing loans | Seed data not loaded | Run `python manage.py reset_demo_data --no-input`. |
| `manage.py not found` | Terminal is in wrong directory | Ensure your terminal is in the `finova/backend` folder: `cd finova/backend`. |

---

## 25. Explicit Server Control

Always remember:

- **START Command**:
  ```powershell
  python manage.py runserver
  ```
- **STOP Command**:
  ```text
  Ctrl + C
  ```

*The server will NEVER automatically launch or stay active without your direct manual command.*

---

## 26. Security Notes
- **Local Development Secrets**: The `.env` file uses development keys. In any production scenario, set `DEBUG=False` and supply an unguessable `DJANGO_SECRET_KEY`.
- **Git Hygiene**: `.env` and `db.sqlite3` are strictly ignored by `.gitignore`. Never use `git add -f` to force-track them.
- **Pure Simulation**: Never input real debit card numbers, net banking passwords, or personal banking credentials.

---

## 27. Project Status

The Finova project has successfully achieved:
- ✅ **Step 1**: Django backend architecture, 14 normalized models, check constraints, and service layer.
- ✅ **Step 2**: Stitch-generated Silk & Glass frontend integration preserving layout, typography, and styling tokens.
- ✅ **Step 3**: Django REST Framework API integration connecting frontend views to live database queries.
- ✅ **Step 4**: Full project audit, dead button fixes, sign-out controls, safe demo reset command (`reset_demo_data`), expansion demo seeding (`seed_expansion_demo_data`), 42 automated tests (including stale token isolation, KYC workflows, multi-persona RBAC, cashflow chart analytics, branch analytics), minimal `requirements.txt`, git hygiene, and this complete documentation.


---

## 28. College Viva & Technical DBMS Defense Guide

When presenting this project during a college viva or evaluation, use these key points:

1. **Why Django ORM & SQLite?**
   *Django's ORM eliminates raw SQL injection vulnerabilities while providing high-level abstraction for relational queries, constraint enforcement, and cross-database portability from SQLite to PostgreSQL.*
2. **Why 3NF Normalization?**
   *Dividing entities into branches, account types, accounts, and transactions eliminates data redundancy, guarantees insertion/update/deletion anomaly prevention, and preserves functional dependency.*
3. **How does Finova guarantee ACID properties?**
   *Fund transfers use Python's `with transaction.atomic():` and `.select_for_update()`. If an exception occurs (e.g., negative balance check violation), all pending operations roll back cleanly.*
4. **How does the frontend communicate with the backend?**
   *The frontend single-page application uses `fetch()` in `api.js` to dispatch JSON requests with an `Authorization: Token <token>` header. DRF decodes the token, authenticates the user, checks permissions, and responds with JSON.*
5. **How is Customer Data Isolation enforced?**
   *Data isolation is enforced strictly on the server in Django QuerySets (e.g., `Account.objects.filter(customer=request.user.customer)`). Even if a customer inspects DOM elements or alters frontend JS, the backend rejects unauthorized access with HTTP 403/404.*

   ---

## 🚀 Quick Run

### ☁️ Run Instantly in GitHub Codespaces (No Setup Required)

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/krishbaloria11/finovadbms?quickstart=1)

> Click the button above to launch a fully configured cloud development environment — no local installation needed!

### 💻 Run Locally (Clone & Go)

```bash
# 1. Clone the repository
git clone https://github.com/krishbaloria11/finova.git
cd finova

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up the database & seed demo data
cd backend
python manage.py migrate
python manage.py seed_demo_data

# 5. Start the server
python manage.py runserver
```

Then open **http://127.0.0.1:8000** in your browser and use the demo credentials from [`DEMO_CREDENTIALS.md`](DEMO_CREDENTIALS.md) to log in.

---

<p align="center">
  Made with ❤️ by <a href="https://github.com/krishbaloria11">krishbaloria11</a>
</p>

