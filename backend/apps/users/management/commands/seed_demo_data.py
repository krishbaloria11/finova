from decimal import Decimal
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.users.models import User, Customer, Employee
from apps.branches.models import Branch
from apps.accounts.models import AccountType, Account
from apps.transactions.models import Transaction, Beneficiary
from apps.loans.models import LoanType, Loan, LoanApplication
from apps.notifications.models import Notification
from apps.audit.models import AuditLog

class Command(BaseCommand):
    help = "Seeds the database with realistic Indian banking and loan data for Finova Silk & Glass demonstration."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Initializing Finova Seed Data Engine..."))

        # 1. Bank Branches (RBI Guideline Compliant)
        blr_branch, _ = Branch.objects.get_or_create(
            branch_code="BLR01",
            defaults={
                "branch_name": "Bengaluru Indiranagar Main",
                "ifsc": "FINO0001234",
                "address": "100 Feet Road, HAL 2nd Stage, Indiranagar",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560038",
                "phone": "+91 80 2520 1234",
                "manager_name": "Vikram Sengupta",
                "is_active": True
            }
        )

        mum_branch, _ = Branch.objects.get_or_create(
            branch_code="MUM01",
            defaults={
                "branch_name": "Mumbai Bandra Kurla Complex Flagship",
                "ifsc": "FINO0005678",
                "address": "G Block, BKC, Bandra East",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400051",
                "phone": "+91 22 6650 5678",
                "manager_name": "Pooja Deshmukh",
                "is_active": True
            }
        )

        del_branch, _ = Branch.objects.get_or_create(
            branch_code="DEL01",
            defaults={
                "branch_name": "New Delhi Connaught Place Central",
                "ifsc": "FINO0009101",
                "address": "Barakhamba Road, Connaught Place",
                "city": "New Delhi",
                "state": "Delhi",
                "pincode": "110001",
                "phone": "+91 11 2341 9101",
                "manager_name": "Rajesh Malhotra",
                "is_active": True
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Bank branches seeded (Bengaluru, Mumbai, Delhi)."))

        # 2. Account Types
        acc_savings, _ = AccountType.objects.get_or_create(
            code="SAVINGS",
            defaults={
                "name": "Primary Savings Account",
                "interest_rate_pa": Decimal("4.00"),
                "minimum_balance": Decimal("1000.00"),
                "description": "Standard retail savings account with RuPay Platinum debit access."
            }
        )

        acc_savings_sec, _ = AccountType.objects.get_or_create(
            code="SAVINGS_SEC",
            defaults={
                "name": "Secondary Savings Account",
                "interest_rate_pa": Decimal("4.50"),
                "minimum_balance": Decimal("5000.00"),
                "description": "High-yield interest bearing secondary savings account."
            }
        )

        acc_current, _ = AccountType.objects.get_or_create(
            code="CURRENT",
            defaults={
                "name": "Current Account Facility",
                "interest_rate_pa": Decimal("0.00"),
                "minimum_balance": Decimal("10000.00"),
                "description": "Commercial current facility with zero balance penalty exemption."
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Account types seeded."))

        # 3. Loan Product Types
        loan_home, _ = LoanType.objects.get_or_create(
            code="HOME",
            defaults={
                "name": "Home Loan",
                "base_interest_rate": Decimal("8.25"),
                "min_amount": Decimal("500000.00"),
                "max_amount": Decimal("50000000.00"),
                "min_tenure_months": 36,
                "max_tenure_months": 360,
                "processing_fee_percent": Decimal("0.35"),
                "description": "Affordable residential home loan facility with floating and fixed interest options.",
                "icon_name": "home"
            }
        )

        loan_personal, _ = LoanType.objects.get_or_create(
            code="PERSONAL",
            defaults={
                "name": "Personal Loan",
                "base_interest_rate": Decimal("11.50"),
                "min_amount": Decimal("50000.00"),
                "max_amount": Decimal("2500000.00"),
                "min_tenure_months": 12,
                "max_tenure_months": 60,
                "processing_fee_percent": Decimal("1.00"),
                "description": "Instant collateral-free personal credit facility for verified customers.",
                "icon_name": "person"
            }
        )

        loan_edu, _ = LoanType.objects.get_or_create(
            code="EDUCATION",
            defaults={
                "name": "Education Loan",
                "base_interest_rate": Decimal("9.00"),
                "min_amount": Decimal("100000.00"),
                "max_amount": Decimal("7500000.00"),
                "min_tenure_months": 24,
                "max_tenure_months": 120,
                "processing_fee_percent": Decimal("0.50"),
                "description": "Higher education financing for premier Indian and global institutions.",
                "icon_name": "school"
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Loan product types seeded."))

        # 4. Customer User: Sophia Mehta (Matches Prototype Exactly)
        user_sophia, created = User.objects.get_or_create(
            username="sophia",
            defaults={
                "email": "sophia.mehta@example.com",
                "first_name": "Sophia",
                "last_name": "Mehta",
                "role": User.Role.CUSTOMER,
                "phone": "+91 98450 12345"
            }
        )
        if created:
            user_sophia.set_password("Finova@2024")
            user_sophia.save()

        cust_sophia, _ = Customer.objects.get_or_create(
            user=user_sophia,
            defaults={
                "customer_id": "CUST-482109",
                "full_name": "Sophia Mehta",
                "pan_number": "ABCPM1234F",
                "aadhaar_last_four": "4821",
                "phone": "+91 98450 12345",
                "address": "Penthouse 14B, Palm Grove Residencies, Koramangala",
                "city": "Bengaluru",
                "state": "Karnataka",
                "pincode": "560034",
                "monthly_income": Decimal("145000.00"),
                "credit_score": 785,
                "credit_category": "Excellent",
                "kyc_status": Customer.KYCStatus.VERIFIED,
                "kyc_document_type": "PAN & Aadhaar Card",
                "kyc_document_number": "ABCPM1234F",
                "kyc_verified_at": timezone.now()
            }
        )

        # 5. Accounts for Sophia Mehta (Matches exact Stitch figures: ₹1,28,450.80 total)
        # Primary Account: ₹42,650.30
        acc_primary, _ = Account.objects.get_or_create(
            account_number="482190824821",
            defaults={
                "customer": cust_sophia,
                "branch": blr_branch,
                "account_type": acc_savings,
                "available_balance": Decimal("42650.30"),
                "ledger_balance": Decimal("43100.00"),
                "card_variant": "RuPay Platinum",
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        # Secondary Savings: ₹75,800.50
        acc_sec, _ = Account.objects.get_or_create(
            account_number="109284711092",
            defaults={
                "customer": cust_sophia,
                "branch": blr_branch,
                "account_type": acc_savings_sec,
                "available_balance": Decimal("75800.50"),
                "ledger_balance": Decimal("75800.50"),
                "card_variant": "Finova RuPay Gold",
                "status": Account.Status.ACTIVE,
                "is_primary": False
            }
        )

        # Current Facility: ₹10,000.00
        acc_curr, _ = Account.objects.get_or_create(
            account_number="993481029934",
            defaults={
                "customer": cust_sophia,
                "branch": mum_branch,
                "account_type": acc_current,
                "available_balance": Decimal("10000.00"),
                "ledger_balance": Decimal("10000.00"),
                "card_variant": "Business Commercial",
                "status": Account.Status.ACTIVE,
                "is_primary": False
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Customer Sophia Mehta and 3 connected accounts established (Total: INR 1,28,450.80)."))

        # 6. Active Home Loan facility: HL-4091
        due_date = date.today() + timedelta(days=5)
        loan_sophia, _ = Loan.objects.get_or_create(
            loan_id="HL-4091",
            defaults={
                "customer": cust_sophia,
                "loan_type": loan_home,
                "servicing_account": acc_primary,
                "principal_amount": Decimal("6000000.00"),
                "interest_rate": Decimal("8.25"),
                "tenure_months": 240,
                "monthly_emi": Decimal("28500.00"),
                "total_payable": Decimal("6840000.00"),
                "total_interest": Decimal("840000.00"),
                "outstanding_amount": Decimal("2850000.00"),
                "repaid_amount": Decimal("3150000.00"),
                "start_date": date(2020, 11, 15),
                "end_date": date(2040, 11, 15),
                "next_due_date": due_date,
                "auto_debit": True,
                "status": Loan.Status.ACTIVE
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Active Home Loan facility #HL-4091 seeded."))

        # 7. Frequent Payees / Beneficiaries for Sophia
        payees = [
            {
                "name": "Elena R.",
                "account_number": "902188219021",
                "ifsc_code": "FINO0005678",
                "bank_name": "Finova Bank BKC",
                "nickname": "Elena",
                "avatar_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuBKwbqviU7xOZnZrxHAEqhVJ2hBMobPe4maVSaAsiwRbSqeYafQSgS1Kzn_DY9hcaL9U6U5t1wjecnsg9cGq3wGGyHL_-hfF3wD_-GxcTp_AMP_NT3dePnlJHTmYe7-ZPC8sko-k40YGJ7HS1fwgPv5e_6VfLPksDODRPmXzYv52a7B5PJUhL_08ntAw-1PATwf_iBHhNlcksiXZvNmLF2gyo6BDMo2eBXR5AaB8KrwsMlp5r0DRftP"
            },
            {
                "name": "Rahul Verma",
                "account_number": "837199208371",
                "ifsc_code": "HDFC0001200",
                "bank_name": "HDFC Bank MG Road",
                "nickname": "Rahul",
                "avatar_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuDbp3dF0ADfpMYIbLU8AQ06M74wiNpLSveNgSe8qjRwF9Y2FZffJORHE93HxVo_YsgbWGJPIU7i4i6-ORlqTkOi1dhYTGn9E964X19iFLWDC3D04T4ZDHlYd_SC94Fx3yqrZufEBQTD_k6qL8AufEY4GpO-FcByChYwVCz96SVxZTULJk0aWFVIN07CSeOf0QgHppz9D2Zei8SAdvLPspaBM5nTtoUaNSZf6JnYkdXwBcqtyi93cUmz"
            },
            {
                "name": "Arjun Sharma",
                "account_number": "772183907721",
                "ifsc_code": "SBIN0004500",
                "bank_name": "State Bank of India",
                "nickname": "Arjun",
                "avatar_url": "https://lh3.googleusercontent.com/aida-public/AB6AXuAZtFwwtN4UkRJMPbW-4TyyjnKUarG1b4RBhaHQPQ8r4F6JfNPCoJnVF-arfBm1Aoarw88gQTQ_3ZP1CE_qgbe-Iw94qO4YN6Dow6YYRtK0s7-nsgX856stf617RYifEltPNuGeOQxeryDBnQswnzazRswoBsBXF3A01Eu3k0eNs9L7maxij5pxTSpUdpiUdERVKXbu1U1HmW3L3z6sncZOZVKa4AAtHygpSllcDkVU6ArumVmEw2n-"
            },
            {
                "name": "BESCOM Bangalore Electricity",
                "account_number": "000129840001",
                "ifsc_code": "FINO0001234",
                "bank_name": "BESCOM Utilities Billdesk",
                "nickname": "BESCOM",
                "avatar_url": ""
            }
        ]

        for p in payees:
            Beneficiary.objects.get_or_create(
                customer=cust_sophia,
                account_number=p["account_number"],
                ifsc_code=p["ifsc_code"],
                defaults={
                    "name": p["name"],
                    "bank_name": p["bank_name"],
                    "nickname": p["nickname"],
                    "avatar_url": p["avatar_url"],
                    "is_verified": True
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] Frequent payees seeded."))

        # 8. Ledger Transactions (Exact match to Stitch Table)
        now_dt = timezone.now()
        txns = [
            {
                "id": "TXN-20241110-001",
                "beneficiary": "Amazon India",
                "category": Transaction.Category.SHOPPING,
                "type": Transaction.TransactionType.DEBIT,
                "amount": Decimal("2499.00"),
                "account": acc_primary,
                "days_ago": 2,
                "remarks": "Order #408-9182312 Electronics & Books"
            },
            {
                "id": "TXN-20241108-002",
                "beneficiary": "Tata Consultancy Services",
                "category": Transaction.Category.SALARY,
                "type": Transaction.TransactionType.CREDIT,
                "amount": Decimal("145000.00"),
                "account": acc_primary,
                "days_ago": 4,
                "remarks": "Monthly Corporate Salary Credit Oct-Nov"
            },
            {
                "id": "TXN-20241101-003",
                "beneficiary": "Finova Home Loan EMI",
                "category": Transaction.Category.EMI_BILLS,
                "type": Transaction.TransactionType.EMI_PAYMENT,
                "amount": Decimal("28500.00"),
                "account": acc_primary,
                "days_ago": 11,
                "remarks": "Auto-debit for facility #HL-4091"
            },
            {
                "id": "TXN-20241031-004",
                "beneficiary": "Swiggy Dineout",
                "category": Transaction.Category.FOOD_DINING,
                "type": Transaction.TransactionType.DEBIT,
                "amount": Decimal("1840.00"),
                "account": acc_primary,
                "days_ago": 12,
                "remarks": "UPI QR restaurant payment"
            },
            {
                "id": "TXN-20241028-005",
                "beneficiary": "BESCOM Bangalore Electricity",
                "category": Transaction.Category.UTILITIES,
                "type": Transaction.TransactionType.DEBIT,
                "amount": Decimal("1250.00"),
                "account": acc_primary,
                "days_ago": 15,
                "remarks": "Consumer ID #4091823 Utility Settlement"
            },
            {
                "id": "TXN-20241025-006",
                "beneficiary": "Fixed Deposit Quarterly Interest",
                "category": Transaction.Category.INVESTMENT,
                "type": Transaction.TransactionType.CREDIT,
                "amount": Decimal("3420.50"),
                "account": acc_sec,
                "days_ago": 18,
                "remarks": "FD #FD8901 Quarterly Interest Auto-credit"
            }
        ]

        for t in txns:
            t_time = now_dt - timedelta(days=t["days_ago"])
            Transaction.objects.get_or_create(
                transaction_id=t["id"],
                defaults={
                    "from_account": t["account"] if t["type"] in [Transaction.TransactionType.DEBIT, Transaction.TransactionType.EMI_PAYMENT] else None,
                    "to_account": t["account"] if t["type"] == Transaction.TransactionType.CREDIT else None,
                    "beneficiary_name": t["beneficiary"],
                    "transaction_type": t["type"],
                    "category": t["category"],
                    "amount": t["amount"],
                    "balance_after": t["account"].available_balance,
                    "status": Transaction.Status.COMPLETED,
                    "remarks": t["remarks"],
                    "timestamp": t_time
                }
            )
        self.stdout.write(self.style.SUCCESS("[OK] 6 real-world banking transactions seeded."))

        # 9. Notifications for Sophia
        Notification.objects.get_or_create(
            user=user_sophia,
            title="Home Loan EMI Due in 5 Days",
            defaults={
                "message": f"Home Loan EMI of ₹28,500.00 will be auto-debited from Savings •••• 4821 on {due_date.strftime('%a, %b %d')}.",
                "notification_type": Notification.NotificationType.PAYMENT_DUE,
                "is_read": False
            }
        )
        Notification.objects.get_or_create(
            user=user_sophia,
            title="Salary Credited",
            defaults={
                "message": "₹1,45,000.00 has been credited to your Primary Savings account from Tata Consultancy Services.",
                "notification_type": Notification.NotificationType.TRANSFER_SUCCESS,
                "is_read": True
            }
        )
        self.stdout.write(self.style.SUCCESS("[OK] Notifications seeded."))

        # 10. Staff Users: Bank Employee & Administrator
        user_emp, created = User.objects.get_or_create(
            username="employee",
            defaults={
                "email": "employee@finova.in",
                "first_name": "Ramesh",
                "last_name": "Iyer",
                "role": User.Role.EMPLOYEE,
                "phone": "+91 98450 99881",
                "is_staff": True
            }
        )
        if created:
            user_emp.set_password("Finova@2024")
            user_emp.save()

        emp_profile, _ = Employee.objects.get_or_create(
            user=user_emp,
            defaults={
                "employee_id": "EMP-BLR-101",
                "full_name": "Ramesh Iyer",
                "branch": blr_branch,
                "designation": "Senior Credit Underwriter",
                "department": "Retail Credit & Risk Assessment",
                "is_active": True
            }
        )

        user_admin, created = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@finova.in",
                "first_name": "System",
                "last_name": "Admin",
                "role": User.Role.ADMIN,
                "phone": "+91 98450 00001",
                "is_staff": True,
                "is_superuser": True
            }
        )
        if created:
            user_admin.set_password("FinovaAdmin@2024")
            user_admin.save()
        self.stdout.write(self.style.SUCCESS("[OK] Bank Employee (employee) and Administrator (admin) credentials created."))

        # 11. Underwriting Demo: Sample Loan Applications for Employee Review
        cust_rohan_user, _ = User.objects.get_or_create(
            username="rohan",
            defaults={"email": "rohan.d@example.com", "first_name": "Rohan", "last_name": "Deshmukh", "role": User.Role.CUSTOMER}
        )
        if _:
            cust_rohan_user.set_password("Finova@2024")
            cust_rohan_user.save()

        cust_rohan, _ = Customer.objects.get_or_create(
            user=cust_rohan_user,
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
                "kyc_document_type": "PAN & Driving License",
                "kyc_document_number": "DESHM1234K"
            }
        )

        acc_rohan, _ = Account.objects.get_or_create(
            account_number="482199001122",
            defaults={
                "customer": cust_rohan,
                "branch": mum_branch,
                "account_type": acc_savings,
                "available_balance": Decimal("35000.00"),
                "ledger_balance": Decimal("35000.00"),
                "card_variant": "Finova RuPay Gold",
                "status": Account.Status.ACTIVE,
                "is_primary": True
            }
        )

        LoanApplication.objects.get_or_create(
            application_id="LA-2024-9182",
            defaults={
                "customer": cust_rohan,
                "loan_type": loan_personal,
                "requested_amount": Decimal("350000.00"),
                "tenure_months": 24,
                "proposed_interest_rate": Decimal("11.50"),
                "calculated_emi": Decimal("16400.00"),
                "purpose": "Home renovation and electronics upgrade",
                "employment_type": "Salaried",
                "employer_name": "Infosys Ltd",
                "monthly_income": Decimal("95000.00"),
                "existing_obligations": Decimal("8000.00"),
                "pan_number": "DESHM1234K",
                "residential_address": "402, Sea Crest Towers, Worli, Mumbai",
                "status": LoanApplication.Status.UNDER_REVIEW
            }
        )

        # 12. Audit Logs
        AuditLog.objects.get_or_create(
            action="SYSTEM_INIT",
            defaults={
                "user": user_admin,
                "ip_address": "127.0.0.1",
                "record_type": "System",
                "record_id": "INIT-001",
                "details": "Finova Silk & Glass core banking database initialized with seed records."
            }
        )

        self.stdout.write(self.style.SUCCESS("[OK] Finova Banking database seeded successfully! Ready for demonstration."))
