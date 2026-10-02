from decimal import Decimal
from django.test import TestCase
from django.db import IntegrityError
from apps.users.models import User, Customer
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType

class AccountModelTestCase(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            branch_code="TEST01",
            branch_name="Test Branch",
            ifsc="FINO0009999",
            address="Test Road",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001",
            manager_name="Test Manager"
        )
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="Password@123",
            role=User.Role.CUSTOMER
        )
        self.customer = Customer.objects.create(
            user=self.user,
            customer_id="CUST-TEST",
            full_name="Test Customer",
            pan_number="ABCDE1234F",
            aadhaar_last_four="9999",
            phone="9876543210",
            address="Test Address",
            city="Bengaluru",
            state="Karnataka",
            pincode="560001"
        )
        self.acc_type = AccountType.objects.create(
            code="SAVINGS",
            name="Savings Account",
            interest_rate_pa=Decimal("4.00")
        )

    def test_account_creation_and_properties(self):
        acc = Account.objects.create(
            account_number="123456789012",
            customer=self.customer,
            branch=self.branch,
            account_type=self.acc_type,
            available_balance=Decimal("5000.00"),
            ledger_balance=Decimal("5000.00")
        )
        self.assertEqual(acc.masked_account_number, "•••• 9012")
        self.assertEqual(acc.ifsc, "FINO0009999")
        self.assertEqual(acc.available_balance, Decimal("5000.00"))

    def test_unique_account_number_constraint(self):
        Account.objects.create(
            account_number="123456789012",
            customer=self.customer,
            branch=self.branch,
            account_type=self.acc_type,
            available_balance=Decimal("1000.00")
        )
        with self.assertRaises(IntegrityError):
            Account.objects.create(
                account_number="123456789012",
                customer=self.customer,
                branch=self.branch,
                account_type=self.acc_type,
                available_balance=Decimal("2000.00")
            )
