from rest_framework import serializers
from .models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True, default='System')

    class Meta:
        model = AuditLog
        fields = ['id', 'username', 'action', 'ip_address', 'record_type', 'record_id', 'details', 'timestamp']
        read_only_fields = fields
