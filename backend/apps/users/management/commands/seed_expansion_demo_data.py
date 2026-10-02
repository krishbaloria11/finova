"""
Idempotent Seeding Engine for Finova Banking Operations Expansion.
Safely provisions additional demo customers, employee2, and deterministic KYC requests
WITHOUT altering or deleting existing database records or Sophia's balance.
"""
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.users.models import User, Customer, Employee, KYCRequest
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.loans.models import Loan, LoanType, LoanApplication
from apps.transactions.models import Transaction, Beneficiary
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


class Command(BaseCommand):
    help = "Safely provisions 5 customers, 2 employees, and realistic KYC workflows idempotently."

    def handle(self, *args, **options):
        self.stdout.write("Initializing Finova Expansion Seeding Engine...")
        now = timezone.now()

        # 1. Ensure Branches
        blr_branch = Branch.objects.filter(branch_code="BLR01").first() or Branch.objects.first()
        mum_branch = Branch.objects.filter(branch_code="MUM01").first() or Branch.objects.first()
        del_branch = Branch.objects.filter(branch_code="DEL01").first() or Branch.objects.first()

        # 2. Account Types
        savings_type = AccountType.objects.filter(code="SAVINGS").first()
        current_type = AccountType.objects.filter(code="CURRENT").first()

        # 3. Loan Types
        home_loan_type = LoanType.objects.filter(code="HOME").first()
        personal_loan_type = LoanType.objects.filter(code="PERSONAL").first()

        # =========================================================================
        # 4. EMPLOYEES: Ensure exactly 2 demo employees exist
        # =========================================================================
        # Employee 1: Ramesh Iyer (Senior Credit Underwriter)
        emp1_user, _ = User.objects.get_or_create(
            username="employee",
            defaults={
                "email": "ramesh.iyer@finova.in",
                "first_name": "Ramesh",
                "last_name": "Iyer",
                "role": User.Role.EMPLOYEE,
                "phone": "+91 98450 11001",
                "is_staff": True
            }
        )
        emp1_user.set_password("Finova@2024")
        emp1_user.save()

        emp1_profile, _ = Employee.objects.get_or_create(
            user=emp1_user,
            defaults={
                "employee_id": "EMP-BLR-101",
                "full_name": "Ramesh Iyer",
                "branch": blr_branch,
                "designation": "Senior Credit Underwriter",
                "department": "Retail Credit & Risk Assessment",
                "is_active": True
            }
        )

        # Employee 2: Ananya Rao (KYC & Operations Officer)
        emp2_user, _ = User.objects.get_or_create(
            username="employee2",
            defaults={
                "email": "ananya.rao@finova.in",
                "first_name": "Ananya",
                "last_name": "Rao",
                "role": User.Role.EMPLOYEE,
                "phone": "+91 98200 22002",
                "is_staff": True
            }
        )
        emp2_user.set_password("Finova@2024")
        emp2_user.save()

        emp2_profile, _ = Employee.objects.get_or_create(
            user=emp2_user,
            defaults={
                "employee_id": "EMP-MUM-102",
                "full_name": "Ananya Rao",
                "branch": mum_branch,
                "designation": "KYC & Operations Officer",
                "department": "KYC & Customer Onboarding",
                "is_active": True
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Verified 2 Demo Employees (employee, employee2)"))

        # =========================================================================
        # 5. CUSTOMER 2: Rohan Deshmukh (existing - enrich with data if missing)
        # =========================================================================
        rohan_user, _ = User.objects.get_or_create(
            username="rohan",
            defaults={
                "email": "rohan.d@example.com",
                "first_name": "Rohan",
                "last_name": "Deshmukh",
                "role": User.Role.CUSTOMER
            }
        )
        rohan_user.set_password("Finova@2024")
        rohan_user.save()

        rohan_cust, _ = Customer.objects.get_or_create(
            user=rohan_user,
            defaults={
                "customer_id": "CUST-918231",
                "full_name": "Rohan Deshmukh",
                "pan_number": "DESHM1234K",
                "aadhaar_last_four": "9182",
                "phone": "+91 99200 44556",
                "address": "402, Sea Crest Towers, Worli",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400018",
                "monthly_income": Decimal("95000.00"),
                "credit_score": 740,
                "credit_category": "Good",
                "kyc_status": Customer.KYCStatus.PENDING,
            }
        )

        rohan_acc, _ = Account.objects.get_or_create(
            customer=rohan_cust,
            account_number="482199001122",
            defaults={
                "account_type": savings_type,
                "branch": mum_branch,
                "available_balance": Decimal("35000.00"),
                "ledger_balance": Decimal("35000.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        # Seed Rohan transactions if fewer than 3
        if Transaction.objects.filter(from_account=rohan_acc).count() + Transaction.objects.filter(to_account=rohan_acc).count() < 3:
            Transaction.objects.get_or_create(
                transaction_id="TXN-ROHAN-001",
                defaults={
                    "to_account": rohan_acc,
                    "amount": Decimal("95000.00"),
                    "category": Transaction.Category.SALARY,
                    "transaction_type": Transaction.TransactionType.CREDIT,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": now - timedelta(days=25),
                    "balance_after": Decimal("130000.00"),
                    "remarks": "Monthly salary credit - Mumbai tech firm"
                }
            )
            Transaction.objects.get_or_create(
                transaction_id="TXN-ROHAN-002",
                defaults={
                    "from_account": rohan_acc,
                    "amount": Decimal("45000.00"),
                    "category": Transaction.Category.TRANSFER,
                    "transaction_type": Transaction.TransactionType.DEBIT,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": now - timedelta(days=12),
                    "balance_after": Decimal("85000.00"),
                    "remarks": "Apartment rental transfer Worli"
                }
            )
            Transaction.objects.get_or_create(
                transaction_id="TXN-ROHAN-003",
                defaults={
                    "from_account": rohan_acc,
                    "amount": Decimal("8500.00"),
                    "category": Transaction.Category.SHOPPING,
                    "transaction_type": Transaction.TransactionType.DEBIT,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": now - timedelta(days=3),
                    "balance_after": Decimal("76500.00"),
                    "remarks": "Grocery & home essentials shopping"
                }
            )

        # =========================================================================
        # 6. CUSTOMER 3: Aarav Sharma (Software Architect, Bengaluru)
        # =========================================================================
        aarav_user, _ = User.objects.get_or_create(
            username="aarav",
            defaults={
                "email": "aarav.sharma@example.com",
                "first_name": "Aarav",
                "last_name": "Sharma",
                "role": User.Role.CUSTOMER,
                "phone": "+91 98450 11223"
            }
        )
        aarav_user.set_password("Finova@2024")
        aarav_user.save()

        aarav_cust, _ = Customer.objects.get_or_create(
            user=aarav_user,
            defaults={
                "customer_id": "CUST-331902",
                "full_name": "Aarav Sharma",
                "pan_number": "AARAV1234S",
                "aadhaar_last_four": "3319",
                "phone": "+91 98450 11223",
                "address": "12, Lavelle Road, Shanthala Nagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560001",
                "monthly_income": Decimal("185000.00"),
                "credit_score": 810,
                "credit_category": "Excellent",
                "kyc_status": Customer.KYCStatus.VERIFIED,
                "kyc_verified_at": now - timedelta(days=60),
                "kyc_remarks": "Fully verified via biometric e-KYC"
            }
        )

        aarav_acc1, _ = Account.objects.get_or_create(
            customer=aarav_cust,
            account_number="501234567890",
            defaults={
                "account_type": savings_type,
                "branch": blr_branch,
                "available_balance": Decimal("195400.00"),
                "ledger_balance": Decimal("195400.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        aarav_acc2, _ = Account.objects.get_or_create(
            customer=aarav_cust,
            account_number="501234567891",
            defaults={
                "account_type": current_type,
                "branch": blr_branch,
                "available_balance": Decimal("45000.00"),
                "ledger_balance": Decimal("45000.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": False
            }
        )

        # Aarav transactions spread across 7D, 30D, 90D
        aarav_txns = [
            ("TXN-AARAV-001", None, aarav_acc1, Decimal("185000.00"), Transaction.Category.SALARY, Transaction.TransactionType.CREDIT, now - timedelta(days=5), Decimal("195400.00"), "Monthly Salary Credit - Tech Corp"),
            ("TXN-AARAV-002", aarav_acc1, None, Decimal("3200.00"), Transaction.Category.FOOD_DINING, Transaction.TransactionType.DEBIT, now - timedelta(days=2), Decimal("192200.00"), "Weekend Dining - Lavelle Road Bistro"),
            ("TXN-AARAV-003", aarav_acc1, None, Decimal("45000.00"), Transaction.Category.TRANSFER, Transaction.TransactionType.DEBIT, now - timedelta(days=15), Decimal("147200.00"), "Apartment Lease Payment"),
            ("TXN-AARAV-004", aarav_acc1, None, Decimal("4800.00"), Transaction.Category.UTILITIES, Transaction.TransactionType.DEBIT, now - timedelta(days=22), Decimal("142400.00"), "BESCOM Electricity & Fiber Bill"),
            ("TXN-AARAV-005", aarav_acc1, None, Decimal("32000.00"), Transaction.Category.SHOPPING, Transaction.TransactionType.DEBIT, now - timedelta(days=45), Decimal("110400.00"), "Electronics & Laptop Peripherals"),
            ("TXN-AARAV-006", None, aarav_acc1, Decimal("15000.00"), Transaction.Category.INVESTMENT, Transaction.TransactionType.CREDIT, now - timedelta(days=70), Decimal("125400.00"), "Quarterly Mutual Fund Dividend Payout"),
        ]
        for tid, f_acc, t_acc, amt, cat, t_type, t_time, bal_after, rmks in aarav_txns:
            Transaction.objects.get_or_create(
                transaction_id=tid,
                defaults={
                    "from_account": f_acc,
                    "to_account": t_acc,
                    "amount": amt,
                    "category": cat,
                    "transaction_type": t_type,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": t_time,
                    "balance_after": bal_after,
                    "remarks": rmks
                }
            )

        # Aarav Active Personal Loan
        if personal_loan_type:
            Loan.objects.get_or_create(
                loan_id="LN-PL-331902",
                defaults={
                    "customer": aarav_cust,
                    "loan_type": personal_loan_type,
                    "servicing_account": aarav_acc1,
                    "principal_amount": Decimal("500000.00"),
                    "interest_rate": Decimal("11.50"),
                    "tenure_months": 48,
                    "monthly_emi": Decimal("10985.00"),
                    "total_payable": Decimal("527280.00"),
                    "total_interest": Decimal("27280.00"),
                    "outstanding_amount": Decimal("412000.00"),
                    "repaid_amount": Decimal("88000.00"),
                    "start_date": (now - timedelta(days=120)).date(),
                    "end_date": (now + timedelta(days=1320)).date(),
                    "next_due_date": (now + timedelta(days=14)).date(),
                    "status": Loan.Status.ACTIVE
                }
            )

        # =========================================================================
        # 7. CUSTOMER 4: Priya Patel (Clinical Research Associate, Mumbai)
        # =========================================================================
        priya_user, _ = User.objects.get_or_create(
            username="priya",
            defaults={
                "email": "priya.patel@example.com",
                "first_name": "Priya",
                "last_name": "Patel",
                "role": User.Role.CUSTOMER,
                "phone": "+91 98200 55667"
            }
        )
        priya_user.set_password("Finova@2024")
        priya_user.save()

        priya_cust, _ = Customer.objects.get_or_create(
            user=priya_user,
            defaults={
                "customer_id": "CUST-552814",
                "full_name": "Priya Patel",
                "pan_number": "PATEL5678P",
                "aadhaar_last_four": "5528",
                "phone": "+91 98200 55667",
                "address": "B-104, Palm Beach Road, Vashi",
                "city": "Navi Mumbai",
                "state": "Maharashtra",
                "pincode": "400703",
                "monthly_income": Decimal("92000.00"),
                "credit_score": 745,
                "credit_category": "Good",
                "kyc_status": Customer.KYCStatus.PENDING,
            }
        )

        priya_acc, _ = Account.objects.get_or_create(
            customer=priya_cust,
            account_number="601234567890",
            defaults={
                "account_type": savings_type,
                "branch": mum_branch,
                "available_balance": Decimal("64250.00"),
                "ledger_balance": Decimal("64250.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        priya_txns = [
            ("TXN-PRIYA-001", None, priya_acc, Decimal("92000.00"), Transaction.Category.SALARY, Transaction.TransactionType.CREDIT, now - timedelta(days=3), Decimal("64250.00"), "Monthly Salary Credit - Clinical Lab"),
            ("TXN-PRIYA-002", priya_acc, None, Decimal("4150.00"), Transaction.Category.SHOPPING, Transaction.TransactionType.DEBIT, now - timedelta(days=1), Decimal("60100.00"), "Supermarket & Grocery Delivery"),
            ("TXN-PRIYA-003", priya_acc, None, Decimal("12500.00"), Transaction.Category.UTILITIES, Transaction.TransactionType.DEBIT, now - timedelta(days=18), Decimal("47600.00"), "Health Insurance Premium Payment"),
            ("TXN-PRIYA-004", priya_acc, None, Decimal("8900.00"), Transaction.Category.FOOD_DINING, Transaction.TransactionType.DEBIT, now - timedelta(days=40), Decimal("38700.00"), "Family Gathering Dining - Bandra"),
            ("TXN-PRIYA-005", priya_acc, None, Decimal("1800.00"), Transaction.Category.OTHER, Transaction.TransactionType.DEBIT, now - timedelta(days=65), Decimal("36900.00"), "Medical Journal Subscription"),
        ]
        for tid, f_acc, t_acc, amt, cat, t_type, t_time, bal_after, rmks in priya_txns:
            Transaction.objects.get_or_create(
                transaction_id=tid,
                defaults={
                    "from_account": f_acc,
                    "to_account": t_acc,
                    "amount": amt,
                    "category": cat,
                    "transaction_type": t_type,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": t_time,
                    "balance_after": bal_after,
                    "remarks": rmks
                }
            )

        # Priya Loan Application (Home Loan)
        priya_app, _ = LoanApplication.objects.get_or_create(
            application_id="LA-2024-5528",
            defaults={
                "customer": priya_cust,
                "loan_type": home_loan_type,
                "requested_amount": Decimal("3500000.00"),
                "tenure_months": 240,
                "proposed_interest_rate": Decimal("8.45"),
                "calculated_emi": Decimal("30268.00"),
                "purpose": "Purchase of 2BHK flat in Navi Mumbai",
                "employment_type": "Salaried - Healthcare",
                "employer_name": "Metro Clinical Diagnostics",
                "monthly_income": Decimal("92000.00"),
                "existing_obligations": Decimal("0.00"),
                "pan_number": "PATEL5678P",
                "aadhaar_number": "998877665528",
                "residential_address": "B-104, Palm Beach Road, Vashi, Navi Mumbai",
                "status": LoanApplication.Status.UNDER_REVIEW,
                "reviewed_by": emp2_profile,
                "review_notes": "Application preliminary check complete. Pending assigned KYC document verification."
            }
        )

        # =========================================================================
        # 8. CUSTOMER 5: Vikram Malhotra (Retail Business Owner, New Delhi)
        # =========================================================================
        vikram_user, _ = User.objects.get_or_create(
            username="vikram",
            defaults={
                "email": "vikram.m@example.com",
                "first_name": "Vikram",
                "last_name": "Malhotra",
                "role": User.Role.CUSTOMER,
                "phone": "+91 98110 77889"
            }
        )
        vikram_user.set_password("Finova@2024")
        vikram_user.save()

        vikram_cust, _ = Customer.objects.get_or_create(
            user=vikram_user,
            defaults={
                "customer_id": "CUST-774129",
                "full_name": "Vikram Malhotra",
                "pan_number": "MALHO9012M",
                "aadhaar_last_four": "7741",
                "phone": "+91 98110 77889",
                "address": "78, Connaught Circus",
                "city": "New Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "monthly_income": Decimal("120000.00"),
                "credit_score": 695,
                "credit_category": "Fair",
                "kyc_status": Customer.KYCStatus.NEEDS_REVIEW,
            }
        )

        vikram_acc1, _ = Account.objects.get_or_create(
            customer=vikram_cust,
            account_number="701234567890",
            defaults={
                "account_type": current_type,
                "branch": del_branch,
                "available_balance": Decimal("88700.00"),
                "ledger_balance": Decimal("88700.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        vikram_acc2, _ = Account.objects.get_or_create(
            customer=vikram_cust,
            account_number="701234567891",
            defaults={
                "account_type": savings_type,
                "branch": del_branch,
                "available_balance": Decimal("15300.00"),
                "ledger_balance": Decimal("15300.00"),
                "status": Account.Status.ACTIVE,
                "is_primary": False
            }
        )

        vikram_txns = [
            ("TXN-VIKRAM-001", None, vikram_acc1, Decimal("55000.00"), Transaction.Category.TRANSFER, Transaction.TransactionType.CREDIT, now - timedelta(days=4), Decimal("88700.00"), "Commercial Trade Invoice Settlement"),
            ("TXN-VIKRAM-002", vikram_acc1, None, Decimal("28000.00"), Transaction.Category.OTHER, Transaction.TransactionType.DEBIT, now - timedelta(days=2), Decimal("60700.00"), "Wholesale Inventory Restock"),
            ("TXN-VIKRAM-003", vikram_acc1, None, Decimal("18400.00"), Transaction.Category.UTILITIES, Transaction.TransactionType.DEBIT, now - timedelta(days=12), Decimal("42300.00"), "Quarterly GST Filing Payment"),
            ("TXN-VIKRAM-004", vikram_acc1, None, Decimal("35000.00"), Transaction.Category.TRANSFER, Transaction.TransactionType.DEBIT, now - timedelta(days=25), Decimal("6700.00"), "Connaught Circus Commercial Rent"),
            ("TXN-VIKRAM-005", vikram_acc1, None, Decimal("42000.00"), Transaction.Category.SHOPPING, Transaction.TransactionType.DEBIT, now - timedelta(days=50), Decimal("48700.00"), "Storefront Lighting & Display Fixtures"),
        ]
        for tid, f_acc, t_acc, amt, cat, t_type, t_time, bal_after, rmks in vikram_txns:
            Transaction.objects.get_or_create(
                transaction_id=tid,
                defaults={
                    "from_account": f_acc,
                    "to_account": t_acc,
                    "amount": amt,
                    "category": cat,
                    "transaction_type": t_type,
                    "status": Transaction.Status.COMPLETED,
                    "timestamp": t_time,
                    "balance_after": bal_after,
                    "remarks": rmks
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Verified 5 Customers (sophia, rohan, aarav, priya, vikram)"))

        # =========================================================================
        # 9. DETERMINISTIC KYC REQUESTS FOR EMPLOYEE QUEUE
        # =========================================================================
        # Request 1: Aarav Sharma - APPROVED by Employee 1 (Ramesh)
        KYCRequest.objects.get_or_create(
            request_id="KYC-2024-001",
            defaults={
                "customer": aarav_cust,
                "assigned_employee": emp1_profile,
                "status": KYCRequest.Status.APPROVED,
                "document_type": "PAN & Biometric Aadhaar",
                "document_number": "AARAV1234S",
                "reviewed_by": emp1_profile,
                "reviewed_at": now - timedelta(days=55),
                "review_notes": "Identity and tax filing records verified. High net worth customer approved."
            }
        )

        # Request 2: Priya Patel - ASSIGNED to Employee 2 (Ananya Rao)
        KYCRequest.objects.get_or_create(
            request_id="KYC-2024-002",
            defaults={
                "customer": priya_cust,
                "loan_application": priya_app,
                "assigned_employee": emp2_profile,
                "status": KYCRequest.Status.ASSIGNED,
                "document_type": "PAN & Salary Slips (3M)",
                "document_number": "PATEL5678P",
                "review_notes": "Assigned to KYC operations officer for salary credit and employer verification."
            }
        )

        # Request 3: Vikram Malhotra - NEEDS_REVIEW (Assigned to Employee 1)
        KYCRequest.objects.get_or_create(
            request_id="KYC-2024-003",
            defaults={
                "customer": vikram_cust,
                "assigned_employee": emp1_profile,
                "status": KYCRequest.Status.NEEDS_REVIEW,
                "document_type": "PAN & GST Registration",
                "document_number": "MALHO9012M",
                "reviewed_by": emp1_profile,
                "reviewed_at": now - timedelta(days=1),
                "review_notes": "Address proof scan is blurry; please submit a clear recent municipal tax or electricity bill."
            }
        )

        # Request 4: Rohan Deshmukh - PENDING (Unassigned Queue)
        KYCRequest.objects.get_or_create(
            request_id="KYC-2024-004",
            defaults={
                "customer": rohan_cust,
                "status": KYCRequest.Status.PENDING,
                "document_type": "PAN & Driving License",
                "document_number": "DESHM1234K"
            }
        )

        # Request 5: Sophia Mehta - APPROVED by Employee 1
        sophia_cust = Customer.objects.filter(user__username="sophia").first()
        if sophia_cust:
            KYCRequest.objects.get_or_create(
                request_id="KYC-2024-005",
                defaults={
                    "customer": sophia_cust,
                    "assigned_employee": emp1_profile,
                    "status": KYCRequest.Status.APPROVED,
                    "document_type": "PAN & Passport",
                    "document_number": "ABCDE1234F",
                    "reviewed_by": emp1_profile,
                    "reviewed_at": now - timedelta(days=90),
                    "review_notes": "Premier retail banking relationship KYC verified."
                }
            )

        self.stdout.write(self.style.SUCCESS("[OK] Deterministic KYC Requests seeded (Pending, Assigned, Approved, Needs Review)."))

        # 10. Sample Customer In-App Notifications
        if priya_user:
            Notification.objects.get_or_create(
                user=priya_user,
                title="KYC Verification Assigned",
                defaults={
                    "message": "Your KYC documents for Home Loan application #LA-2024-5528 have been assigned to Officer Ananya Rao.",
                    "notification_type": Notification.NotificationType.LOAN_UPDATE,
                    "is_read": False,
                    "created_at": now - timedelta(hours=4)
                }
            )

        if vikram_user:
            Notification.objects.get_or_create(
                user=vikram_user,
                title="KYC Additional Review Required",
                defaults={
                    "message": "Your KYC verification requires additional review: Address proof scan is blurry; please submit a clear recent municipal tax or electricity bill.",
                    "notification_type": Notification.NotificationType.SECURITY,
                    "is_read": False,
                    "created_at": now - timedelta(days=1)
                }
            )

        if aarav_user:
            Notification.objects.get_or_create(
                user=aarav_user,
                title="KYC Verification Approved",
                defaults={
                    "message": "Your KYC verification has been approved. Your Finova Premier banking account is fully activated.",
                    "notification_type": Notification.NotificationType.SECURITY,
                    "is_read": True,
                    "created_at": now - timedelta(days=55)
                }
            )

        self.stdout.write(self.style.SUCCESS("=== FINOVA EXPANSION SEEDING COMPLETE ==="))
