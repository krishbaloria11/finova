from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.users.models import User, Customer, Employee, KYCRequest
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.loans.models import LoanType, LoanApplication, Loan
from apps.transactions.models import Transaction
from apps.notifications.models import Notification
from apps.audit.models import AuditLog


class FinovaAPIIntegrationTestCase(TestCase):
    """
    Comprehensive API & Integration test suite for Finova Silk & Glass Banking System.
    Validates:
    - Authentication and Role-Based Access Control (Customer, Employee, Admin)
    - Customer Data Isolation (Tenancy)
    - Simulated Fund Transfers (Atomicity, Validation, Audit Trail, Ledger Updates)
    - Loan Application, Underwriting Review, and Fund Disbursement
    - EMI Calculation and Atomic Installment Payments
    - Notifications Center and Read Receipts
    - Admin System Stats and Audit Logging
    """

    def setUp(self):
        self.client = APIClient()

        # 1. Branch Setup
        self.branch = Branch.objects.create(
            branch_code="BLR01",
            branch_name="Bengaluru Indiranagar",
            ifsc="FINO0001234",
            address="100ft Road, Indiranagar",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            manager_name="Vikram Sengupta"
        )

        # 2. Account Types Setup
        self.savings_type = AccountType.objects.create(
            code="SAVINGS",
            name="Premier Savings Account",
            interest_rate_pa=Decimal("4.50")
        )
        self.current_type = AccountType.objects.create(
            code="CURRENT",
            name="Business Advantage Current",
            interest_rate_pa=Decimal("0.00")
        )

        # 3. Loan Types Setup
        self.home_loan_type = LoanType.objects.create(
            code="HOME",
            name="Home Loan",
            base_interest_rate=Decimal("8.25"),
            min_amount=Decimal("500000.00"),
            max_amount=Decimal("10000000.00"),
            min_tenure_months=60,
            max_tenure_months=360
        )

        # 4. User 1: Customer (Sophia Mehta)
        self.customer_user = User.objects.create_user(
            username="sophia",
            email="sophia@example.com",
            password="Finova@2024",
            role=User.Role.CUSTOMER,
            first_name="Sophia",
            last_name="Mehta"
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            customer_id="CUST-482109",
            full_name="Sophia Mehta",
            pan_number="ABCPM1234F",
            aadhaar_last_four="4821",
            phone="+91 98450 12345",
            address="Penthouse 14B, Palm Grove Residencies",
            city="Bengaluru",
            state="Karnataka",
            pincode="560034",
            monthly_income=Decimal("145000.00"),
            credit_score=785,
            credit_category="Excellent",
            kyc_status=Customer.KYCStatus.VERIFIED
        )
        self.customer_acc1 = Account.objects.create(
            account_number="482190824821",
            customer=self.customer,
            branch=self.branch,
            account_type=self.savings_type,
            available_balance=Decimal("128450.75"),
            ledger_balance=Decimal("128450.75"),
            is_primary=True,
            status=Account.Status.ACTIVE
        )
        self.customer_acc2 = Account.objects.create(
            account_number="482190824822",
            customer=self.customer,
            branch=self.branch,
            account_type=self.current_type,
            available_balance=Decimal("45000.00"),
            ledger_balance=Decimal("45000.00"),
            is_primary=False,
            status=Account.Status.ACTIVE
        )

        # 5. User 2: Counterparty Customer (Aarav Patel)
        self.counterparty_user = User.objects.create_user(
            username="aarav",
            email="aarav@example.com",
            password="Finova@2024",
            role=User.Role.CUSTOMER,
            first_name="Aarav",
            last_name="Patel"
        )
        self.counterparty_cust = Customer.objects.create(
            user=self.counterparty_user,
            customer_id="CUST-109842",
            full_name="Aarav Patel",
            pan_number="ABCPA9876K",
            aadhaar_last_four="9876",
            phone="+91 98111 22233",
            address="42 MG Road",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            monthly_income=Decimal("95000.00"),
            credit_score=740,
            credit_category="Good",
            kyc_status=Customer.KYCStatus.VERIFIED
        )
        self.counterparty_acc = Account.objects.create(
            account_number="482155667788",
            customer=self.counterparty_cust,
            branch=self.branch,
            account_type=self.savings_type,
            available_balance=Decimal("20000.00"),
            ledger_balance=Decimal("20000.00"),
            is_primary=True,
            status=Account.Status.ACTIVE
        )

        # 6. User 3: Bank Employee / Underwriter (Ramesh Iyer)
        self.employee_user = User.objects.create_user(
            username="employee",
            email="ramesh@finova.internal",
            password="Finova@2024",
            role=User.Role.EMPLOYEE,
            first_name="Ramesh",
            last_name="Iyer"
        )
        self.employee = Employee.objects.create(
            user=self.employee_user,
            employee_id="EMP-FIN-088",
            full_name="Ramesh Iyer",
            designation="Senior Credit Underwriter",
            branch=self.branch
        )

        # 7. User 4: System Administrator (Admin)
        self.admin_user = User.objects.create_user(
            username="admin",
            email="admin@finova.internal",
            password="FinovaAdmin@2024",
            role=User.Role.ADMIN,
            first_name="Finova",
            last_name="Admin",
            is_staff=True
        )

    # -------------------------------------------------------------
    # 1. Role-Based Permissions & Authentication Tests
    # -------------------------------------------------------------
    def test_anonymous_access_denied(self):
        """Unauthenticated requests to secured endpoints must return 401 Unauthorized."""
        for endpoint in ['/api/dashboard/', '/api/accounts/', '/api/transfers/', '/api/loans/', '/api/admin/stats/']:
            response = self.client.get(endpoint)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED, f"Expected 401 for {endpoint}")

    def test_customer_cannot_access_admin_stats(self):
        """Customers must receive 403 Forbidden when attempting to access executive admin analytics."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_customer_cannot_review_loan_applications(self):
        """Customers cannot approve or review loan applications."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.post('/api/loan-applications/1/review/', {
            'decision': 'APPROVED',
            'notes': 'Self approval should fail'
        })
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_admin_stats(self):
        """Admins have full access to management statistics."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/admin/stats/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_customers', response.data)
        self.assertIn('total_deposits', response.data)
        self.assertIn('recent_audit_logs', response.data)

    def test_customer_data_isolation(self):
        """Customers only see their own accounts and transaction ledger."""
        self.client.force_authenticate(user=self.customer_user)
        response = self.client.get('/api/accounts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data['results'] if isinstance(response.data, dict) and 'results' in response.data else response.data
        acc_numbers = [acc['account_number'] for acc in results]
        self.assertIn(self.customer_acc1.account_number, acc_numbers)
        self.assertIn(self.customer_acc2.account_number, acc_numbers)
        self.assertNotIn(self.counterparty_acc.account_number, acc_numbers)

    # -------------------------------------------------------------
    # 2. Simulated Money Transfer Workflow (ACID & TransferService)
    # -------------------------------------------------------------
    def test_api_transfer_successful(self):
        """
        Verify complete simulated transfer flow:
        - Validation
        - Atomic debit and credit
        - Transaction records
        - Balance updates reflected in frontend response
        - Audit log and notification generated
        """
        self.client.force_authenticate(user=self.customer_user)
        transfer_amount = Decimal("5000.00")
        initial_sender_balance = self.customer_acc1.available_balance
        initial_recipient_balance = self.counterparty_acc.available_balance

        payload = {
            'from_account_id': self.customer_acc1.id,
            'to_account_number': self.counterparty_acc.account_number,
            'confirm_account_number': self.counterparty_acc.account_number,
            'to_ifsc': self.branch.ifsc,
            'beneficiary_name': "Aarav Patel",
            'amount': str(transfer_amount),
            'category': 'TRANSFER',
            'remarks': 'Project Collaboration Share'
        }

        response = self.client.post('/api/transfers/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('transaction', response.data)
        txn_data = response.data['transaction']

        # Verify DB updates
        self.customer_acc1.refresh_from_db()
        self.counterparty_acc.refresh_from_db()

        self.assertEqual(self.customer_acc1.available_balance, initial_sender_balance - transfer_amount)
        self.assertEqual(self.counterparty_acc.available_balance, initial_recipient_balance + transfer_amount)
        self.assertEqual(Decimal(str(txn_data['amount'])), transfer_amount)
        self.assertEqual(txn_data['status'], 'COMPLETED')

        # Verify notification created
        notif = Notification.objects.filter(user=self.customer_user).first()
        self.assertIsNotNone(notif)
        self.assertEqual(notif.notification_type, Notification.NotificationType.TRANSFER_SUCCESS)

        # Verify audit log
        audit = AuditLog.objects.filter(action="MONEY_TRANSFER").first()
        self.assertIsNotNone(audit)

    def test_api_transfer_insufficient_funds_rejected(self):
        """Simulated transfer with amount > available balance must be rejected atomically."""
        self.client.force_authenticate(user=self.customer_user)
        excessive_amount = self.customer_acc1.available_balance + Decimal("10000.00")

        payload = {
            'from_account_id': self.customer_acc1.id,
            'to_account_number': self.counterparty_acc.account_number,
            'confirm_account_number': self.counterparty_acc.account_number,
            'to_ifsc': self.branch.ifsc,
            'beneficiary_name': "Aarav Patel",
            'amount': str(excessive_amount)
        }

        response = self.client.post('/api/transfers/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Sender balance must remain untouched
        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.available_balance, Decimal("128450.75"))

    def test_api_transfer_invalid_account_mismatch(self):
        """Account number mismatch between account and confirm_account must fail validation."""
        self.client.force_authenticate(user=self.customer_user)
        payload = {
            'from_account_id': self.customer_acc1.id,
            'to_account_number': "482155667788",
            'confirm_account_number': "482155667799",
            'to_ifsc': self.branch.ifsc,
            'beneficiary_name': "Aarav Patel",
            'amount': "500.00"
        }
        response = self.client.post('/api/transfers/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # -------------------------------------------------------------
    # 3. Loan Application & Underwriting Workflow
    # -------------------------------------------------------------
    def test_loan_application_and_employee_approval_flow(self):
        """
        Verify end-to-end Loan Workflow:
        1. Customer submits loan application via API.
        2. Application is marked UNDER_REVIEW.
        3. Employee logs in, reviews application, and approves it.
        4. Active Loan is automatically created with calculated EMI.
        5. Principal amount is disbursed directly into borrower account.
        """
        # 1. Customer applies
        self.client.force_authenticate(user=self.customer_user)
        apply_payload = {
            'loan_type': self.home_loan_type.id,
            'requested_amount': '2500000.00',
            'tenure_months': 120,
            'purpose': 'New Home Construction',
            'employment_type': 'Salaried',
            'employer_name': 'Tech Corp India',
            'monthly_income': '145000.00'
        }
        apply_resp = self.client.post('/api/loan-applications/', apply_payload, format='json')
        self.assertEqual(apply_resp.status_code, status.HTTP_201_CREATED)
        app_id = apply_resp.data['id']
        self.assertEqual(apply_resp.data['status'], 'UNDER_REVIEW')
        self.assertTrue(Decimal(str(apply_resp.data['calculated_emi'])) > 0)

        # 2. Employee reviews and approves
        initial_balance = self.customer_acc1.available_balance
        self.client.force_authenticate(user=self.employee_user)
        review_resp = self.client.post(f'/api/loan-applications/{app_id}/review/', {
            'decision': 'APPROVED',
            'notes': 'Satisfactory CIBIL 785 score. Income verified.',
            'sanction_account_id': self.customer_acc1.id
        }, format='json')

        self.assertEqual(review_resp.status_code, status.HTTP_200_OK)
        self.assertEqual(review_resp.data['status'], 'APPROVED')

        # 3. Verify Loan created and Disbursed into Account
        created_loan = Loan.objects.filter(customer=self.customer, status=Loan.Status.ACTIVE).first()
        self.assertIsNotNone(created_loan)
        self.assertEqual(created_loan.principal_amount, Decimal("2500000.00"))
        self.assertEqual(created_loan.outstanding_amount, Decimal("2500000.00"))

        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.available_balance, initial_balance + Decimal("2500000.00"))

    # -------------------------------------------------------------
    # 4. EMI Calculation & Payment Workflow
    # -------------------------------------------------------------
    def test_emi_payment_workflow(self):
        """
        Verify simulated EMI payment:
        - Debits account balance
        - Decreases loan outstanding amount
        - Increases repaid amount
        - Creates payment record and notification
        """
        # Create active loan
        loan = Loan.objects.create(
            loan_id="HL-ACTIVE-01",
            customer=self.customer,
            loan_type=self.home_loan_type,
            servicing_account=self.customer_acc1,
            principal_amount=Decimal("1000000.00"),
            interest_rate=Decimal("8.25"),
            tenure_months=120,
            monthly_emi=Decimal("12265.00"),
            total_payable=Decimal("1471800.00"),
            total_interest=Decimal("471800.00"),
            outstanding_amount=Decimal("1000000.00"),
            repaid_amount=Decimal("0.00"),
            start_date="2024-01-01",
            end_date="2034-01-01",
            next_due_date="2024-02-01",
            status=Loan.Status.ACTIVE
        )

        initial_acc_bal = self.customer_acc1.available_balance
        self.client.force_authenticate(user=self.customer_user)

        pay_resp = self.client.post('/api/loans/pay-emi/', {
            'loan_id': loan.id,
            'account_id': self.customer_acc1.id,
            'amount': '12265.00'
        }, format='json')

        self.assertEqual(pay_resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('payment', pay_resp.data)

        # Check DB states
        loan.refresh_from_db()
        self.customer_acc1.refresh_from_db()

        self.assertEqual(self.customer_acc1.available_balance, initial_acc_bal - Decimal("12265.00"))
        self.assertTrue(loan.outstanding_amount < Decimal("1000000.00"))
        self.assertEqual(loan.repaid_amount, Decimal("12265.00"))

    # -------------------------------------------------------------
    # 5. Notifications API Flow
    # -------------------------------------------------------------
    def test_notifications_lifecycle(self):
        """Verify fetching notifications, marking individual read, and mark all read."""
        n1 = Notification.objects.create(
            user=self.customer_user,
            title="System Alert 1",
            message="Your statement is ready",
            notification_type=Notification.NotificationType.SYSTEM
        )
        n2 = Notification.objects.create(
            user=self.customer_user,
            title="System Alert 2",
            message="Security check completed",
            notification_type=Notification.NotificationType.SECURITY
        )

        self.client.force_authenticate(user=self.customer_user)

        # 1. Fetch
        resp = self.client.get('/api/notifications/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        notifs = resp.data['results'] if isinstance(resp.data, dict) and 'results' in resp.data else resp.data
        self.assertEqual(len(notifs), 2)

        # 2. Mark one read
        patch_resp = self.client.patch(f'/api/notifications/{n1.id}/mark_read/')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        n1.refresh_from_db()
        self.assertTrue(n1.is_read)

        # 3. Mark all read
        post_resp = self.client.post('/api/notifications/mark_all_read/')
        self.assertEqual(post_resp.status_code, status.HTTP_200_OK)
        n2.refresh_from_db()
        self.assertTrue(n2.is_read)

    # -------------------------------------------------------------
    # 6. Authentication Logout Flow
    # -------------------------------------------------------------
    def test_logout_flow(self):
        """Verify logout deletes auth token and creates an audit log entry."""
        from rest_framework.authtoken.models import Token
        token, _ = Token.objects.get_or_create(user=self.customer_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')

        resp = self.client.post('/api/auth/logout/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['message'], 'Logged out successfully.')

        # Verify token deleted
        self.assertFalse(Token.objects.filter(user=self.customer_user).exists())

        # Verify audit log
        audit = AuditLog.objects.filter(user=self.customer_user, action="USER_LOGOUT").first()
        self.assertIsNotNone(audit)

    def test_reset_demo_data_aborts_when_not_debug(self):
        """Verify reset_demo_data refuses to run if DEBUG is False."""
        from django.core.management import call_command, CommandError
        from django.test import override_settings

        with override_settings(DEBUG=False):
            with self.assertRaises(CommandError) as ctx:
                call_command('reset_demo_data', no_input=True)
            self.assertIn("SAFETY ABORT", str(ctx.exception))

    def test_reset_demo_data_execution_and_idempotency(self):
        """Verify reset_demo_data restores clean state and running twice does not duplicate records."""
        from django.core.management import call_command
        from django.test import override_settings
        from io import StringIO

        with override_settings(DEBUG=True):
            out = StringIO()
            # First reset run
            call_command('reset_demo_data', force=True, no_input=True, stdout=out)
            self.assertIn("successfully restored", out.getvalue())

            # Check key seeded demo objects exist
            self.assertTrue(User.objects.filter(username="sophia").exists())
            self.assertTrue(User.objects.filter(username="employee").exists())
            self.assertTrue(User.objects.filter(username="admin").exists())
            user_count_1 = User.objects.count()
            branch_count_1 = Branch.objects.count()
            account_count_1 = Account.objects.count()

            # Second reset run (Idempotency test)
            out2 = StringIO()
            call_command('reset_demo_data', force=True, no_input=True, stdout=out2)
            self.assertIn("successfully restored", out2.getvalue())

            user_count_2 = User.objects.count()
            branch_count_2 = Branch.objects.count()
            account_count_2 = Account.objects.count()

            self.assertEqual(user_count_1, user_count_2, "Reset command must be idempotent: user count unchanged")
            self.assertEqual(branch_count_1, branch_count_2, "Reset command must be idempotent: branch count unchanged")
            self.assertEqual(account_count_1, account_count_2, "Reset command must be idempotent: account count unchanged")

    def test_admin_account_freeze_unfreeze_and_permissions(self):
        """Verify role permissions and behavior of administrative account freeze/unfreeze."""
        # 1. Unauthenticated -> 401
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/freeze/', {'reason': 'AML flag'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # 2. Customer -> 403
        self.client.force_authenticate(user=self.customer_user)
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/freeze/', {'reason': 'AML flag'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 3. Employee -> 403
        self.client.force_authenticate(user=self.employee_user)
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/freeze/', {'reason': 'AML flag'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 4. Admin without reason -> 400
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/freeze/', {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Admin with reason -> 200 and status FROZEN
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/freeze/', {'reason': 'AML velocity alert'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.status, Account.Status.FROZEN)

        # 6. Verify audit log created
        audit = AuditLog.objects.filter(action="ACCOUNT_FROZEN", record_id=self.customer_acc1.account_number).first()
        self.assertIsNotNone(audit)
        self.assertIn("AML velocity alert", audit.details)

        # 7. Customer cannot transfer from frozen account
        self.client.force_authenticate(user=self.customer_user)
        transfer_payload = {
            "from_account_id": self.customer_acc1.id,
            "to_account_number": self.counterparty_acc.account_number,
            "confirm_account_number": self.counterparty_acc.account_number,
            "to_ifsc": "FINO0001234",
            "beneficiary_name": "Aarav Patel",
            "amount": "1000.00",
            "category": "TRANSFER",
            "remarks": "Test transfer from frozen"
        }
        resp = self.client.post('/api/transfers/', transfer_payload)
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("FROZEN", str(resp.data))

        # 8. Admin unfreezes with reason -> 200 and status ACTIVE
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/unfreeze/', {'reason': 'Investigation cleared'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.status, Account.Status.ACTIVE)

        unfreeze_audit = AuditLog.objects.filter(action="ACCOUNT_UNFROZEN", record_id=self.customer_acc1.account_number).first()
        self.assertIsNotNone(unfreeze_audit)

    def test_admin_account_activate_deactivate(self):
        """Verify administrative account activation and deactivation lifecycle."""
        self.client.force_authenticate(user=self.admin_user)

        # Deactivate
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/deactivate/', {'reason': 'Customer requested closure'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.status, Account.Status.CLOSED)

        # Reactivate
        resp = self.client.post(f'/api/accounts/{self.customer_acc1.id}/activate/', {'reason': 'Customer reopening petition'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer_acc1.refresh_from_db()
        self.assertEqual(self.customer_acc1.status, Account.Status.ACTIVE)

    def test_admin_transaction_reversal_atomic_and_permissions(self):
        """Verify transaction reversal atomicity, permissions, balance restoration, and audit trail."""
        from apps.transactions.services import TransferService

        # 1. Execute initial valid transfer
        sender_initial_bal = self.customer_acc1.available_balance
        recipient_initial_bal = self.counterparty_acc.available_balance
        transfer_amount = Decimal("5000.00")

        txn = TransferService.execute_transfer(
            from_account_id=self.customer_acc1.id,
            to_account_number=self.counterparty_acc.account_number,
            to_ifsc="FINO0001234",
            beneficiary_name="Aarav Patel",
            amount=transfer_amount,
            category=Transaction.Category.TRANSFER,
            remarks="Legitimate transfer for test",
            user=self.customer_user
        )

        self.customer_acc1.refresh_from_db()
        self.counterparty_acc.refresh_from_db()
        self.assertEqual(self.customer_acc1.available_balance, sender_initial_bal - transfer_amount)
        self.assertEqual(self.counterparty_acc.available_balance, recipient_initial_bal + transfer_amount)

        # 2. Permission checks on Reversal endpoint
        # Unauthenticated -> 401
        self.client.force_authenticate(user=None)
        resp = self.client.post(f'/api/transactions/{txn.id}/reverse/', {'reason': 'Reversal test'})
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

        # Customer -> 403
        self.client.force_authenticate(user=self.customer_user)
        resp = self.client.post(f'/api/transactions/{txn.id}/reverse/', {'reason': 'Reversal test'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Employee -> 403
        self.client.force_authenticate(user=self.employee_user)
        resp = self.client.post(f'/api/transactions/{txn.id}/reverse/', {'reason': 'Reversal test'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Admin without reason -> 400
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.post(f'/api/transactions/{txn.id}/reverse/', {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Successful Admin Reversal
        resp = self.client.post(f'/api/transactions/{txn.id}/reverse/', {'reason': 'Erroneous duplicate debit confirmed'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['status'], 'REVERSED')

        # 4. Verify original transaction status
        txn.refresh_from_db()
        self.assertEqual(txn.status, Transaction.Status.REVERSED)

        # 5. Verify balances restored atomically
        self.customer_acc1.refresh_from_db()
        self.counterparty_acc.refresh_from_db()
        self.assertEqual(self.customer_acc1.available_balance, sender_initial_bal)
        self.assertEqual(self.counterparty_acc.available_balance, recipient_initial_bal)

        # 6. Verify compensating transaction in ledger
        compensating_tx = Transaction.objects.filter(reference_number=resp.data['reversal_reference']).first()
        self.assertIsNotNone(compensating_tx)
        self.assertEqual(compensating_tx.amount, transfer_amount)
        self.assertEqual(compensating_tx.category, Transaction.Category.OTHER)

        # 7. Verify Audit Log
        audit = AuditLog.objects.filter(action="TRANSACTION_REVERSED", record_id=txn.transaction_id).first()
        self.assertIsNotNone(audit)
        self.assertIn("Erroneous duplicate debit", audit.details)

        # 8. Attempting second reversal -> 400
        resp_dup = self.client.post(f'/api/transactions/{txn.id}/reverse/', {'reason': 'Duplicate attempt'})
        self.assertEqual(resp_dup.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already been reversed", str(resp_dup.data['error']))

    def test_employee_customer_lookup_and_isolation(self):
        """Verify staff customer search and profile detail inspection."""
        # Employee can search customers
        self.client.force_authenticate(user=self.employee_user)
        resp = self.client.get('/api/customers/?search=Sophia')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) >= 1)
        self.assertEqual(resp.data[0]['name'], 'Sophia Mehta')
        self.assertTrue('accounts' in resp.data[0])

        # Employee can view full customer detail
        resp_det = self.client.get(f'/api/customers/{self.customer.id}/')
        self.assertEqual(resp_det.status_code, status.HTTP_200_OK)
        self.assertIn('customer', resp_det.data)
        self.assertIn('accounts', resp_det.data)
        self.assertIn('recent_transactions', resp_det.data)

        # Customer cannot view another customer detail
        self.client.force_authenticate(user=self.customer_user)
        resp_cust = self.client.get(f'/api/customers/{self.counterparty_cust.id}/')
        self.assertEqual(resp_cust.status_code, status.HTTP_403_FORBIDDEN)

    def test_employee_kyc_workflow(self):
        """Verify KYC verification, rejection, and review actions with audit logging."""
        # Set customer KYC to PENDING
        self.customer.kyc_status = Customer.KYCStatus.PENDING
        self.customer.save()

        # Customer cannot verify own KYC
        self.client.force_authenticate(user=self.customer_user)
        resp = self.client.post(f'/api/customers/{self.customer.id}/kyc/', {'kyc_status': 'VERIFIED'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Employee must provide reason for rejection
        self.client.force_authenticate(user=self.employee_user)
        resp = self.client.post(f'/api/customers/{self.customer.id}/kyc/', {'kyc_status': 'REJECTED'})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # Employee flags NEEDS_REVIEW with reason
        resp = self.client.post(f'/api/customers/{self.customer.id}/kyc/', {
            'kyc_status': 'NEEDS_REVIEW',
            'remarks': 'Utility bill scan unreadable'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.kyc_status, Customer.KYCStatus.NEEDS_REVIEW)
        self.assertIn("Underwriting Review", self.customer.kyc_remarks)

        # Audit log for NEEDS_REVIEW
        audit_review = AuditLog.objects.filter(action="KYC_NEEDS_REVIEW", record_id=self.customer.customer_id).first()
        self.assertIsNotNone(audit_review)

        # Employee VERIFIES KYC
        resp = self.client.post(f'/api/customers/{self.customer.id}/kyc/', {
            'kyc_status': 'VERIFIED',
            'remarks': 'Passport presented at branch'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.kyc_status, Customer.KYCStatus.VERIFIED)

        audit_verify = AuditLog.objects.filter(action="KYC_VERIFIED", record_id=self.customer.customer_id).first()
        self.assertIsNotNone(audit_verify)

    def test_admin_branch_management(self):
        """Verify administrative branch toggle and access restrictions."""
        # Customer cannot toggle branch
        self.client.force_authenticate(user=self.customer_user)
        resp = self.client.post(f'/api/branches/{self.branch.id}/toggle_status/', {'reason': 'Renovation'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # Admin can toggle branch
        self.client.force_authenticate(user=self.admin_user)
        initial_status = self.branch.is_active
        resp = self.client.post(f'/api/branches/{self.branch.id}/toggle_status/', {'reason': 'Renovation'})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.branch.refresh_from_db()
        self.assertEqual(self.branch.is_active, not initial_status)

        audit = AuditLog.objects.filter(action="BRANCH_STATUS_TOGGLED", record_id=self.branch.branch_code).first()
        self.assertIsNotNone(audit)

    def test_admin_stats_aggregation(self):
        """Verify expanded admin metrics and system aggregations."""
        self.client.force_authenticate(user=self.admin_user)
        resp = self.client.get('/api/admin/stats/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('total_customers', resp.data)
        self.assertIn('total_accounts', resp.data)
        self.assertIn('active_accounts', resp.data)
        self.assertIn('frozen_accounts', resp.data)
        self.assertIn('total_deposits', resp.data)
        self.assertIn('total_withdrawals', resp.data)
        self.assertIn('total_transaction_volume', resp.data)
        self.assertIn('failed_transactions', resp.data)
        self.assertIn('reversed_transactions', resp.data)

    def test_cashflow_chart_api_periods(self):
        """Verify dynamic cashflow time-series API for 7D, 30D, and 90D cycles."""
        self.client.force_authenticate(user=self.customer_user)

        # 1. Test 7 Days
        resp_7 = self.client.get('/api/dashboard/cashflow-chart/?days=7')
        self.assertEqual(resp_7.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_7.data['timeframe_days'], 7)
        self.assertIn('total_inflow', resp_7.data)
        self.assertIn('total_outflow', resp_7.data)
        self.assertIn('net_cashflow', resp_7.data)
        self.assertIn('transaction_count', resp_7.data)
        self.assertIn('points', resp_7.data)
        self.assertIsInstance(resp_7.data['points'], list)

        # 2. Test 30 Days
        resp_30 = self.client.get('/api/dashboard/cashflow-chart/?days=30')
        self.assertEqual(resp_30.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_30.data['timeframe_days'], 30)

        # 3. Test 90 Days
        resp_90 = self.client.get('/api/dashboard/cashflow-chart/?days=90')
        self.assertEqual(resp_90.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_90.data['timeframe_days'], 90)

    def test_loan_application_triggers_kyc_and_employee_assignment(self):
        """Verify customer loan application generates KYC request and assigns to employee."""
        self.client.force_authenticate(user=self.customer_user)

        initial_kyc_count = KYCRequest.objects.count()
        resp = self.client.post('/api/loan-applications/', {
            'loan_type': self.home_loan_type.id,
            'requested_amount': '2500000.00',
            'tenure_months': 120,
            'employment_type': 'Salaried',
            'employer_name': 'Global Tech Solutions',
            'monthly_income': '145000.00',
            'existing_obligations': '0.00',
            'purpose': 'Flat Acquisition in Bangalore'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        app_id = resp.data['id']

        # KYC request created and linked
        self.assertEqual(KYCRequest.objects.count(), initial_kyc_count + 1)
        kyc_req = KYCRequest.objects.filter(loan_application_id=app_id).first()
        self.assertIsNotNone(kyc_req)
        self.assertEqual(kyc_req.customer, self.customer)
        self.assertIsNotNone(kyc_req.assigned_employee)

        # Customer received notification
        notif = Notification.objects.filter(user=self.customer_user, title__icontains="KYC").first()
        self.assertIsNotNone(notif)

    def test_employee_kyc_workflow_approval_rejection_needs_review(self):
        """Verify employee KYC actions: Needs Review, Rejection, and Approval with notifications."""
        kyc_req = KYCRequest.objects.create(
            request_id="KYC-TEST-001",
            customer=self.customer,
            assigned_employee=self.employee,
            status=KYCRequest.Status.ASSIGNED
        )

        # 1. Customer cannot review KYC
        self.client.force_authenticate(user=self.customer_user)
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/needs_review/', {'notes': 'Test'})
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

        # 2. Employee needs_review without notes -> 400
        self.client.force_authenticate(user=self.employee_user)
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/needs_review/', {'notes': ''})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 3. Employee needs_review with notes -> 200
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/needs_review/', {
            'notes': 'Please upload clear electricity bill'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        kyc_req.refresh_from_db()
        self.assertEqual(kyc_req.status, KYCRequest.Status.NEEDS_REVIEW)
        self.assertEqual(kyc_req.review_notes, 'Please upload clear electricity bill')

        # Customer notification created
        notif_review = Notification.objects.filter(user=self.customer_user, title__icontains="Review").first()
        self.assertIsNotNone(notif_review)

        # 4. Employee reject without reason -> 400
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/reject/', {'reason': ''})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

        # 5. Employee reject with reason -> 200
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/reject/', {
            'reason': 'Fraudulent PAN scan detected'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        kyc_req.refresh_from_db()
        self.assertEqual(kyc_req.status, KYCRequest.Status.REJECTED)
        self.assertEqual(kyc_req.rejection_reason, 'Fraudulent PAN scan detected')

        # Customer notification created
        notif_reject = Notification.objects.filter(user=self.customer_user, title__icontains="Rejected").first()
        self.assertIsNotNone(notif_reject)

        # 6. Employee approve -> 200
        resp = self.client.post(f'/api/kyc-requests/{kyc_req.id}/approve/', {
            'notes': 'Physical verification confirmed'
        })
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        kyc_req.refresh_from_db()
        self.assertEqual(kyc_req.status, KYCRequest.Status.APPROVED)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.kyc_status, Customer.KYCStatus.VERIFIED)

        # Customer notification created
        notif_approve = Notification.objects.filter(user=self.customer_user, title__icontains="Approved").first()
        self.assertIsNotNone(notif_approve)

    def test_employee_stats_and_workload_api(self):
        """Verify employee operational stats and workload endpoints."""
        self.client.force_authenticate(user=self.employee_user)

        resp_stats = self.client.get('/api/employee/stats/')
        self.assertEqual(resp_stats.status_code, status.HTTP_200_OK)
        self.assertIn('my_assigned_kyc', resp_stats.data)
        self.assertIn('total_pending_kyc', resp_stats.data)
        self.assertIn('total_needs_review_kyc', resp_stats.data)
        self.assertIn('total_completed_kyc', resp_stats.data)
        self.assertIn('pending_loan_applications', resp_stats.data)

        resp_emp_list = self.client.get('/api/employees/')
        self.assertEqual(resp_emp_list.status_code, status.HTTP_200_OK)
        self.assertIsInstance(resp_emp_list.data, list)
        self.assertTrue(len(resp_emp_list.data) >= 1)
        self.assertIn('open_kyc_count', resp_emp_list.data[0])
        self.assertIn('completed_kyc_count', resp_emp_list.data[0])

        # Customer forbidden from employee stats and employee list
        self.client.force_authenticate(user=self.customer_user)
        self.assertEqual(self.client.get('/api/employee/stats/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/employees/').status_code, status.HTTP_403_FORBIDDEN)

    def test_all_demo_users_and_credentials(self):
        """Verify all 5 demo customers, 2 demo employees, and 1 admin authenticate successfully."""
        from django.core.management import call_command
        call_command('seed_expansion_demo_data')

        credentials_to_test = [
            ('sophia', 'Finova@2024', 'CUSTOMER', 'Sophia Mehta'),
            ('rohan', 'Finova@2024', 'CUSTOMER', 'Rohan Deshmukh'),
            ('aarav', 'Finova@2024', 'CUSTOMER', 'Aarav Sharma'),
            ('priya', 'Finova@2024', 'CUSTOMER', 'Priya Patel'),
            ('vikram', 'Finova@2024', 'CUSTOMER', 'Vikram Malhotra'),
            ('employee', 'Finova@2024', 'EMPLOYEE', 'Ramesh Iyer'),
            ('employee2', 'Finova@2024', 'EMPLOYEE', 'Ananya Rao'),
            ('admin', 'FinovaAdmin@2024', 'ADMIN', 'System Administrator'),
        ]

        for username, password, expected_role, expected_name in credentials_to_test:
            resp = self.client.post('/api/auth/login/', {
                'username': username,
                'password': password
            })
            self.assertEqual(resp.status_code, status.HTTP_200_OK, f"Login failed for {username}")
            self.assertIn('token', resp.data, f"No token returned for {username}")
            self.assertEqual(resp.data['user']['role'], expected_role, f"Role mismatch for {username}")
            self.assertIn('first_name', resp.data['user'])

            # Test that auth token allows accessing /api/auth/me/
            auth_client = APIClient()
            auth_client.credentials(HTTP_AUTHORIZATION='Token ' + resp.data['token'])
            me_resp = auth_client.get('/api/auth/me/')
            self.assertEqual(me_resp.status_code, status.HTTP_200_OK)
            self.assertEqual(me_resp.data['user']['username'], username)

            # Test logout clears or revokes token
            logout_resp = auth_client.post('/api/auth/logout/')
            self.assertEqual(logout_resp.status_code, status.HTTP_200_OK)

    def test_admin_search_and_filtering_capabilities(self):
        """Verify admin search and multi-criteria filtering across all banking entities."""
        from django.core.management import call_command
        call_command('seed_expansion_demo_data')

        self.client.force_authenticate(user=self.admin_user)

        # 1. Customer search
        resp_cust = self.client.get('/api/customers/?search=Aarav')
        self.assertEqual(resp_cust.status_code, status.HTTP_200_OK)
        self.assertTrue(any('Aarav' in c['name'] for c in resp_cust.data))

        # 2. Customer KYC status filter
        resp_kyc_filter = self.client.get('/api/customers/?kyc_status=VERIFIED')
        self.assertEqual(resp_kyc_filter.status_code, status.HTTP_200_OK)
        for c in resp_kyc_filter.data:
            self.assertEqual(c['kyc_status'], 'VERIFIED')

        # 3. Account search
        resp_acc = self.client.get('/api/accounts/?status=ACTIVE')
        self.assertEqual(resp_acc.status_code, status.HTTP_200_OK)
        acc_list = resp_acc.data.get('results', resp_acc.data) if isinstance(resp_acc.data, dict) else resp_acc.data
        self.assertTrue(len(acc_list) > 0)
        for acc in acc_list:
            self.assertEqual(acc['status'], 'ACTIVE')

        # 4. KYC requests filtering
        resp_kyc = self.client.get('/api/kyc-requests/?status=ASSIGNED')
        self.assertEqual(resp_kyc.status_code, status.HTTP_200_OK)
        kyc_list = resp_kyc.data.get('results', resp_kyc.data) if isinstance(resp_kyc.data, dict) else resp_kyc.data
        self.assertTrue(len(kyc_list) > 0)
        for k in kyc_list:
            self.assertEqual(k['status'], 'ASSIGNED')

        # 5. Employees list with search
        resp_emp = self.client.get('/api/employees/?search=Ananya')
        self.assertEqual(resp_emp.status_code, status.HTTP_200_OK)
        emp_list = resp_emp.data.get('results', resp_emp.data) if isinstance(resp_emp.data, dict) else resp_emp.data
        self.assertTrue(any('Ananya' in e['full_name'] for e in emp_list))

    def test_security_rbac_and_unauthorized_access_protection(self):
        """Verify strict API protection, 401 for anonymous, 403 for unauthorized roles, and no secret leakage."""
        anon_client = APIClient()

        # Anonymous requests return 401
        protected_urls = [
            '/api/dashboard/',
            '/api/dashboard/cashflow-chart/',
            '/api/accounts/',
            '/api/transfers/',
            '/api/loans/',
            '/api/loan-applications/',
            '/api/notifications/',
            '/api/employee/stats/',
            '/api/admin/stats/',
            '/api/kyc-requests/',
            '/api/audit-logs/',
        ]
        for url in protected_urls:
            resp = anon_client.get(url)
            self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED, f"URL {url} did not return 401 for anonymous")

        # Customer forbidden from Staff and Admin endpoints
        self.client.force_authenticate(user=self.customer_user)
        self.assertEqual(self.client.get('/api/employee/stats/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/admin/stats/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/audit-logs/').status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.client.get('/api/employees/').status_code, status.HTTP_403_FORBIDDEN)

        # Employee forbidden from Admin-only endpoints
        self.client.force_authenticate(user=self.employee_user)
        self.assertEqual(self.client.get('/api/admin/stats/').status_code, status.HTTP_403_FORBIDDEN)

        # Verify no password hashes or secret tokens leaked in customer list serializer
        self.client.force_authenticate(user=self.admin_user)
        resp_cust = self.client.get('/api/customers/')
        self.assertEqual(resp_cust.status_code, status.HTTP_200_OK)
        for c in resp_cust.data:
            self.assertNotIn('password', c)
            self.assertNotIn('token', c)
            self.assertNotIn('secret', c)


