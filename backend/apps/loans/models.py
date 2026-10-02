from django.db import models
from django.utils import timezone
from django.db.models import Q, CheckConstraint
from apps.users.models import Customer, Employee
from apps.accounts.models import Account

class LoanType(models.Model):
    """
    Lookup entity defining bank lending facilities.
    Adheres to 3NF by isolating loan class policies from individual loan accounts.
    """
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="e.g. HOME, PERSONAL, EDUCATION, VEHICLE, BUSINESS"
    )
    name = models.CharField(max_length=80)
    base_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Base annual interest rate (e.g. 8.25)"
    )
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, default=50000.00)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, default=10000000.00)
    min_tenure_months = models.IntegerField(default=12)
    max_tenure_months = models.IntegerField(default=360)
    processing_fee_percent = models.DecimalField(max_digits=4, decimal_places=2, default=0.50)
    description = models.TextField(blank=True)
    icon_name = models.CharField(max_length=40, default='account_balance')

    class Meta:
        db_table = 'finova_loan_types'
        verbose_name = 'Loan Product Type'
        verbose_name_plural = 'Loan Product Types'

    def __str__(self):
        return f"{self.name} ({self.base_interest_rate}% p.a.)"


class LoanApplication(models.Model):
    """
    Captures multi-step customer credit application state.
    Enforces referential integrity between customer, product type, and underwriting employee.
    """
    class Status(models.TextChoices):
        SUBMITTED = 'SUBMITTED', 'Submitted'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'

    application_id = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Candidate key e.g. LA-2024-9182"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loan_applications'
    )
    loan_type = models.ForeignKey(
        LoanType,
        on_delete=models.PROTECT,
        related_name='applications'
    )
    requested_amount = models.DecimalField(max_digits=12, decimal_places=2)
    tenure_months = models.IntegerField(help_text="Requested tenure in months")
    proposed_interest_rate = models.DecimalField(max_digits=5, decimal_places=2)
    calculated_emi = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    purpose = models.CharField(max_length=255)
    employment_type = models.CharField(max_length=50)
    employer_name = models.CharField(max_length=120, blank=True)
    monthly_income = models.DecimalField(max_digits=12, decimal_places=2)
    existing_obligations = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    pan_number = models.CharField(max_length=10)
    aadhaar_number = models.CharField(max_length=16, blank=True)
    residential_address = models.CharField(max_length=255)
    kyc_document_type = models.CharField(max_length=50, default='PAN & Salary Slip')
    kyc_document_number = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNDER_REVIEW,
        db_index=True
    )
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_loan_applications'
    )
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'finova_loan_applications'
        verbose_name = 'Loan Application'
        verbose_name_plural = 'Loan Applications'
        ordering = ['-submitted_at']
        indexes = [
            models.Index(fields=['customer', 'status'], name='idx_loan_app_cust_status'),
        ]

    def __str__(self):
        return f"{self.application_id} - {self.customer.full_name} ({self.get_status_display()})"


class Loan(models.Model):
    """
    Active credit facility entity.
    Demonstrates:
    - Primary key (id)
    - Candidate key (loan_id)
    - One-to-one link to approved application (optional)
    - CHECK constraint (outstanding_amount >= 0)
    - Referential integrity with servicing account
    """
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        APPROVED = 'APPROVED', 'Approved (Pending Disbursement)'
        COMPLETED = 'COMPLETED', 'Fully Repaid'
        CLOSED = 'CLOSED', 'Closed'
        DEFAULTED = 'DEFAULTED', 'Defaulted'

    loan_id = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Unique facility reference e.g. HL-4091"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    loan_type = models.ForeignKey(
        LoanType,
        on_delete=models.PROTECT,
        related_name='loans'
    )
    application = models.OneToOneField(
        LoanApplication,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sanctioned_loan'
    )
    servicing_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='servicing_loans',
        help_text="Account from which monthly auto-debit EMI is deducted"
    )
    principal_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Total sanctioned principal"
    )
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Annual interest rate percentage"
    )
    tenure_months = models.IntegerField()
    monthly_emi = models.DecimalField(max_digits=12, decimal_places=2)
    total_payable = models.DecimalField(max_digits=14, decimal_places=2)
    total_interest = models.DecimalField(max_digits=14, decimal_places=2)
    outstanding_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        help_text="Remaining principal + accrued interest"
    )
    repaid_amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0.00
    )
    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField()
    next_due_date = models.DateField()
    auto_debit = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finova_loans'
        verbose_name = 'Credit Facility'
        verbose_name_plural = 'Credit Facilities'
        ordering = ['-created_at']
        constraints = [
            CheckConstraint(
                condition=Q(outstanding_amount__gte=0),
                name='chk_loan_outstanding_non_negative'
            ),
            CheckConstraint(
                condition=Q(principal_amount__gt=0),
                name='chk_loan_principal_positive'
            ),
        ]
        indexes = [
            models.Index(fields=['customer', 'status'], name='idx_loan_cust_status'),
            models.Index(fields=['next_due_date'], name='idx_loan_due_date'),
        ]

    def __str__(self):
        return f"{self.loan_id} ({self.loan_type.name}) - ₹{self.outstanding_amount} due"

    @property
    def repayment_progress_percentage(self):
        if self.principal_amount > 0:
            pct = (self.repaid_amount / self.principal_amount) * 100
            return min(round(float(pct), 1), 100.0)
        return 0.0


class LoanPayment(models.Model):
    """
    Represents an EMI installment or extra principal prepayment record.
    """
    class Status(models.TextChoices):
        SUCCESSFUL = 'SUCCESSFUL', 'Successful'
        FAILED = 'FAILED', 'Failed'
        PENDING = 'PENDING', 'Pending'

    payment_id = models.CharField(max_length=36, unique=True, db_index=True)
    loan = models.ForeignKey(
        Loan,
        on_delete=models.CASCADE,
        related_name='payments'
    )
    account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name='loan_payments'
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    principal_component = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    interest_component = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    installment_number = models.IntegerField(default=1)
    payment_date = models.DateTimeField(default=timezone.now, db_index=True)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.SUCCESSFUL
    )
    receipt_number = models.CharField(max_length=40, unique=True)
    remarks = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'finova_loan_payments'
        verbose_name = 'Loan Repayment'
        verbose_name_plural = 'Loan Repayments'
        ordering = ['-payment_date']
        indexes = [
            models.Index(fields=['loan', 'payment_date'], name='idx_loan_pmt_date'),
        ]

    def __str__(self):
        return f"{self.payment_id} | {self.loan.loan_id} | ₹{self.amount_paid}"
