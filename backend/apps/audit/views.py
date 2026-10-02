from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from django.db.models import Q
from .models import AuditLog
from .serializers import AuditLogSerializer
from apps.users.models import User

class IsAdminUserPermission(permissions.BasePermission):
    """
    Strict Admin Authorization: Only Administrator role or Django superusers
    are permitted to inspect regulatory audit trails.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.role == User.Role.ADMIN or request.user.is_superuser


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit and compliance log access restricted to Bank Administrators.
    Provides comprehensive filtering by actor, action, object type, date range, and keyword.
    """
    serializer_class = AuditLogSerializer
    permission_classes = [IsAdminUserPermission]

    def get_queryset(self):
        user = self.request.user
        if user.role != User.Role.ADMIN and not user.is_superuser:
            return AuditLog.objects.none()

        qs = AuditLog.objects.select_related('user').all()

        action = self.request.query_params.get('action')
        if action and action != 'ALL':
            qs = qs.filter(action__icontains=action)

        actor = self.request.query_params.get('actor')
        if actor:
            qs = qs.filter(user__username__icontains=actor)

        record_type = self.request.query_params.get('record_type')
        if record_type:
            qs = qs.filter(record_type__icontains=record_type)

        date_from = self.request.query_params.get('date_from')
        if date_from:
            qs = qs.filter(timestamp__date__gte=date_from)

        date_to = self.request.query_params.get('date_to')
        if date_to:
            qs = qs.filter(timestamp__date__lte=date_to)

        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(details__icontains=search) |
                Q(action__icontains=search) |
                Q(record_id__icontains=search) |
                Q(user__username__icontains=search)
            )

        return qs.order_by('-timestamp')

