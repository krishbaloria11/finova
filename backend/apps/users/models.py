from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.branches.models import Branch

class User(AbstractUser):
    """
    Custom user model with Role-Based Access Control (RBAC).
    Roles:
    - CUSTOMER: Personal retail banking and credit access
    - EMPLOYEE: Loan underwriting, KYC review, customer operations
    - ADMIN: Complete system oversight, branch management, audit viewing
    """
    class Role(models.TextChoices):
        CUSTOMER = 'CUSTOMER', 'Customer'
        EMPLOYEE = 'EMPLOYEE', 'Bank Employee'
        ADMIN = 'ADMIN', 'System Administrator'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.CUSTOMER,
        db_index=True
    )
    phone = models.CharField(max_length=15, blank=True)

    class Meta:
        db_table = 'finova_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    @property
    def is_customer(self):
        return self.role == self.Role.CUSTOMER

    @property
    def is_employee(self):
        return self.role == self.Role.EMPLOYEE

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN or self.is_superuser


class Customer(models.Model):
    """
    Normalized customer entity (3NF) linking personal profile,
    financial status, credit rating, and KYC verification.
    """
    class KYCStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending Verification'
        VERIFIED = 'VERIFIED', 'Verified'
        REJECTED = 'REJECTED', 'Rejected'
        NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Review'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='customer_profile'
    )
    customer_id = models.CharField(
        max_length=20,
        unique=True,
        db_index=True,
        help_text="Unique Customer Identification File (CIF) number"
    )
    full_name = models.CharField(max_length=120)
    pan_number = models.CharField(
        max_length=10,
        db_index=True,
        help_text="Indian Permanent Account Number (PAN)"
    )
    aadhaar_last_four = models.CharField(
        max_length=4,
        help_text="Last 4 digits of Aadhaar (privacy compliant)"
    )
    phone = models.CharField(max_length=15)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=80)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=10)
    monthly_income = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0.00
    )
    credit_score = models.IntegerField(
        default=750,
        help_text="Simulated Indian CIBIL Credit Score (300-900)"
    )
    credit_category = models.CharField(max_length=30, default='Excellent')
    credit_score_updated_at = models.DateField(auto_now=True)
    kyc_status = models.CharField(
        max_length=20,
        choices=KYCStatus.choices,
        default=KYCStatus.PENDING,
        db_index=True
    )
    kyc_document_type = models.CharField(max_length=50, default='PAN & Aadhaar')
    kyc_document_number = models.CharField(max_length=50, blank=True)
    kyc_verified_at = models.DateTimeField(null=True, blank=True)
    kyc_remarks = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'finova_customers'
        verbose_name = 'Customer Profile'
        verbose_name_plural = 'Customer Profiles'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.customer_id})"


class Employee(models.Model):
    """
    Normalized bank employee entity linking staff member to a branch
    and departmental permissions.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='employee_profile'
    )
    employee_id = models.CharField(max_length=20, unique=True, db_index=True)
    full_name = models.CharField(max_length=120)
    branch = models.ForeignKey(
        Branch,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='employees'
    )
    designation = models.CharField(max_length=80, default='Credit Officer')
    department = models.CharField(max_length=80, default='Retail Credit & Underwriting')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finova_employees'
        verbose_name = 'Bank Employee'
        verbose_name_plural = 'Bank Employees'

    def __str__(self):
        return f"{self.full_name} - {self.designation} ({self.employee_id})"


class KYCRequest(models.Model):
    """
    Realistic Bank KYC verification queue entity.
    Tracks assignment of KYC review cases to banking operations officers,
    review decisions, reasons, and audit trails.
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending Assignment'
        ASSIGNED = 'ASSIGNED', 'Assigned to Officer'
        APPROVED = 'APPROVED', 'Verified & Approved'
        REJECTED = 'REJECTED', 'Rejected'
        NEEDS_REVIEW = 'NEEDS_REVIEW', 'Needs Additional Review'

    request_id = models.CharField(
        max_length=32,
        unique=True,
        db_index=True,
        help_text="Unique KYC tracking identifier e.g. KYC-2024-001"
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name='kyc_requests'
    )
    loan_application = models.ForeignKey(
        'loans.LoanApplication',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='kyc_requests'
    )
    assigned_employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_kyc_requests'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    document_type = models.CharField(max_length=80, default='PAN & Aadhaar')
    document_number = models.CharField(max_length=50, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_kyc_requests'
    )
    review_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        db_table = 'finova_kyc_requests'
        verbose_name = 'KYC Verification Request'
        verbose_name_plural = 'KYC Verification Requests'
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.request_id} - {self.customer.full_name} [{self.status}]"

    @classmethod
    def assign_to_employee(cls, kyc_request):
        """
        Deterministic Least-Loaded Employee Assignment:
        Assigns the request to the active Employee with the fewest currently open KYC cases.
        Ties are broken deterministically by employee_id.
        """
        active_employees = list(Employee.objects.filter(is_active=True).order_by('employee_id'))
        if not active_employees:
            return None

        # Sort employees by count of open assignments (PENDING, ASSIGNED, NEEDS_REVIEW)
        def open_count(emp):
            return cls.objects.filter(
                assigned_employee=emp,
                status__in=[cls.Status.PENDING, cls.Status.ASSIGNED, cls.Status.NEEDS_REVIEW]
            ).count()

        least_loaded = min(active_employees, key=open_count)
        kyc_request.assigned_employee = least_loaded
        kyc_request.status = cls.Status.ASSIGNED
        kyc_request.save(update_fields=['assigned_employee', 'status'])
        return least_loaded

