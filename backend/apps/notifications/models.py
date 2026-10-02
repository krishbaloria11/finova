from django.db import models
from django.conf import settings
from django.utils import timezone

class Notification(models.Model):
    """
    User notification system for transfers, EMI reminders, loan decisions, and security alerts.
    """
    class NotificationType(models.TextChoices):
        PAYMENT_DUE = 'PAYMENT_DUE', 'Payment Due'
        TRANSFER_SUCCESS = 'TRANSFER_SUCCESS', 'Transfer Successful'
        LOAN_UPDATE = 'LOAN_UPDATE', 'Loan Application Update'
        SECURITY = 'SECURITY', 'Security Alert'
        SYSTEM = 'SYSTEM', 'System Notice'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    title = models.CharField(max_length=120)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=25,
        choices=NotificationType.choices,
        default=NotificationType.SYSTEM,
        db_index=True
    )
    link = models.CharField(max_length=120, blank=True)
    is_read = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = 'finova_notifications'
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.title} ({'Read' if self.is_read else 'Unread'})"
