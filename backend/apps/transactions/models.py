from django.db import models
from django.utils import timezone
from django.db.models import Q, CheckConstraint
from apps.users.models import Customer
from apps.accounts.models import Account

class Transaction(models.Model):
    """
    Core banking ledger entity.
    Demonstrates DBMS concepts:
    - Primary key (id)
    - Candidate key (transaction_id)
    - Foreign keys with referential integrity (from_account, to_account)
    - CHECK constraint (amount > 0)
    - Normalized 3NF design (does not duplicate customer attributes)
    - Multi-column indexes for fast ledger filtering and date pagination
    """
    class TransactionType(models.TextChoices):
        TRANSFER = 'TRANSFER', 'Transfer (Internal/NEFT/RTGS/IMPS)'
        DEBIT = 'DEBIT', 'Debit'
        CREDIT = 'CREDIT', 'Credit'
        DEPOSIT = 'DEPOSIT', 'Cash/Cheque Deposit'
        WITHDRAWAL = 'WITHDRAWAL', 'Cash Withdrawal'
        EMI_PAYMENT = 'EMI_PAYMENT', 'Loan EMI Payment'
        LOAN_DISBURSEMENT = 'LOAN_DISBURSEMENT', 'Loan Disbursement'

    class Category(models.TextChoices):
        SHOPPING = 'SHOPPING', 'Shopping & Electronics'
        SALARY = 'SALARY', 'Monthly Salary Credit'
        EMI_BILLS = 'EMI_BILLS', 'Auto-debit Loan EMI / Bills'
        FOOD_DINING = 'FOOD_DINING', 'Food & Dining'
        UTILITIES = 'UTILITIES', 'Utilities & Bills'
        INVESTMENT = 'INVESTMENT', 'Interest Payout / Investment'
        TRANSFER = 'TRANSFER', 'UPI & Account Transfer'
        OTHER = 'OTHER', 'General Transactions'

    class Status(models.TextChoices):
        COMPLETED = 'COMPLETED', 'Completed'
        PENDING = 'PENDING', 'Pending'
        FAILED = 'FAILED', 'Failed'
        REVERSED = 'REVERSED', 'Reversed'

    transaction_id = models.CharField(
        max_length=36,
        unique=True,
        db_index=True,
        help_text="Unique transaction reference (e.g. TXN20241110001)"
    )
    from_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='debit_transactions'
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='credit_transactions'
    )
    beneficiary_name = models.CharField(max_length=120)
    beneficiary_account = models.CharField(max_length=24, blank=True)
    beneficiary_ifsc = models.CharField(max_length=11, blank=True)
    transaction_type = models.CharField(
        max_length=25,
        choices=TransactionType.choices,
        default=TransactionType.TRANSFER,
        db_index=True
    )
    category = models.CharField(
        max_length=25,
        choices=Category.choices,
        default=Category.TRANSFER,
        db_index=True
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Transaction value in INR"
    )
    balance_after = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Account balance immediately following ledger commitment"
    )
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.COMPLETED,
        db_index=True
    )
    remarks = models.CharField(max_length=255, blank=True)
    reference_number = models.CharField(max_length=64, blank=True)
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'finova_transactions'
        verbose_name = 'Banking Transaction'
        verbose_name_plural = 'Banking Transactions'
        ordering = ['-timestamp', '-id']
        constraints = [
            CheckConstraint(
                condition=Q(amount__gt=0),
                name='chk_transaction_amount_positive'
            ),
        ]
        indexes = [
            models.Index(fields=['from_account', 'timestamp'], name='idx_txn_from_time'),
            models.Index(fields=['to_account', 'timestamp'], name='idx_txn_to_time'),
            models.Index(fields=['category', 'timestamp'], name='idx_txn_cat_time'),
            models.Index(fields=['status', 'timestamp'], name='idx_txn_status_time'),
        ]

    def __str__(self):
        return f"{self.transaction_id} | {self.beneficiary_name} | ₹{self.amount} ({self.status})"


class Beneficiary(models.Model):
    """
    Saved payees for fast transfers. Demonstrates composite uniqueness:
    A customer cannot add the same account + IFSC combination twice.
    """
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='beneficiaries'
    )
    name = models.CharField(max_length=120)
    account_number = models.CharField(max_length=24)
    ifsc_code = models.CharField(max_length=11)
    bank_name = models.CharField(max_length=100)
    nickname = models.CharField(max_length=60, blank=True)
    avatar_url = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finova_beneficiaries'
        verbose_name = 'Transfer Beneficiary'
        verbose_name_plural = 'Transfer Beneficiaries'
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                fields=['customer', 'account_number', 'ifsc_code'],
                name='uniq_customer_beneficiary_account'
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.bank_name} ({self.account_number})"
