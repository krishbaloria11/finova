from django.db import models
from django.conf import settings
from django.utils import timezone

class AuditLog(models.Model):
    """
    Immutable audit trail for all sensitive financial and managerial activities.
    Meets regulatory requirements (RBI / College DBMS audit specifications).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    action = models.CharField(
        max_length=64,
        db_index=True,
        help_text="e.g. USER_LOGIN, MONEY_TRANSFER, LOAN_APPROVED, KYC_VERIFIED"
    )
    ip_address = models.CharField(max_length=45, blank=True)
    record_type = models.CharField(max_length=64, blank=True)
    record_id = models.CharField(max_length=64, blank=True)
    details = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'finova_audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'timestamp'], name='idx_audit_user_time'),
            models.Index(fields=['action', 'timestamp'], name='idx_audit_action_time'),
        ]

    def __str__(self):
        user_label = self.user.username if self.user else 'System'
        return f"[{self.timestamp:%Y-%m-%d %H:%M:%S}] {user_label} - {self.action}"
