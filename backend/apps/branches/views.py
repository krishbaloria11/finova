from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Branch
from .serializers import BranchSerializer
from apps.users.models import User
from apps.audit.models import AuditLog

from django.db.models import Q

class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer

    def get_queryset(self):
        qs = Branch.objects.all()
        search = self.request.query_params.get('search', '').strip()
        if search:
            qs = qs.filter(
                Q(branch_name__icontains=search) |
                Q(branch_code__icontains=search) |
                Q(city__icontains=search) |
                Q(ifsc__icontains=search) |
                Q(manager_name__icontains=search)
            )
        status_param = self.request.query_params.get('status')
        if status_param and status_param != 'ALL':
            if status_param.lower() in ['active', 'true']:
                qs = qs.filter(is_active=True)
            elif status_param.lower() in ['inactive', 'false']:
                qs = qs.filter(is_active=False)
        return qs

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'toggle_status']:
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def check_admin(self, request):
        if request.user.role != User.Role.ADMIN and not request.user.is_superuser:
            return False
        return True

    def create(self, request, *args, **kwargs):
        if not self.check_admin(request):
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)
        response = super().create(request, *args, **kwargs)
        AuditLog.objects.create(
            user=request.user,
            action="BRANCH_CREATED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Branch",
            record_id=str(response.data.get('branch_code', '')),
            details=f"Admin {request.user.username} registered new branch {response.data.get('branch_name')} ({response.data.get('ifsc')})"
        )
        return response

    def update(self, request, *args, **kwargs):
        if not self.check_admin(request):
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)
        response = super().update(request, *args, **kwargs)
        AuditLog.objects.create(
            user=request.user,
            action="BRANCH_UPDATED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Branch",
            record_id=str(response.data.get('branch_code', '')),
            details=f"Admin {request.user.username} modified branch details for {response.data.get('branch_name')}"
        )
        return response

    @action(detail=True, methods=['post'])
    def toggle_status(self, request, pk=None):
        """Admin action: Toggle branch operating status (Active / Inactive)."""
        if not self.check_admin(request):
            return Response({'error': 'Unauthorized. Admin permissions required.'}, status=status.HTTP_403_FORBIDDEN)

        branch = self.get_object()
        branch.is_active = not branch.is_active
        branch.save(update_fields=['is_active'])

        new_status_str = "ACTIVE" if branch.is_active else "INACTIVE"
        AuditLog.objects.create(
            user=request.user,
            action="BRANCH_STATUS_TOGGLED",
            ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
            record_type="Branch",
            record_id=branch.branch_code,
            details=f"Branch {branch.branch_name} ({branch.branch_code}) marked {new_status_str} by {request.user.username}"
        )

        return Response({
            'message': f"Branch {branch.branch_name} status updated to {new_status_str}.",
            'branch': BranchSerializer(branch).data
        })

