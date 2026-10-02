from django.db import models
from django.db.models import Q, CheckConstraint
from apps.users.models import Customer
from apps.branches.models import Branch

class AccountType(models.Model):
    """
    Lookup entity defining distinct bank product parameters.
    Demonstrates 3NF normalization separating account properties from customer accounts.
    """
    code = models.CharField(max_length=20, unique=True, help_text="e.g., SAVINGS, CURRENT, FD")
    name = models.CharField(max_length=80)
    interest_rate_pa = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=4.00,
        help_text="Annual interest rate percentage"
    )
    minimum_balance = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=1000.00
    )
    description = models.TextField(blank=True)

    class Meta:
        db_table = 'finova_account_types'
        verbose_name = 'Account Type'
        verbose_name_plural = 'Account Types'

    def __str__(self):
        return f"{self.name} ({self.code})"


class Account(models.Model):
    """
    Represents a customer's specific bank account.
    Demonstrates DBMS concepts:
    - Primary key (id)
    - Foreign keys with referential integrity (customer, branch, account_type)
    - Candidate key (account_number)
    - SQL CHECK constraints (available_balance >= 0, ledger_balance >= 0)
    - Composite indexing for performant customer dashboard queries
    """
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        FROZEN = 'FROZEN', 'Frozen'
        DORMANT = 'DORMANT', 'Dormant'
        CLOSED = 'CLOSED', 'Closed'

    account_number = models.CharField(
        max_length=16,
        unique=True,
        db_index=True,
        help_text="Standard 12 to 16-digit Indian bank account number"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='accounts'
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name='accounts'
    )
    account_type = models.ForeignKey(
        AccountType,
        on_delete=models.PROTECT,
        related_name='accounts'
    )
    available_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Current liquid balance available for withdrawal/transfer"
    )
    ledger_balance = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00,
        help_text="Total book balance including uncleared items"
    )
    currency = models.CharField(max_length=5, default='INR')
    card_variant = models.CharField(
        max_length=50,
        default='RuPay Platinum Contactless'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    is_primary = models.BooleanField(default=False)
    opened_date = models.DateField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finova_accounts'
        verbose_name = 'Customer Account'
        verbose_name_plural = 'Customer Accounts'
        ordering = ['-is_primary', 'id']
        constraints = [
            CheckConstraint(
                condition=Q(available_balance__gte=0),
                name='chk_account_available_balance_non_negative'
            ),
            CheckConstraint(
                condition=Q(ledger_balance__gte=0),
                name='chk_account_ledger_balance_non_negative'
            ),
        ]
        indexes = [
            models.Index(fields=['customer', 'status'], name='idx_account_cust_status'),
            models.Index(fields=['account_number'], name='idx_account_number'),
        ]

    def __str__(self):
        return f"{self.account_type.name} •••• {self.account_number[-4:]} (₹{self.available_balance})"

    @property
    def masked_account_number(self):
        if len(self.account_number) >= 4:
            return f"•••• {self.account_number[-4:]}"
        return self.account_number

    @property
    def ifsc(self):
        return self.branch.ifsc
