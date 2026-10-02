from decimal import Decimal
from django.test import TestCase
from apps.users.models import User, Customer, Employee
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.loans.models import LoanType, LoanApplication, Loan
from apps.loans.services import LoanService

class LoanServiceTestCase(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            branch_code="BLR01", branch_name="Bengaluru Branch",
            ifsc="FINO0001234", address="HAL 2nd Stage",
            city="Bengaluru", state="Karnataka", pincode="560038",
            manager_name="Branch Manager"
        )
        self.acc_type = AccountType.objects.create(code="SAVINGS", name="Savings", interest_rate_pa=Decimal("4.00"))

        self.user = User.objects.create_user(username="borrower", email="b@test.com", password="Pass@123")
        self.customer = Customer.objects.create(
            user=self.user, customer_id="CUST-B1", full_name="Borrower Customer",
            pan_number="ABCDE9999Z", aadhaar_last_four="8888", phone="9888877777",
            address="Borrower Address", city="Bengaluru", state="Karnataka", pincode="560001"
        )
        self.account = Account.objects.create(
            account_number="482188881234", customer=self.customer,
            branch=self.branch, account_type=self.acc_type,
            available_balance=Decimal("100000.00"), ledger_balance=Decimal("100000.00"),
            is_primary=True
        )
        self.loan_type = LoanType.objects.create(
            code="HOME", name="Home Loan",
            base_interest_rate=Decimal("8.25")
        )

        self.emp_user = User.objects.create_user(username="officer", email="o@test.com", password="Pass@123", role=User.Role.EMPLOYEE)
        self.employee = Employee.objects.create(
            user=self.emp_user, employee_id="EMP-01", full_name="Officer Ramesh",
            branch=self.branch
        )

    def test_emi_calculation_formula(self):
        # Principal: 10,00,000, Rate: 10% p.a., Tenure: 12 months
        result = LoanService.calculate_emi(
            principal=Decimal("1000000.00"),
            annual_rate=Decimal("10.00"),
            tenure_months=12
        )
        # Monthly rate = 10 / 1200 = 0.00833333
        # Standard EMI for 10L at 10% for 1 year is approx 87,915.89
        self.assertAlmostEqual(float(result['monthly_emi']), 87915.89, places=1)
        self.assertTrue(result['total_payable'] > Decimal("1000000.00"))

    def test_loan_underwriting_approval_and_disbursement(self):
        app = LoanApplication.objects.create(
            application_id="LA-TEST-001",
            customer=self.customer,
            loan_type=self.loan_type,
            requested_amount=Decimal("500000.00"),
            tenure_months=60,
            proposed_interest_rate=Decimal("8.25"),
            purpose="Home Extension",
            employment_type="Salaried",
            monthly_income=Decimal("80000.00"),
            pan_number="ABCDE9999Z"
        )

        initial_balance = self.account.available_balance

        approved_app = LoanService.review_application(
            application_id=app.id,
            decision="APPROVE",
            reviewer_employee=self.employee,
            review_notes="All documents verified.",
            sanction_account_id=self.account.id
        )

        self.assertEqual(approved_app.status, LoanApplication.Status.APPROVED)
        sanctioned_loan = Loan.objects.get(customer=self.customer, status=Loan.Status.ACTIVE)
        self.assertEqual(sanctioned_loan.principal_amount, Decimal("500000.00"))
        self.assertEqual(sanctioned_loan.outstanding_amount, Decimal("500000.00"))

        # Account should be credited with the disbursed amount
        self.account.refresh_from_db()
        self.assertEqual(self.account.available_balance, initial_balance + Decimal("500000.00"))

    def test_pay_emi_transaction(self):
        # Create active loan
        loan = Loan.objects.create(
            loan_id="HL-TEST-01",
            customer=self.customer,
            loan_type=self.loan_type,
            servicing_account=self.account,
            principal_amount=Decimal("100000.00"),
            interest_rate=Decimal("8.25"),
            tenure_months=12,
            monthly_emi=Decimal("8710.00"),
            total_payable=Decimal("104520.00"),
            total_interest=Decimal("4520.00"),
            outstanding_amount=Decimal("100000.00"),
            repaid_amount=Decimal("0.00"),
            start_date="2024-01-01",
            end_date="2025-01-01",
            next_due_date="2024-02-01",
            status=Loan.Status.ACTIVE
        )

        initial_acc_balance = self.account.available_balance
        payment = LoanService.pay_emi(
            loan_id=loan.id,
            account_id=self.account.id,
            amount=Decimal("8710.00")
        )

        loan.refresh_from_db()
        self.account.refresh_from_db()

        self.assertEqual(payment.amount_paid, Decimal("8710.00"))
        self.assertEqual(self.account.available_balance, initial_acc_balance - Decimal("8710.00"))
        self.assertTrue(loan.outstanding_amount < Decimal("100000.00"))
        self.assertEqual(loan.repaid_amount, Decimal("8710.00"))
