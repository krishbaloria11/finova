from django.db import models

class Branch(models.Model):
    """
    Represents an Indian bank branch entity adhering to RBI guidelines.
    Demonstrates:
    - Primary key (id)
    - Candidate keys / Unique constraints (branch_code, ifsc)
    - Database indexing for rapid lookup
    """
    branch_code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Unique branch identifier code (e.g., BLR01, MUM02)"
    )
    branch_name = models.CharField(max_length=120)
    ifsc = models.CharField(
        max_length=11,
        unique=True,
        db_index=True,
        help_text="11-character Indian Financial System Code (e.g., FINO0001234)"
    )
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=80, db_index=True)
    state = models.CharField(max_length=80)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=20, blank=True)
    manager_name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'finova_branches'
        verbose_name = 'Bank Branch'
        verbose_name_plural = 'Bank Branches'
        ordering = ['branch_code']

    def __str__(self):
        return f"{self.branch_name} ({self.ifsc})"
