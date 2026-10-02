from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.users.models import User, Customer
from apps.branches.models import Branch
from apps.accounts.models import Account, AccountType
from apps.transactions.models import Transaction
from apps.transactions.services import TransferService

class TransferServiceTestCase(TestCase):
    def setUp(self):
        self.branch = Branch.objects.create(
            branch_code="BLR01",
            branch_name="Bengaluru Branch",
            ifsc="FINO0001234",
            address="HAL 2nd Stage",
            city="Bengaluru",
            state="Karnataka",
            pincode="560038",
            manager_name="Branch Manager"
        )
        self.acc_type = AccountType.objects.create(
            code="SAVINGS",
            name="Savings Account",
            interest_rate_pa=Decimal("4.00")
        )

        # Sender
        self.user1 = User.objects.create_user(username="sender", email="s@test.com", password="Pass@123")
        self.cust1 = Customer.objects.create(
            user=self.user1, customer_id="CUST-1", full_name="Sender User",
            pan_number="ABCDE1111A", aadhaar_last_four="1111", phone="9900011111",
            address="Addr 1", city="Bengaluru", state="Karnataka", pincode="560001"
        )
        self.acc1 = Account.objects.create(
            account_number="482100000001",
            customer=self.cust1,
            branch=self.branch,
            account_type=self.acc_type,
            available_balance=Decimal("10000.00"),
            ledger_balance=Decimal("10000.00")
        )

        # Recipient
        self.user2 = User.objects.create_user(username="recipient", email="r@test.com", password="Pass@123")
        self.cust2 = Customer.objects.create(
            user=self.user2, customer_id="CUST-2", full_name="Recipient User",
            pan_number="ABCDE2222B", aadhaar_last_four="2222", phone="9900022222",
            address="Addr 2", city="Bengaluru", state="Karnataka", pincode="560001"
        )
        self.acc2 = Account.objects.create(
            account_number="482100000002",
            customer=self.cust2,
            branch=self.branch,
            account_type=self.acc_type,
            available_balance=Decimal("2000.00"),
            ledger_balance=Decimal("2000.00")
        )

    def test_successful_internal_transfer(self):
        txn = TransferService.execute_transfer(
            from_account_id=self.acc1.id,
            to_account_number=self.acc2.account_number,
            to_ifsc="FINO0001234",
            beneficiary_name="Recipient User",
            amount=Decimal("3000.00"),
            remarks="Test Transfer"
        )

        self.acc1.refresh_from_db()
        self.acc2.refresh_from_db()

        self.assertEqual(self.acc1.available_balance, Decimal("7000.00"))
        self.assertEqual(self.acc2.available_balance, Decimal("5000.00"))
        self.assertEqual(txn.status, Transaction.Status.COMPLETED)
        self.assertEqual(txn.amount, Decimal("3000.00"))

    def test_insufficient_funds_fails(self):
        with self.assertRaises(ValidationError):
            TransferService.execute_transfer(
                from_account_id=self.acc1.id,
                to_account_number=self.acc2.account_number,
                to_ifsc="FINO0001234",
                beneficiary_name="Recipient User",
                amount=Decimal("15000.00")
            )

        self.acc1.refresh_from_db()
        self.assertEqual(self.acc1.available_balance, Decimal("10000.00"))

    def test_negative_or_zero_amount_fails(self):
        with self.assertRaises(ValidationError):
            TransferService.execute_transfer(
                from_account_id=self.acc1.id,
                to_account_number=self.acc2.account_number,
                to_ifsc="FINO0001234",
                beneficiary_name="Recipient User",
                amount=Decimal("-500.00")
            )
